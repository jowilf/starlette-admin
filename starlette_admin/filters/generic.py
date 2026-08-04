from starlette_admin.filters.base import BaseFilter, FilterDataType
from starlette_admin.i18n import lazy_gettext as _


class EqualFilter(BaseFilter):
    """`field == value`. Generic equality, suitable for strings, enums and any
    other field whose values can be compared as-is. Numbers and temporal
    fields get their own equality filters (see `numeric`/`date`) since they
    need type-aware parsing.
    """

    name = "eq"
    label = _("Equal")
    data_type = FilterDataType.STRING


class NotEqualFilter(BaseFilter):
    """`field != value`. The negated counterpart of
    [EqualFilter][starlette_admin.filters.generic.EqualFilter].
    """

    name = "neq"
    label = _("Not equal")
    data_type = FilterDataType.STRING


class IsNullFilter(BaseFilter):
    """`field IS NULL` (or empty, for collection-like fields). Needs no value."""

    name = "is_null"
    label = _("Is null")
    data_type = FilterDataType.NONE


class IsNotNullFilter(BaseFilter):
    """`field IS NOT NULL` (or non-empty, for collection-like fields).
    Needs no value.
    """

    name = "is_not_null"
    label = _("Is not null")
    data_type = FilterDataType.NONE
