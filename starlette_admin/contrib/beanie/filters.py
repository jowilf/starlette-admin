"""Beanie (MongoDB) implementations of the core filter contract.

Each ``apply()`` returns a standalone pymongo query-fragment dict for just its
own condition. ``build_filter_query`` recursively combines a ``FilterGroup``
tree into a single MongoDB filter dict via ``$and`` / ``$or``, which
``ModelView._build_query`` then merges with the full-text search query.
"""

import datetime
import re
from collections.abc import Sequence
from typing import Any

import bson.errors
from beanie import PydanticObjectId
from bson.objectid import ObjectId
from starlette.requests import Request
from starlette_admin.contrib.beanie.fields import BeanieObjectIdField
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    NumberField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.filters import (
    FilterApplyContext,
    FilterDataType,
    FilterGroup,
    FilterRegistry,
    FilterRule,
    FilterValidationError,
    filters,
)
from starlette_admin.filters.array import InFilter as BaseArrayInFilter
from starlette_admin.filters.array import NotInFilter as BaseArrayNotInFilter
from starlette_admin.filters.base import BaseFilter
from starlette_admin.filters.boolean import IsFalseFilter as BaseIsFalseFilter
from starlette_admin.filters.boolean import IsTrueFilter as BaseIsTrueFilter
from starlette_admin.filters.date import DateBetweenFilter as BaseDateBetweenFilter
from starlette_admin.filters.date import DateEqualFilter as BaseDateEqualFilter
from starlette_admin.filters.date import DateInFutureFilter as BaseDateInFutureFilter
from starlette_admin.filters.date import DateInPastFilter as BaseDateInPastFilter
from starlette_admin.filters.date import (
    DateTimeBetweenFilter as BaseDateTimeBetweenFilter,
)
from starlette_admin.filters.date import DateTimeEqualFilter as BaseDateTimeEqualFilter
from starlette_admin.filters.enum import InFilter as BaseInFilter
from starlette_admin.filters.enum import NotInFilter as BaseNotInFilter
from starlette_admin.filters.generic import EqualFilter as BaseEqualFilter
from starlette_admin.filters.generic import IsNotNullFilter as BaseIsNotNullFilter
from starlette_admin.filters.generic import IsNullFilter as BaseIsNullFilter
from starlette_admin.filters.generic import NotEqualFilter as BaseNotEqualFilter
from starlette_admin.filters.numeric import BetweenFilter as BaseBetweenFilter
from starlette_admin.filters.numeric import EqualFilter as BaseNumericEqualFilter
from starlette_admin.filters.numeric import GreaterThanFilter as BaseGreaterThanFilter
from starlette_admin.filters.numeric import (
    GreaterThanOrEqualFilter as BaseGreaterThanOrEqualFilter,
)
from starlette_admin.filters.numeric import LessThanFilter as BaseLessThanFilter
from starlette_admin.filters.numeric import (
    LessThanOrEqualFilter as BaseLessThanOrEqualFilter,
)
from starlette_admin.filters.numeric import NotEqualFilter as BaseNumericNotEqualFilter
from starlette_admin.filters.string import ContainsFilter as BaseContainsFilter
from starlette_admin.filters.string import EndsWithFilter as BaseEndsWithFilter
from starlette_admin.filters.string import NotContainsFilter as BaseNotContainsFilter
from starlette_admin.filters.string import StartsWithFilter as BaseStartsWithFilter
from starlette_admin.i18n import lazy_gettext as _

# Generic (equality + null checks)


class EqualFilter(BaseEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: ctx.value}


class NotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$ne": ctx.value}}


class IsNullFilter(BaseIsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: None}


