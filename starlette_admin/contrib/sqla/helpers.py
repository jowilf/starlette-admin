from typing import Any, Callable, Dict, List, Optional, Sequence

from sqlalchemy import String, and_, cast, false, not_, or_, true
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import (
    InstrumentedAttribute,
    RelationshipProperty,
)
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl
from sqlalchemy.sql import ClauseElement


def __is_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return ~latest_attr.has()
        return ~latest_attr.any()
    return latest_attr.is_(None)


def __is_not_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return latest_attr.has()
        return latest_attr.any()
    return latest_attr.is_not(None)


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
    "is_null": lambda f, v: __is_null(f),
    "is_not_null": lambda f, v: __is_not_null(f),
    "between": lambda f, v: f.between(*v),
    "not_between": lambda f, v: not_(f.between(*v)),
}

_STRING_OPERATORS = {
    "eq",
    "neq",
    "contains",
    "not_contains",
    "startswith",
    "not_startswith",
    "endswith",
    "not_endswith",
}


def _apply_string_operator(col_attr: Any, operator: str, value: Any) -> Any:
    """Apply a string operator to a single column attribute."""
    casted = cast(col_attr, String)
    if operator == "eq":
        return casted == value
    if operator == "neq":
        return casted != value
    if operator == "contains":
        return casted.ilike(f"%{value}%")
    if operator == "not_contains":
        return not_(casted.ilike(f"%{value}%"))
    if operator == "startswith":
        return casted.ilike(f"{value}%")
    if operator == "not_startswith":
        return not_(casted.ilike(f"{value}%"))
    if operator == "endswith":
        return casted.ilike(f"%{value}")
    if operator == "not_endswith":
        return not_(casted.ilike(f"%{value}"))
    return None


def _collect_string_clauses(
    mapper: Any,
    related_model: Any,
    operator: str,
    value: Any,
    allowed_columns: Optional[List[str]] = None,
) -> List[Any]:
    """Collect filter clauses from the related model's string columns."""
    clauses: List[Any] = []
    for col_prop in mapper.column_attrs:
        if allowed_columns is not None and col_prop.key not in allowed_columns:
            continue
        col = col_prop.columns[0]
        try:
            python_type = col.type.python_type
        except NotImplementedError:
            continue
        if python_type is str:
            related_attr = getattr(related_model, col_prop.key)
            clause = _apply_string_operator(related_attr, operator, value)
            if clause is not None:
                clauses.append(clause)

    if not clauses:
        # Fallback: try to match against cast of PK
        pk_cols = mapper.primary_key
        if len(pk_cols) == 1:
            pk_attr = getattr(
                related_model, mapper.get_property_by_column(pk_cols[0]).key
            )
            clause = _apply_string_operator(cast(pk_attr, String), operator, value)
            if clause is not None:
                clauses.append(clause)

    return clauses


def _relationship_string_filter(
    attr: InstrumentedAttribute,
    operator: str,
    value: Any,
    allowed_columns: Optional[List[str]] = None,
) -> Any:
    """Build a string filter on a relationship by searching the related model's
    string columns (matching ``__admin_repr__`` behavior).

    Args:
        attr: The relationship attribute on the parent model.
        operator: The string operator (eq, neq, contains, etc.).
        value: The user-provided search text.
        allowed_columns: Optional list of column names on the related model
            to search. Comes from ``searchable_relation_fields``.
            If ``None``, all string columns are searched.
    """
    related_model = attr.property.entity.class_
    mapper = sa_inspect(related_model)

    string_clauses = _collect_string_clauses(
        mapper, related_model, operator, value, allowed_columns
    )

    if not string_clauses:
        return and_(True)  # No filterable columns — match everything

    # For positive operators: combine with OR (match if ANY column matches)
    # For negated operators: combine with AND (exclude only if NO column matches)
    if operator.startswith("not_") or operator == "neq":
        combined = (
            and_(*string_clauses) if len(string_clauses) > 1 else string_clauses[0]
        )
    else:
        combined = (
            or_(*string_clauses) if len(string_clauses) > 1 else string_clauses[0]
        )

    # Apply via .has() (scalar) or .any() (collection)
    if isinstance(attr.impl, ScalarObjectAttributeImpl):
        return attr.has(combined)
    return attr.any(combined)


def build_query(
    where: Dict[str, Any],
    model: Any,
    latest_attr: Optional[InstrumentedAttribute] = None,
    searchable_relation_fields: Optional[Dict[str, List[str]]] = None,
) -> Any:
    filters = []
    for key, _ in where.items():
        if key == "or":
            filters.append(
                or_(
                    *[
                        build_query(v, model, latest_attr, searchable_relation_fields)
                        for v in where[key]
                    ]
                )
            )
        elif key == "and":
            filters.append(
                and_(
                    *[
                        build_query(v, model, latest_attr, searchable_relation_fields)
                        for v in where[key]
                    ]
                )
            )
        elif key in OPERATORS:
            # Handle string operators on relationship attributes
            if (
                latest_attr is not None
                and isinstance(latest_attr.property, RelationshipProperty)
                and key in _STRING_OPERATORS
            ):
                allowed_columns = None
                if searchable_relation_fields:
                    allowed_columns = searchable_relation_fields.get(latest_attr.key)
                filters.append(
                    _relationship_string_filter(
                        latest_attr, key, where[key], allowed_columns
                    )
                )
            else:
                filters.append(OPERATORS[key](latest_attr, where[key]))  # type: ignore
        else:
            attr: Optional[InstrumentedAttribute] = getattr(model, key, None)
            if attr is not None:
                filters.append(
                    build_query(where[key], model, attr, searchable_relation_fields)
                )
    if len(filters) == 1:
        return filters[0]
    if filters:
        return and_(*filters)
    return and_(True)


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


def extract_column_python_type(attr: InstrumentedAttribute) -> type:
    try:
        return attr.type.python_type
    except NotImplementedError:
        return str
