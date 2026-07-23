"""Tortoise ORM implementations of the core filter contract.

Each ``apply()`` returns a standalone ``Q`` expression for just its own
condition. ``build_filter_query`` recursively combines a ``FilterGroup`` tree
into a single ``Q`` with ``&`` / ``|``, which ``ModelView`` applies to its
queryset in one ``filter()`` call, preserving nested AND/OR semantics.
"""

import datetime
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
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
    TextAreaField,
    TimeField,
)
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRegistry,
    FilterRule,
    filters,
)
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
from tortoise.expressions import Q

from .fields import BackwardHasOne
from .helpers import relation_source_field


def _tortoise_field(ctx: FilterApplyContext) -> Any:
    """Return the Tortoise field object being filtered on
    (`ctx.view` is always the owning `ModelView` here).
    """
    return ctx.view.model._meta.fields_map[ctx.field_name]  # ty: ignore[unresolved-attribute]


def _coerce_enum(ctx: FilterApplyContext, raw: Any) -> Any:
    """Coerce a raw filter value into the field's enum member.

    Filter values arrive as strings; `IntEnum` members need an integer
    lookup first. Tortoise's enum fields reject plain strings in filters,
    so coercion cannot be left to the ORM.
    """
    enum_type = _tortoise_field(ctx).enum_type
    try:
        return enum_type(raw)
    except ValueError:
        return enum_type(int(raw))


# Generic (null checks)


