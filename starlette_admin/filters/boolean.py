from starlette_admin.filters.base import BaseFilter, FilterDataType
from starlette_admin.i18n import lazy_gettext as _


class IsTrueFilter(BaseFilter):
    """`field IS TRUE`. Needs no value: selecting it from the filter builder
    is the assertion.
    """

    name = "is_true"
    label = _("Is true")
    data_type = FilterDataType.NONE


class IsFalseFilter(BaseFilter):
    """`field IS FALSE`. Needs no value, see
    [IsTrueFilter][starlette_admin.filters.boolean.IsTrueFilter].
    """

    name = "is_false"
    label = _("Is false")
    data_type = FilterDataType.NONE
