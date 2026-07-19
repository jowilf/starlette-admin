from typing import Any

from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterValidationError,
)
from starlette_admin.i18n import lazy_gettext as _


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return v


def _parse_array(raw: Any) -> list[str]:
    """Parse a raw URL value into a list of strings.

    Accepts a list/tuple (as produced by `_parse_filter_string` for
    comma-separated values) or a plain comma-separated string (hand-built URL).
    Each part is unquoted so values with spaces survive the round-trip.
    """
    if isinstance(raw, (list, tuple)):
        values = [_unquote(str(v)) for v in raw]
    else:
        parts: list[str] = []
        cur: list[str] = []
        in_q = False
        for ch in str(raw):
            if ch == '"':
                in_q = not in_q
                cur.append(ch)
            elif not in_q and ch == ",":
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        parts.append("".join(cur))
        values = [_unquote(p) for p in parts]
    values = [v for v in values if v]
    if not values:
        raise FilterValidationError(_("At least one value is required"))
    return values


class InFilter(BaseFilter):
    """List/array field contains at least one of the given values (tag input)."""

    name = "in"
    label = _("Is one of")
    data_type = FilterDataType.ARRAY

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_array(raw)


class NotInFilter(BaseFilter):
    """A list or array field contains none of the given values (tag input)."""

    name = "not_in"
    label = _("Is not one of")
    data_type = FilterDataType.ARRAY

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_array(raw)
