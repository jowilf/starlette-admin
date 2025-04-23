import functools
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

from beanie import Document, Link
from beanie.odm.enums import SortDirection
from mongoengine.base.fields import BaseField as MongoBaseField
from mongoengine.queryset import Q as BaseQ  # noqa: N811
from mongoengine.queryset import QNode
from mongoengine.queryset.visitor import QCombination


def flatten_qcombination(q: QNode) -> Dict[str, Any]:
    """
    Flatten QCombination into a list of QNode
    """

    # if q is a QCombination, flatten it
    if isinstance(q, QCombination):
        if q.operation == QCombination.OR:
            return {"$or": [flatten_qcombination(child) for child in q.children]}
        if q.operation == QCombination.AND:
            return {"$and": [flatten_qcombination(child) for child in q.children]}
        raise ValueError(f"Unknown operation: {q.operation}")

    return q.query


class Q(BaseQ):
    """
    Override mongoengine.Q class to support expression like this:
    >>> Q('name', 'Jo', 'istartswith') # same as Q(name__istartswith = 'Jo')
    or
    >>> Q('name', 'John') # same as Q(name = 'John')
    """

    def __init__(self, field: str, value: Any, op: Optional[str] = None) -> None:
        if op in TEXT_OPERATORS:
            super().__init__(**{field: self.handle_text_operator(op, value)})
        elif op is not None:
            super().__init__(**{field: {op: value}})
        else:
            super().__init__(**{field: value})

    def handle_text_operator(self, op: str, value: Any) -> Dict[str, Any]:
        operator_map: Dict[str, dict[str, Any]] = {
            "$istartswith": {"$regex": f"^{value}", "$options": "i"},
            "$iendswith": {"$regex": f"{value}$", "$options": "i"},
            "$icontains": {"$regex": f"{value}", "$options": "i"},
            "$not__istartswith": {"$not": {"$regex": f"^{value}", "$options": "i"}},
            "$not__iendswith": {"$not": {"$regex": f"{value}$", "$options": "i"}},
            "$not__icontains": {"$not": {"$regex": f"{value}", "$options": "i"}},
        }
        if op in operator_map:
            return operator_map[op]
        raise ValueError(f"Invalid operator: {op}")

    @classmethod
    def empty(cls) -> BaseQ:
        return BaseQ()


TEXT_OPERATORS: List[str] = [
    "$istartswith",
    "$iendswith",
    "$icontains",
    "$not__istartswith",
    "$not__iendswith",
    "$not__icontains",
]

OPERATORS: Dict[str, Callable[[str, Any], Q]] = {
    "eq": lambda f, v: Q(f, v),
    "neq": lambda f, v: Q(f, v, "$ne"),
    "lt": lambda f, v: Q(f, v, "$lt"),
    "gt": lambda f, v: Q(f, v, "$gt"),
    "le": lambda f, v: Q(f, v, "$lte"),
    "ge": lambda f, v: Q(f, v, "$gte"),
    "in": lambda f, v: Q(f, v, "$in"),
    "not_in": lambda f, v: Q(f, v, "$nin"),
    "startswith": lambda f, v: Q(f, v, "$istartswith"),
    "not_startswith": lambda f, v: Q(f, v, "$not__istartswith"),
    "endswith": lambda f, v: Q(f, v, "$iendswith"),
    "not_endswith": lambda f, v: Q(f, v, "$not__iendswith"),
    "contains": lambda f, v: Q(f, v, "$icontains"),
    "not_contains": lambda f, v: Q(f, v, "$not__icontains"),
    "is_false": lambda f, v: Q(f, False),
    "is_true": lambda f, v: Q(f, True),
    "is_null": lambda f, v: Q(f, None),
    "is_not_null": lambda f, v: Q(f, None, "$ne"),
    "between": lambda f, v: Q(f, v[0], "$gte") & Q(f, v[1], "$lte"),
    "not_between": lambda f, v: Q(f, v[0], "$lt") | Q(f, v[1], "$gt"),
}