class IsNotNullFilter(BaseIsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$ne": None}}


# String


class ContainsFilter(BaseContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$regex": re.escape(ctx.value), "$options": "i"}}


class NotContainsFilter(BaseNotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        import re as _re

        return {
            ctx.field_name: {"$not": _re.compile(re.escape(ctx.value), _re.IGNORECASE)}
        }


class StartsWithFilter(BaseStartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {
            ctx.field_name: {
                "$regex": f"^{re.escape(ctx.value)}",
                "$options": "i",
            }
        }


class EndsWithFilter(BaseEndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {
            ctx.field_name: {
                "$regex": f"{re.escape(ctx.value)}$",
                "$options": "i",
            }
        }


class StringEqualFilter(BaseEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {
            ctx.field_name: {"$regex": f"^{re.escape(ctx.value)}$", "$options": "i"}
        }


class StringNotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        import re as _re

        return {
            ctx.field_name: {
                "$not": _re.compile(f"^{re.escape(ctx.value)}$", _re.IGNORECASE)
            }
        }


# Numeric


class NumericEqualFilter(BaseNumericEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: ctx.value}


class NumericNotEqualFilter(BaseNumericNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$ne": ctx.value}}


class GreaterThanFilter(BaseGreaterThanFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gt": ctx.value}}


class LessThanFilter(BaseLessThanFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$lt": ctx.value}}


class GreaterThanOrEqualFilter(BaseGreaterThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gte": ctx.value}}


class LessThanOrEqualFilter(BaseLessThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$lte": ctx.value}}


class BetweenFilter(BaseBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gte": ctx.value, "$lte": ctx.value2}}


# Date / datetime


class DateEqualFilter(BaseDateEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: ctx.value}


class DateTimeEqualFilter(BaseDateTimeEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: ctx.value}


class DateBetweenFilter(BaseDateBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gte": ctx.value, "$lte": ctx.value2}}


class DateTimeBetweenFilter(BaseDateTimeBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gte": ctx.value, "$lte": ctx.value2}}


def _utcnow() -> datetime.datetime:
    """Return the current time as a naive UTC `datetime`.

    Naive (tzinfo-less) so it compares correctly with the naive UTC
    datetimes pymongo stores for `DateTimeField` values.
    """
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class DateInPastFilter(BaseDateInPastFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$lt": _utcnow()}}


class DateInFutureFilter(BaseDateInFutureFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$gt": _utcnow()}}


# Boolean


class IsTrueFilter(BaseIsTrueFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: True}


class IsFalseFilter(BaseIsFalseFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: False}


# Array


class ArrayInFilter(BaseArrayInFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$in": ctx.value}}


class ArrayNotInFilter(BaseArrayNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$nin": ctx.value}}


# Enum


class InFilter(BaseInFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$in": ctx.value}}


class NotInFilter(BaseNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$nin": ctx.value}}


# ObjectId (BeanieObjectIdField / id field)


def _parse_object_id(raw: Any) -> ObjectId:
    """Parse a single raw filter value into an `ObjectId`.

    Raises:
        FilterValidationError: If `raw` isn't a valid ObjectId string.
    """
    try:
        return PydanticObjectId(str(raw).strip())
    except (bson.errors.InvalidId, TypeError):
        raise FilterValidationError(
            _("Invalid ObjectId: %(value)s") % {"value": raw}
        ) from None


def _parse_object_id_list(raw: Any) -> list[ObjectId]:
    """Parse a raw filter value into a list of `ObjectId`s.

    Accepts a list/tuple of values or a single comma-separated string; blank
    entries are dropped.

    Raises:
        FilterValidationError: If no non-blank values remain, or if any
            value isn't a valid ObjectId string.
    """
    if isinstance(raw, (list, tuple)):
        values = [str(v).strip() for v in raw]
    else:
        values = [v.strip() for v in str(raw).split(",")]
    values = [v for v in values if v]
    if not values:
        raise FilterValidationError(_("At least one value is required")) from None
    try:
        return [PydanticObjectId(v) for v in values]
    except (bson.errors.InvalidId, TypeError) as exc:
        raise FilterValidationError(
            _("Invalid ObjectId in list: %(value)s") % {"value": exc}
        ) from exc


class ObjectIdEqualFilter(BaseFilter):
    name = "eq"
    label = _("Equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> ObjectId:
        return _parse_object_id(raw)

    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: ctx.value}


class ObjectIdNotEqualFilter(BaseFilter):
    name = "neq"
    label = _("Not equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> ObjectId:
        return _parse_object_id(raw)

    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$ne": ctx.value}}


class ObjectIdInFilter(BaseArrayInFilter):
    def parse_value(self, raw: Any) -> list[ObjectId]:  # ty: ignore[invalid-method-override]
        return _parse_object_id_list(raw)

    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$in": ctx.value}}


class ObjectIdNotInFilter(BaseArrayNotInFilter):
    def parse_value(self, raw: Any) -> list[ObjectId]:  # ty: ignore[invalid-method-override]
        return _parse_object_id_list(raw)

    def apply(self, ctx: FilterApplyContext) -> dict:
        return {ctx.field_name: {"$nin": ctx.value}}


# FilterGroup-to-MongoDB-query conversion

# Beanie and pymongo use "_id" internally; the admin field is named "id".
_FIELD_NAME_MAP = {"id": "_id"}


def build_filter_query(
    group: FilterGroup,
    fields_by_name: dict,
    registry: "FilterRegistry",
    view: Any,
    request: Request,
) -> dict | None:
    """Recursively combine a ``FilterGroup`` tree into a MongoDB filter dict.

    Returns ``None`` for an empty group. Fragments at one level are combined
    with ``{"$and": [...]}`` or ``{"$or": [...]}`` per ``group.logic``.
    """
    fragments: list[dict] = []
    for rule in group.rules:
        fragment = (
            build_filter_query(rule, fields_by_name, registry, view, request)
            if isinstance(rule, FilterGroup)
            else _build_rule_query(rule, fields_by_name, registry, view, request)
        )
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None
    if len(fragments) == 1:
        return fragments[0]

    op = "$or" if group.logic == "or" else "$and"
    return {op: fragments}


def _build_rule_query(
    rule: FilterRule,
    fields_by_name: dict,
    registry: "FilterRegistry",
    view: Any,
    request: Request,
) -> dict | None:
    """Build the MongoDB query fragment for a single `FilterRule` leaf.

    Looks up the concrete filter class for `rule.field`/`rule.filter` in
    `registry`, remaps `rule.field` from `"id"` to `"_id"` if needed, and
    delegates to that filter's `apply()`.

    Returns:
        The query fragment, or `None` if no matching filter is registered.
    """
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None

    field_name = _FIELD_NAME_MAP.get(rule.field, rule.field)
    ctx = FilterApplyContext(
        query=None,
        field_name=field_name,
        value=rule.value,
        value2=rule.value2,
        request=request,
        view=view,
    )
    return filter_cls().apply(ctx)


# Default registry

# Filters registered by plugins, merged into every BeanieFilterRegistry
# instance (see FilterRegistry._external_filters).
_EXTERNAL_FILTERS: dict[type["BaseField"], Sequence[type[BaseFilter]]] = {}


def register_filters(
    field_type: type["BaseField"], *filter_classes: type[BaseFilter]
) -> None:
    """Extend the default beanie `FilterRegistry`. Plugin API."""
    _EXTERNAL_FILTERS[field_type] = filter_classes


class BeanieFilterRegistry(FilterRegistry):
    """Default filter registry for Beanie-backed views, returned by
    `ModelView.get_filter_registry()`.

    Each `@filters`-decorated method below declares the filters available for
    one field type. To change what a field type offers, subclass this
    registry and override just that one method (see
    `FilterRegistry.filters_for` for how a field type without its own entry
    falls back to its nearest registered ancestor).
    """

    def _external_filters(self) -> dict[type["BaseField"], Sequence[type[BaseFilter]]]:
        return _EXTERNAL_FILTERS

    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        """Filters for any `BaseField` without a more specific registration
        below, so every field type is at least filterable by whether its
        value is null.
        """
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            StartsWithFilter,
            EndsWithFilter,
            StringEqualFilter,
            StringNotEqualFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(TextAreaField)
    def textarea_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            StartsWithFilter,
            EndsWithFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(EnumField)
    def enum_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            EqualFilter,
            NotEqualFilter,
            InFilter,
            NotInFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(NumberField, FloatField)
    def numeric_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        """`FloatField` is registered explicitly alongside `NumberField`
        because it subclasses `StringField` directly. Without this entry it
        would inherit string filters through the MRO walk instead of numeric
        ones.
        """
        return [
            NumericEqualFilter,
            NumericNotEqualFilter,
            GreaterThanFilter,
            LessThanFilter,
            GreaterThanOrEqualFilter,
            LessThanOrEqualFilter,
            BetweenFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(DateField)
    def date_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            DateEqualFilter,
            DateBetweenFilter,
            DateInPastFilter,
            DateInFutureFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(DateTimeField)
    def datetime_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            DateTimeEqualFilter,
            DateTimeBetweenFilter,
            DateInPastFilter,
            DateInFutureFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(BooleanField)
    def boolean_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsTrueFilter, IsFalseFilter, IsNullFilter, IsNotNullFilter]

    @filters(HasOne, HasMany)
    def relation_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsNullFilter, IsNotNullFilter]

    @filters(TagsField)
    def tags_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [ArrayInFilter, ArrayNotInFilter, IsNullFilter, IsNotNullFilter]

    @filters(BeanieObjectIdField)
    def object_id_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ObjectIdEqualFilter,
            ObjectIdNotEqualFilter,
            ObjectIdInFilter,
            ObjectIdNotInFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]
