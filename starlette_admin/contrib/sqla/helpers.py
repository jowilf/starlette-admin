import inspect
from typing import Any, Callable, Dict, List, Optional, Sequence, Type

from sqlalchemy import ARRAY, Boolean, Column, and_, false, not_, or_, true
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
from sqlalchemy.sql import ClauseElement
from starlette_admin.contrib.sqla.exceptions import NotSupportedColumn
from starlette_admin.contrib.sqla.fields import FileField, ImageField
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EnumField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    StringField,
    TagsField,
    TextAreaField,
    TimeField,
)
from starlette_admin.helpers import slugify_class_name

OPERATORS: Dict[str, Callable[[InstrumentedAttribute, Any], ClauseElement]] = {
    "eq": lambda f, v: f == v,
    "neq": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "gt": lambda f, v: f > v,
    "le": lambda f, v: f <= v,
    "ge": lambda f, v: f >= v,
    "in": lambda f, v: f.in_(v),
    "not_in": lambda f, v: f.not_in(v),
    "startswith": lambda f, v: f.startswith(v),
    "not_startswith": lambda f, v: not_(f.startswith(v)),
    "endswith": lambda f, v: f.endswith(v),
    "not_endswith": lambda f, v: not_(f.endswith(v)),
    "contains": lambda f, v: f.contains(v),
    "not_contains": lambda f, v: not_(f.contains(v)),
    "is_false": lambda f, v: f == false(),
    "is_true": lambda f, v: f == true(),
    "is_null": lambda f, v: f.is_(None),
    "is_not_null": lambda f, v: f.is_not(None),
    "between": lambda f, v: f.between(*v),
    "not_between": lambda f, v: not_(f.between(*v)),
}


def build_query(
    where: Dict[str, Any],
    model: Any,
    latest_attr: Optional[InstrumentedAttribute] = None,
) -> Any:
    filters = []
    for key in where:
        if key == "or":
            filters.append(
                or_(*[build_query(v, model, latest_attr) for v in where[key]])
            )
        elif key == "and":
            filters.append(
                and_(*[build_query(v, model, latest_attr) for v in where[key]])
            )
        elif key in OPERATORS:
            filters.append(OPERATORS[key](latest_attr, where[key]))  # type: ignore
        else:
            attr: Optional[InstrumentedAttribute] = getattr(model, key, None)
            if attr is not None:
                filters.append(build_query(where[key], model, attr))
    if len(filters) == 1:
        return filters[0]
    if filters:
        return and_(*filters)
    return and_(True)


def build_order_clauses(order_list: List[str], model: Any) -> Any:
    clauses = []
    for value in order_list:
        attr_key, order = value.strip().split(maxsplit=1)
        attr = getattr(model, attr_key, None)
        if attr is not None:
            clauses.append(attr.desc() if order.lower() == "desc" else attr)
    return clauses


converters = {
    "String": StringField,  # includes Unicode
    "CHAR": StringField,
    "Text": TextAreaField,  # includes UnicodeText
    "LargeBinary": TextAreaField,
    "Binary": TextAreaField,
    "Boolean": BooleanField,
    "dialects.mssql.base.BIT": BooleanField,
    "Date": DateField,
    "DateTime": DateTimeField,
    "Time": TimeField,
    "Enum": EnumField,
    "Integer": IntegerField,  # includes BigInteger and SmallInteger
    "Numeric": DecimalField,  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    "JSON": JSONField,
    "dialects.mysql.types.YEAR": StringField,
    "dialects.mysql.base.YEAR": StringField,
    "dialects.postgresql.base.INET": StringField,
    "dialects.postgresql.base.MACADDR": StringField,
    "dialects.postgresql.base.UUID": StringField,
    "sqlalchemy_file.types.FileField": FileField,  # support for sqlalchemy-file
    "sqlalchemy_file.types.ImageField": ImageField,  # support for sqlalchemy-file
}


def convert_to_field(column: Column) -> Type[BaseField]:
    if isinstance(column.type, ARRAY) and (
        column.type.dimensions is None or column.type.dimensions == 1
    ):
        """Support for Postgresql ARRAY type"""
        return TagsField
    elif isinstance(column.type, ARRAY):
        raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")
    types = inspect.getmro(type(column.type))

    # Search by module + name
    for col_type in types:
        type_string = f"{col_type.__module__}.{col_type.__name__}"
        if type_string in converters:
            return converters[type_string]

    # Search by name
    for col_type in types:
        if col_type.__name__ in converters:
            return converters[col_type.__name__]

        # Support for custom types like SQLModel which inherit TypeDecorator
        if hasattr(col_type, "impl"):
            if callable(col_type.impl):
                impl = col_type.impl
            else:
                impl = col_type.impl.__class__

            if impl.__name__ in converters:
                return converters[impl.__name__]
    raise NotSupportedColumn(  # pragma: no cover
        f"Column {column.type} is not supported"
    )


def normalize_fields(  # noqa: C901
    fields: Sequence[Any], mapper: Mapper
) -> List[BaseField]:
    converted_fields = []
    for field in fields:
        if isinstance(field, BaseField):
            converted_fields.append(field)
        else:
            if isinstance(field, InstrumentedAttribute):
                attr = mapper.attrs.get(field.key)
            else:
                attr = mapper.attrs.get(field)
            if attr is None:
                raise ValueError(f"Can't find column with key {field}")
            if isinstance(attr, RelationshipProperty):
                identity = slugify_class_name(attr.entity.class_.__name__)
                if attr.direction.name == "MANYTOONE" or (
                    attr.direction.name == "ONETOMANY" and not attr.uselist
                ):
                    converted_fields.append(HasOne(attr.key, identity=identity))
                else:
                    converted_fields.append(HasMany(attr.key, identity=identity))
            elif isinstance(attr, ColumnProperty):
                assert (
                    len(attr.columns) == 1
                ), "Multiple-column properties are not supported"
                column = attr.columns[0]
                required = False
                if column.foreign_keys:
                    continue
                if (
                    not column.nullable
                    and not isinstance(column.type, (Boolean,))
                    and not column.default
                    and not column.server_default
                ):
                    required = True

                field = convert_to_field(column)
                if field is EnumField:
                    field = EnumField.from_enum(attr.key, column.type.enum_class)
                else:
                    field = field(attr.key)
                    if isinstance(field, (FileField, ImageField)) and getattr(
                        column.type, "multiple", False
                    ):
                        field.multiple = True

                field.required = required
                converted_fields.append(field)
    return converted_fields


def normalize_list(arr: Optional[Sequence[Any]]) -> Optional[Sequence[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, InstrumentedAttribute):
            _new_list.append(v.key)
        elif isinstance(v, str):
            _new_list.append(v)
        else:
            raise ValueError(
                f"Expected str or InstrumentedAttribute, got {type(v).__name__}"
            )
    return _new_list


def extract_column_python_type(column: Column) -> type:
    try:
        return column.type.python_type
    except NotImplementedError:
        return str
