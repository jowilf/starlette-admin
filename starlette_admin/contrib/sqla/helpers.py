from typing import Any, Callable, Dict, List, Optional, Sequence

from sqlalchemy import Column, String, and_, cast, false, not_, or_, true
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
from sqlalchemy.sql import ClauseElement
from starlette_admin.contrib.sqla.converters import find_converter
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
                    field_converter = find_converter(column)  # type: ignore
                    converted_fields.append(field_converter(attr.key, column))  # type: ignore
    return converted_fields


def normalize_list(
    arr: Optional[Sequence[Any]], is_default_sort_list: bool = False
) -> Optional[Sequence[str]]:
    """This methods will convert all InstrumentedAttribute into str"""
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, InstrumentedAttribute):
            _new_list.append(v.key)
        elif isinstance(v, str):
            _new_list.append(v)
        elif (
            isinstance(v, tuple) and is_default_sort_list
        ):  # Support for fields_default_sort:
            if (
                len(v) == 2
                and isinstance(v[0], (str, InstrumentedAttribute))
                and isinstance(v[1], bool)
            ):
                _new_list.append(
                    (
                        v[0].key if isinstance(v[0], InstrumentedAttribute) else v[0],  # type: ignore[arg-type]
                        v[1],
                    )
                )
            else:
                raise ValueError(
                    "Invalid argument, Expected Tuple[str | InstrumentedAttribute, bool]"
                )
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
