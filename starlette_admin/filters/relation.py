"""Backend-agnostic base filters for relation fields (`HasOne`/`HasMany`).

Each filter's value is a list of the related records' primary keys, picked in
the filter builder from a searchable Select2 dropdown backed by the foreign
view's `relation-lookup` API. Primary keys stay raw strings here; each ORM
contrib package converts them to the foreign key column's type in `apply()`.
"""

from typing import Any

from starlette_admin.filters.base import BaseFilter, FilterDataType
from starlette_admin.filters.enum import _parse_choices
from starlette_admin.i18n import lazy_gettext as _


class RelationInFilter(BaseFilter):
    """To-one relation (`HasOne`) points to one of the selected records."""

    name = "in"
    label = _("Is one of")
    data_type = FilterDataType.RELATION

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class RelationNotInFilter(BaseFilter):
    """To-one relation (`HasOne`) does not point to any of the selected
    records. Rows with no related record at all also match.
    """

    name = "not_in"
    label = _("Is not one of")
    data_type = FilterDataType.RELATION

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class RelationAnyOfFilter(BaseFilter):
    """To-many relation (`HasMany`) contains at least one of the selected
    records.
    """

    name = "any_of"
    label = _("Has any of")
    data_type = FilterDataType.RELATION

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)


class RelationNoneOfFilter(BaseFilter):
    """To-many relation (`HasMany`) contains none of the selected records.
    Rows with no related records at all also match.
    """

    name = "none_of"
    label = _("Has none of")
    data_type = FilterDataType.RELATION

    def parse_value(self, raw: Any) -> list[str]:
        return _parse_choices(raw)
