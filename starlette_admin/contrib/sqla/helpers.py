import inspect
from typing import Any, Callable, Dict, List, Optional, Sequence

import sqlalchemy_file
from sqlalchemy import Column, String, and_, cast, false, not_, or_, true
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
from sqlalchemy.sql import ClauseElement
from starlette_admin import ImageField
from starlette_admin.contrib.sqla.converters import converters
from starlette_admin.contrib.sqla.exceptions import NotSupportedColumn
from starlette_admin.fields import BaseField, HasMany, HasOne
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
    "startswith": lambda f, v: cast(f, String).startswith(v),
    "not_startswith": lambda f, v: not_(cast(f, String).startswith(v)),
    "endswith": lambda f, v: cast(f, String).endswith(v),
    "not_endswith": lambda f, v: not_(cast(f, String).endswith(v)),
    "contains": lambda f, v: cast(f, String).contains(v),
    "not_contains": lambda f, v: not_(cast(f, String).contains(v)),
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


def find_converter(column: Column) -> Callable[[str, Column], BaseField]:
    types = inspect.getmro(type(column.type))
    # Search by module + name
    for col_type in types:
        print(col_type)
        type_string = f"{col_type.__module__}.{col_type.__name__}"
        if type_string in converters:
            return converters[type_string]

    # Search by name
    for col_type in types:
        print(col_type.__name__)
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
        f"Column {column.type} can not be converted automatically. Find the appropriate field manually"
    )


def normalize_fields(  # noqa: C901
    fields: Sequence[Any], mapper: Mapper
) -> List[BaseField]:
    """
    Look and convert all InstrumentedAttribute or str in fields into the
    right field (starlette_admin.BaseField)
    """
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
                if not column.foreign_keys:
                    field_converter = find_converter(column)
                    converted_fields.append(field_converter(attr.key, column))
    return converted_fields


def normalize_list(arr: Optional[Sequence[Any]]) -> Optional[Sequence[str]]:
    """This methods will convert all InstrumentedAttribute into str"""
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


if __name__ == "__main__":
    print(
        find_converter(Column("n", sqlalchemy_file.ImageField))(
            "n", Column("n", sqlalchemy_file.ImageField)
        )
    )
    print(ImageField("n"))
