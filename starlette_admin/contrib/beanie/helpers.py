import types as _types
from collections.abc import Sequence
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
)

from beanie import Document, Link
from beanie.odm.enums import SortDirection
from beanie.odm.fields import ExpressionField
from beanie.odm.operators.find.logical import LogicalOperatorForListOfExpressions


class BeanieLogicalOperator(LogicalOperatorForListOfExpressions):
    """Placeholder Beanie find operator that resolves to an empty query.

    `ModelView.build_full_text_search_query` returns an instance of this
    class when a document has no searchable string fields, so callers
    still get a valid (no-op) operator to pass to `find()`. It must be
    constructed with no expressions; `query` raises otherwise.
    """

    @property
    def query(self) -> dict[str, Any]:
        if not self.expressions:
            return {}
        raise ValueError(
            "BeanieLogicalOperator only supports an empty query: it must be "
            "constructed with no expressions."
        )


def isvalid_field(document: type[Document], field: str) -> bool:
    """Check whether `field` names an existing attribute on `document`.

    Nested attributes are addressed with dot notation (e.g., `"child.age"`);
    each dot-separated segment is validated against the corresponding
    model's fields.

    Args:
        document: The Beanie document (or nested pydantic model) type to
            check against.
        field: The field path to validate, possibly dotted.

    Returns:
        `True` if `field` resolves to an existing attribute, `False`
        otherwise, including when any intermediate segment is missing.
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
        return isvalid_field(nested_type, nested_field)

    except Exception:  # pragma: no cover
        return False


def resolve_expression_field_name(field: ExpressionField) -> str:
    """Return the admin-facing name for a Beanie `ExpressionField`.

    MongoDB's `_id` key is exposed to starlette-admin as `id`; every other
    expression field name passes through unchanged.
    """
    field_str = str(field)
    return "id" if field_str == "_id" else field_str


def _normalize_field_name(field: str | ExpressionField) -> str:
    """Resolve `field` to its admin-facing string name, if it's an `ExpressionField`."""
    if isinstance(field, ExpressionField):
        return resolve_expression_field_name(field)
    return field


def normalize_field_list(
    field_list: Sequence[str | ExpressionField | tuple[str | ExpressionField, bool]],
    is_default_sort_list: bool = False,
) -> list:
    """Normalize a list of field references to their admin-facing string names.

    Each entry may be a `str`, an `ExpressionField`, or, only when
    `is_default_sort_list` is `True`, a `(field, is_descending)` tuple as
    used for `fields_default_sort`. `ExpressionField`s are resolved with
    `resolve_expression_field_name`.

    Raises:
        ValueError: If a tuple entry is given while `is_default_sort_list`
            is `False`, if a tuple entry isn't shaped
            `(str | ExpressionField, bool)`, or if an entry is neither a
            `str`, an `ExpressionField`, nor (when allowed) such a tuple.
    """
    result: list[Any] = []
    for item in field_list:
        if isinstance(item, (str, ExpressionField)):
            result.append(_normalize_field_name(item))
        elif isinstance(item, tuple) and is_default_sort_list:
            if (
                len(item) == 2
                and isinstance(item[0], (str, ExpressionField))
                and isinstance(item[1], bool)
            ):
                result.append((_normalize_field_name(item[0]), item[1]))
            else:
                raise ValueError(
                    "Invalid argument, expected tuple[str | ExpressionField, bool]"
                )
        else:
            raise ValueError(
                f"Expected str or ExpressionField, got {type(item).__name__}"
            )
    return result


def _is_union(tp: type) -> bool:
    return get_origin(tp) is Union or isinstance(tp, _types.UnionType)


def is_link_type(field_type: type) -> bool:
    """Return `True` if `field_type` is a Beanie `Link[T]` annotation.

    Also matches a `Link[T]` wrapped in a `Union`/`Optional`, e.g.,
    `Link[T] | None`.
    """
    if get_origin(field_type) is Link:
        return True
    if _is_union(field_type):
        field_args = get_args(field_type)
        if any(get_origin(arg) is Link for arg in field_args):
            return True
    return False


def is_list_of_links_type(field_type: type) -> bool:
    """Return `True` if `field_type` is `list[Link[T]]`.

    Also matches `list[Link[T]]` wrapped in a `Union`/`Optional`, e.g.,
    `list[Link[T]] | None`.
    """
    if get_origin(field_type) is list:
        field_args = get_args(field_type)
        if len(field_args) == 1 and get_origin(field_args[0]) is Link:
            return True

    # Handle Optional[list[Link[...]]] and list[Link[...]] | None forms.
    if _is_union(field_type):
        field_args = get_args(field_type)
        if any(
            get_origin(arg) is list and get_origin(get_args(arg)[0]) is Link
            for arg in field_args
        ):
            return True
    return False


def build_order_clauses(
    sorts: Sequence[tuple[str, str]],
) -> list[tuple[str, SortDirection]]:
    """Convert `(field, direction)` sort pairs into pymongo sort clauses.

    Maps the admin's `id` field to MongoDB's `_id` key and the direction
    string `"desc"` (case-insensitive) to `SortDirection.DESCENDING`; any
    other direction value is treated as ascending.
    """
    clauses: list[tuple[str, SortDirection]] = []
    for key, order in sorts:
        field_key = "_id" if key == "id" else key
        direction = (
            SortDirection.DESCENDING
            if order.lower() == "desc"
            else SortDirection.ASCENDING
        )
        clauses.append((field_key, direction))
    return clauses