def isvalid_field(document: Type[Document], field: str) -> bool:
    """
    Check if field is valid field for document. nested field is separate with '.'
    """
    try:
        split_fields = field.split(".", maxsplit=1)
        if len(split_fields) == 1:
            top_field, nested_field = split_fields[0], None
        else:
            top_field, nested_field = split_fields

        subdoc = document.model_fields.get(top_field)
        if not subdoc:
            return False
        if nested_field is None:
            return True

        nested_type = subdoc.annotation
        if isinstance(get_args(nested_type), list):
            # recursive bit :)
            return any(isvalid_field(t, nested_field) for t in get_args(nested_type))
        return isvalid_field(nested_type, nested_field)

    except Exception:  # pragma: no cover
        return False
    return True


def is_link_type(field_type: Type) -> bool:
    """Check if the field type is a Link or a list of Links.
    This is used to determine if the field is a relation field.
    If the field type is Optional[Link], return true

    Args:
        field_type (Type): The field type to check.

    Returns:
        bool: True if the field type is a Link or a list of Links, False otherwise.
    """
    if get_origin(field_type) is Link:
        return True
    if get_origin(field_type) is Union:
        field_args = get_args(field_type)
        if any(get_origin(arg) is Link for arg in field_args):
            return True
    return False


def is_list_of_links_type(field_type: Type) -> bool:
    """Check if the field type is a list of Links.

    Args:
        field_type (Type): The field type to check.

    Returns:
        bool: True if the field type is a list of Links, False otherwise.
    """
    if get_origin(field_type) is list:
        field_args = get_args(field_type)
        if len(field_args) == 1 and get_origin(field_args[0]) is Link:
            return True

    # if is Optional[List[Link]], return true
    if get_origin(field_type) is Union:
        field_args = get_args(field_type)
        if any(
            get_origin(arg) is list and get_origin(get_args(arg)[0]) is Link
            for arg in field_args
        ):
            return True

    return False


def resolve_deep_query(
    where: Dict[str, Any],
    document: Type[Document],
    latest_field: Optional[str] = None,
) -> QNode:
    _all_queries = []
    for key in where:
        if key in ["or", "and"]:
            _arr = [(resolve_deep_query(q, document, latest_field)) for q in where[key]]
            if len(_arr) > 0:
                funcs = {"or": lambda q1, q2: q1 | q2, "and": lambda q1, q2: q1 & q2}
                _all_queries.append(functools.reduce(funcs[key], _arr))
        elif key in OPERATORS:
            _all_queries.append(OPERATORS[key](latest_field, where[key]))  # type: ignore
        elif isvalid_field(document, key):
            _all_queries.append(resolve_deep_query(where[key], document, key))
    if _all_queries:
        return functools.reduce(lambda q1, q2: q1 & q2, _all_queries)
    return Q.empty()


def build_order_clauses(order_list: List[str]) -> List[Tuple[str, SortDirection]]:
    clauses: List[Tuple[str, SortDirection]] = []
    for value in order_list:
        key, order = value.strip().split(maxsplit=1)
        if key == "id":
            key = "_id"  # this is a beanie quirk
        direction = (
            SortDirection.DESCENDING
            if order.lower() == "desc"
            else SortDirection.ASCENDING
        )
        clauses.append((key, direction))
    return clauses


def normalize_list(
    arr: Optional[Sequence[Any]], is_default_sort_list: bool = False
) -> Optional[Sequence[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, MongoBaseField):
            _new_list.append(v.name)
        elif isinstance(v, str):
            _new_list.append(v)
        elif (
            isinstance(v, tuple) and is_default_sort_list
        ):  # Support for fields_default_sort:
            if (
                len(v) == 2
                and isinstance(v[0], (str, MongoBaseField))
                and isinstance(v[1], bool)
            ):
                _new_list.append(
                    (
                        v[0].name if isinstance(v[0], MongoBaseField) else v[0],
                        v[1],
                    )
                )
            else:
                raise ValueError(
                    "Invalid argument, Expected Tuple[str | monogoengine.BaseField, bool]"
                )

        else:
            raise ValueError(
                f"Expected str or monogoengine.BaseField, got {type(v).__name__}"
            )
    return _new_list
