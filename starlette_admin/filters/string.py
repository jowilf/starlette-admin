from starlette_admin.filters.base import BaseFilter, FilterDataType
from starlette_admin.i18n import lazy_gettext as _


class ContainsFilter(BaseFilter):
    """`field` contains `value` (case-insensitive substring match)."""

    name = "contains"
    label = _("Contains")
    data_type = FilterDataType.STRING


class NotContainsFilter(BaseFilter):
    """The negated counterpart of
    [ContainsFilter][starlette_admin.filters.string.ContainsFilter].
    """

    name = "not_contains"
    label = _("Does not contain")
    data_type = FilterDataType.STRING


class StartsWithFilter(BaseFilter):
    """`field` starts with `value` (case-insensitive)."""

    name = "startswith"
    label = _("Starts with")
    data_type = FilterDataType.STRING


class EndsWithFilter(BaseFilter):
    """`field` ends with `value` (case-insensitive)."""

    name = "endswith"
    label = _("Ends with")
    data_type = FilterDataType.STRING
