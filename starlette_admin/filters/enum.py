from typing import Any

from starlette_admin.filters.array import _parse_array
from starlette_admin.filters.base import BaseFilter, FilterDataType
from starlette_admin.i18n import lazy_gettext as _


def _parse_choices(raw: Any) -> list[str]:
    """Parse a raw URL value into a list of choice values.

    Accepts a list/tuple (as produced by `_parse_filter_string` for
    comma-separated values) or a plain comma-separated string (hand-built URL),
    unquoting any quoted items so choice values with spaces or commas survive
    the round-trip.
    """
    return _parse_array(raw)


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


class AnyOfFilter(BaseFilter):
    """Multi-value enum field (`EnumField(multiple=True)`) contains at least
    one of the selected values.
    """

    name = "any_of"
    label = _("Has any of")
    data_type = FilterDataType.ENUM

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class AllOfFilter(BaseFilter):
    """Multi-value enum field (`EnumField(multiple=True)`) contains every one
    of the selected values.
    """

    name = "all_of"
    label = _("Has all of")
    data_type = FilterDataType.ENUM

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class NoneOfFilter(BaseFilter):
    """Multi-value enum field (`EnumField(multiple=True)`) contains none of
    the selected values. Rows with a `NULL` or empty value also match.
    """

    name = "none_of"
    label = _("Has none of")
    data_type = FilterDataType.ENUM

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)
