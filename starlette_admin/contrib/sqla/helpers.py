from collections.abc import Sequence
from typing import Any, Literal, overload

from sqlalchemy.orm import InstrumentedAttribute
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


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
    """Normalize a list of column references into plain strings.

    Converts each `InstrumentedAttribute` in `arr` to its column key so
    downstream code can work with plain field names regardless of whether the
    caller passed model attributes (e.g. `Post.title`) or strings.

    Parameters:
        arr: The list of column references to normalize. Can be `None`.
        is_default_sort_list: If `True`, allow `(column, direction)` tuples,
            as used by `fields_default_sort`.

    Returns:
        The normalized list of strings (or `(str, bool)` tuples when
        `is_default_sort_list` is `True`), or `None` if `arr` is `None`.

    Raises:
        ValueError: If an item is not a `str`, `InstrumentedAttribute`, or (when
            `is_default_sort_list` is `True`) a valid two-item sort tuple.
    """
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
        ):  # (column, direction) pair from fields_default_sort
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
        _log.debug(
            "extract_column_python_type: %s has no python_type, defaulting to str", attr
        )
        return str
