import uuid
from typing import Any

from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterValidationError,
)
from starlette_admin.i18n import lazy_gettext as _


def _parse_uuid(raw: Any) -> uuid.UUID:
    """Parse a raw URL value into a `uuid.UUID`.

    Parsing here validates UUID syntax up front (raising
    [FilterValidationError][starlette_admin.filters.FilterValidationError] →
    HTTP 400 instead of letting strict database drivers like `asyncpg` raise
    a 500 `DBAPIError` on malformed strings) while letting each backend's
    `apply()` coerce to `str` if its underlying column stores strings.
    """
    text = str(raw).strip()
    try:
        return uuid.UUID(text)
    except ValueError:
        raise FilterValidationError(
            _("%(raw)s is not a valid UUID") % {"raw": repr(raw)}
        ) from None


class UUIDEqualFilter(BaseFilter):
    """`field == value` for UUID fields."""

    name = "eq"
    label = _("Equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> uuid.UUID:
        return _parse_uuid(raw)


class UUIDNotEqualFilter(BaseFilter):
    """`field != value` for UUID fields."""

    name = "neq"
    label = _("Not equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> uuid.UUID:
        return _parse_uuid(raw)
