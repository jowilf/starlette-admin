from collections.abc import Sequence
from typing import Any, Literal, overload

from mongoengine.base.fields import BaseField as MongoBaseField
from mongoengine.queryset import Q as BaseQ


class Q(BaseQ):
    """A `mongoengine.Q` that also accepts positional `(field, value, op)` arguments.

    ``Q('name', 'Jo', 'istartswith')`` is equivalent to ``Q(name__istartswith='Jo')``.
    ``Q('name', 'John')`` is equivalent to ``Q(name='John')``.
    """

    def __init__(self, field: str, value: Any, op: str | None = None) -> None:
        field = f"{field.replace('.', '__')}__"
        if op is not None:
            field = f"{field}{op}"
        super().__init__(**{field: value})

    @classmethod
    def empty(cls) -> BaseQ:
        """Return an empty `Q` that matches every document.

        Used as the identity value when combining query fragments with `&`.
        """
        return BaseQ()


def build_order_clauses(sorts: Sequence[tuple[str, str]]) -> list[str]:
    """Convert `(field, direction)` sort pairs to MongoEngine order-by strings.

    Parameters:
        sorts: Pairs of field name and direction (`"asc"` or `"desc"`, case-insensitive).

    Returns:
        Field names prefixed with `+` (ascending) or `-` (descending), in the
        format `QuerySet.order_by` expects.
    """
    clauses = []
    for field_name, direction in sorts:
        prefix = "-" if direction.lower() == "desc" else "+"
        clauses.append(f"{prefix}{field_name}")
    return clauses


@overload
def normalize_list(
    arr: Sequence[Any] | None, is_default_sort_list: Literal[False] = False
) -> Sequence[str] | None: ...
@overload
def normalize_list(
    arr: Sequence[Any] | None, is_default_sort_list: Literal[True]
) -> Sequence[str | tuple[str, bool]] | None: ...
def normalize_list(
    arr: Sequence[Any] | None, is_default_sort_list: bool = False
) -> Sequence[str | tuple[str, bool]] | None:
    """Normalize a list of field references into a list of field-name strings.

    Lets view configuration attributes (e.g. `searchable_fields`, `sortable_fields`,
    `fields_default_sort`) accept mongoengine field objects (e.g. `Document.name`)
    in addition to plain strings.

    Parameters:
        arr: The list to normalize, or `None`.
        is_default_sort_list: If `True`, also accepts `(field, ascending)` tuples,
            matching the shape expected by `fields_default_sort`.

    Returns:
        `None` if `arr` is `None`; otherwise the normalized list, with each
        mongoengine field replaced by its name.

    Raises:
        ValueError: If an element of `arr` is not a recognized type, or (for
            `is_default_sort_list`) a tuple does not match `(str | BaseField, bool)`.
    """
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, MongoBaseField):
            _new_list.append(v.name)
        elif isinstance(v, str):
            _new_list.append(v)
        elif isinstance(v, tuple) and is_default_sort_list:
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
