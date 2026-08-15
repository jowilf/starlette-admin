from typing import Any

from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterValidationError,
)
from starlette_admin.i18n import lazy_gettext as _


def _parse_choices(raw: Any) -> list[str]:
    """Parse a raw URL value into a list of choice values.

    The filter builder serialises a multi-select as a JSON array, but a
    comma-separated string is accepted too so the filter remains usable from
    a hand-built URL.
    """
    if isinstance(raw, (list, tuple)):
        values = [str(v).strip() for v in raw]
    else:
        values = [v.strip() for v in str(raw).split(",")]
    values = [v for v in values if v]
    if not values:
        raise FilterValidationError(_("At least one value is required"))
    return values


class InFilter(BaseFilter):
    """`field IN (values)`. Renders as a multi-select in the filter builder."""

    name = "in"
    label = _("Is one of")
    data_type = FilterDataType.ENUM

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class NotInFilter(BaseFilter):
    """`field NOT IN (values)`. The negated counterpart of
    [InFilter][starlette_admin.filters.enum.InFilter].
    """

    name = "not_in"
    label = _("Is not one of")
    data_type = FilterDataType.ENUM

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)