class IsNullFilter(BaseIsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {f"{ctx.field_name}__isnull": True}
        return Q(**filters)


class IsNotNullFilter(BaseIsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {f"{ctx.field_name}__isnull": False}
        return Q(**filters)


# To-one relations. Null checks target the raw key column: Tortoise resolves
# `author__isnull` as a nested filter on the related model and rejects it.


class RelationIsNullFilter(BaseIsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        source = relation_source_field(ctx.view.model, ctx.field_name)  # ty: ignore[unresolved-attribute]
        filters: dict[str, Any] = {f"{source}__isnull": True}
        return Q(**filters)


class RelationIsNotNullFilter(BaseIsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        source = relation_source_field(ctx.view.model, ctx.field_name)  # ty: ignore[unresolved-attribute]
        filters: dict[str, Any] = {f"{source}__isnull": False}
        return Q(**filters)


# String


class ContainsFilter(BaseContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__icontains": ctx.value})


class NotContainsFilter(BaseNotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return ~Q(**{f"{ctx.field_name}__icontains": ctx.value})


class StartsWithFilter(BaseStartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__istartswith": ctx.value})


class EndsWithFilter(BaseEndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__iendswith": ctx.value})


class StringEqualFilter(BaseEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__iexact": ctx.value})


class StringNotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return ~Q(**{f"{ctx.field_name}__iexact": ctx.value})


# Numeric


class NumericEqualFilter(BaseNumericEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{ctx.field_name: ctx.value})


class NumericNotEqualFilter(BaseNumericNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__not": ctx.value})


class GreaterThanFilter(BaseGreaterThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__gt": ctx.value})


class LessThanFilter(BaseLessThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__lt": ctx.value})


class GreaterThanOrEqualFilter(BaseGreaterThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__gte": ctx.value})


class LessThanOrEqualFilter(BaseLessThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__lte": ctx.value})


class BetweenFilter(BaseBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(
            **{
                f"{ctx.field_name}__gte": ctx.value,
                f"{ctx.field_name}__lte": ctx.value2,
            }
        )


# Date / datetime


class DateEqualFilter(BaseDateEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{ctx.field_name: ctx.value})


class DateTimeEqualFilter(BaseDateTimeEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{ctx.field_name: ctx.value})


class DateBetweenFilter(BaseDateBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(
            **{
                f"{ctx.field_name}__gte": ctx.value,
                f"{ctx.field_name}__lte": ctx.value2,
            }
        )


class DateTimeBetweenFilter(BaseDateTimeBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(
            **{
                f"{ctx.field_name}__gte": ctx.value,
                f"{ctx.field_name}__lte": ctx.value2,
            }
        )


def _now_for_field(ctx: FilterApplyContext) -> datetime.date | datetime.datetime:
    """Return "now" as the value type the filtered column stores.

    A `DateField` compares against today's date; a `DatetimeField` against an
    aware UTC datetime (Tortoise warns on naive datetimes when timezone
    support is active).
    """
    import tortoise.fields as tfields

    if isinstance(_tortoise_field(ctx), tfields.DateField):
        return datetime.date.today()
    return datetime.datetime.now(datetime.UTC)


class DateInPastFilter(BaseDateInPastFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {f"{ctx.field_name}__lt": _now_for_field(ctx)}
        return Q(**filters)


class DateInFutureFilter(BaseDateInFutureFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {f"{ctx.field_name}__gt": _now_for_field(ctx)}
        return Q(**filters)


# Boolean


class IsTrueFilter(BaseIsTrueFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {ctx.field_name: True}
        return Q(**filters)


class IsFalseFilter(BaseIsFalseFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {ctx.field_name: False}
        return Q(**filters)


# Enum


class EnumEqualFilter(BaseEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{ctx.field_name: _coerce_enum(ctx, ctx.value)})


class EnumNotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        return Q(**{f"{ctx.field_name}__not": _coerce_enum(ctx, ctx.value)})


class EnumInFilter(BaseInFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {
            f"{ctx.field_name}__in": [_coerce_enum(ctx, v) for v in ctx.value]
        }
        return Q(**filters)


class EnumNotInFilter(BaseNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> Q:
        filters: dict[str, Any] = {
            f"{ctx.field_name}__not_in": [_coerce_enum(ctx, v) for v in ctx.value]
        }
        return Q(**filters)


# FilterGroup-to-Q conversion


def build_filter_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
    view: Any,
    request: Request,
) -> Q | None:
    """Recursively combine a ``FilterGroup`` tree into a single ``Q``
    expression (or ``None`` for an empty tree, meaning "no filtering").
    """
    fragments = []
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
    result = fragments[0]
    for fragment in fragments[1:]:
        result = (result | fragment) if group.logic == "or" else (result & fragment)
    return result


def _build_rule_query(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
    view: Any,
    request: Request,
) -> Q | None:
    """Build the ``Q`` fragment for a single `FilterRule` leaf, or ``None``
    when no matching filter is registered.
    """
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None,
        field_name=rule.field,
        value=rule.value,
        value2=rule.value2,
        request=request,
        view=view,
    )
    return filter_cls().apply(ctx)


# Registry

# Filters registered by plugins, merged into every TortoiseFilterRegistry
# instance (see FilterRegistry._external_filters).
_EXTERNAL_FILTERS: dict[type["BaseField"], Sequence[type[BaseFilter]]] = {}


def register_filters(
    field_type: type["BaseField"], *filter_classes: type[BaseFilter]
) -> None:
    """Extend the default tortoise `FilterRegistry`. Plugin API."""
    _EXTERNAL_FILTERS[field_type] = filter_classes


class TortoiseFilterRegistry(FilterRegistry):
    """Default filter registry for Tortoise-backed views, returned by
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
            EnumEqualFilter,
            EnumNotEqualFilter,
            EnumInFilter,
            EnumNotInFilter,
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

    @filters(TimeField)
    def time_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        """Time-typed values cannot be bound as SQL parameters by every
        Tortoise backend, so only null checks are offered.
        """
        return [IsNullFilter, IsNotNullFilter]

    @filters(BooleanField)
    def boolean_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsTrueFilter, IsFalseFilter, IsNullFilter, IsNotNullFilter]

    @filters(HasOne)
    def to_one_relation_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [RelationIsNullFilter, RelationIsNotNullFilter]

    @filters(HasMany, BackwardHasOne)
    def to_many_relation_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        """To-many and backward relations have no raw key column on this model
        to null-check, and Tortoise joins would drop unmatched rows, so no
        filters are offered.
        """
        return []
