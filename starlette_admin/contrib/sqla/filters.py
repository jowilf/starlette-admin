"""SQLAlchemy implementations of the core filter contract.

Like `examples/custom-backend/filters.py`, each `apply()` ignores `ctx.query`
and returns a standalone boolean clause for just its own condition rather than
an incrementally `.where()`-chained `Select`: nested AND/OR groups need their
fragments combined with `and_`/`or_` *before* a single `.where(...)` lands on
the statement. Chaining `.where()` per-leaf would silently AND everything
together and break OR semantics. `build_filter_clause` does that combination
per the `FilterGroup` tree, and `ModelView.find_all`/`count` apply the result
once.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import String, and_, cast, false, func, not_, or_, true
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl
from starlette.requests import Request
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    NumberField,
    RelationField,
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
from starlette_admin.filters.date import (
    DateBetweenFilter as BaseDateBetweenFilter,
)
from starlette_admin.filters.date import DateEqualFilter as BaseDateEqualFilter
from starlette_admin.filters.date import (
    DateInFutureFilter as BaseDateInFutureFilter,
)
from starlette_admin.filters.date import DateInPastFilter as BaseDateInPastFilter
from starlette_admin.filters.date import (
    DateTimeBetweenFilter as BaseDateTimeBetweenFilter,
)
from starlette_admin.filters.date import (
    DateTimeEqualFilter as BaseDateTimeEqualFilter,
)
from starlette_admin.filters.date import TimeBetweenFilter as BaseTimeBetweenFilter
from starlette_admin.filters.date import TimeEqualFilter as BaseTimeEqualFilter
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
from starlette_admin.filters.numeric import (
    NotEqualFilter as BaseNumericNotEqualFilter,
)
from starlette_admin.filters.string import ContainsFilter as BaseContainsFilter
from starlette_admin.filters.string import EndsWithFilter as BaseEndsWithFilter
from starlette_admin.filters.string import (
    NotContainsFilter as BaseNotContainsFilter,
)
from starlette_admin.filters.string import StartsWithFilter as BaseStartsWithFilter


def _column(ctx: FilterApplyContext) -> InstrumentedAttribute:
    """Resolve `ctx.field_name` into the model column/relationship attribute
    being filtered on (`ctx.view` is always the owning `ModelView` here).
    """
    return getattr(ctx.view.model, ctx.field_name)  # ty: ignore[unresolved-attribute]


def _is_null(column: InstrumentedAttribute) -> Any:
    if isinstance(column.property, RelationshipProperty):
        if isinstance(column.impl, ScalarObjectAttributeImpl):
            return ~column.has()
        return ~column.any()
    return column.is_(None)


def _is_not_null(column: InstrumentedAttribute) -> Any:
    if isinstance(column.property, RelationshipProperty):
        if isinstance(column.impl, ScalarObjectAttributeImpl):
            return column.has()
        return column.any()
    return column.is_not(None)


# Generic (equality + null checks)


class EqualFilter(BaseEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == ctx.value


class NotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) != ctx.value


class IsNullFilter(BaseIsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _is_null(_column(ctx))


class IsNotNullFilter(BaseIsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _is_not_null(_column(ctx))


# String


class ContainsFilter(BaseContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return cast(_column(ctx), String).ilike(f"%{ctx.value}%")


class NotContainsFilter(BaseNotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return not_(cast(_column(ctx), String).ilike(f"%{ctx.value}%"))


class StartsWithFilter(BaseStartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return cast(_column(ctx), String).ilike(f"{ctx.value}%")


class EndsWithFilter(BaseEndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return cast(_column(ctx), String).ilike(f"%{ctx.value}")


# Numeric


class NumericEqualFilter(BaseNumericEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == ctx.value


class NumericNotEqualFilter(BaseNumericNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) != ctx.value


class GreaterThanFilter(BaseGreaterThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) > ctx.value


class LessThanFilter(BaseLessThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) < ctx.value


class GreaterThanOrEqualFilter(BaseGreaterThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) >= ctx.value


class LessThanOrEqualFilter(BaseLessThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) <= ctx.value


class BetweenFilter(BaseBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).between(ctx.value, ctx.value2)


# Date / datetime / time


class DateEqualFilter(BaseDateEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == ctx.value


class DateTimeEqualFilter(BaseDateTimeEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == ctx.value


class TimeEqualFilter(BaseTimeEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == ctx.value


class DateBetweenFilter(BaseDateBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).between(ctx.value, ctx.value2)


class DateTimeBetweenFilter(BaseDateTimeBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).between(ctx.value, ctx.value2)


class TimeBetweenFilter(BaseTimeBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).between(ctx.value, ctx.value2)


class DateInPastFilter(BaseDateInPastFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) < func.now()


class DateInFutureFilter(BaseDateInFutureFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) > func.now()


# Boolean


class IsTrueFilter(BaseIsTrueFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == true()


class IsFalseFilter(BaseIsFalseFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx) == false()


# Enum


class InFilter(BaseInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).in_(ctx.value)


class NotInFilter(BaseNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return _column(ctx).not_in(ctx.value)


# Combining a parsed FilterGroup tree into a single clause


def build_filter_clause(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
    view: Any,
    request: Request,
) -> Any | None:
    """Recursively turn a parsed `FilterGroup` tree into a single SQLAlchemy
    boolean clause (or `None` for an empty tree, meaning "no filtering").

    Each leaf `FilterRule` is resolved back to its concrete filter class via
    `fields_by_name`/`registry` (the same pair `_parse_list_params` validated
    it against) and turned into a clause fragment through `apply()`; nested
    `FilterGroup`s recurse. Fragments combine with `and_`/`or_` according to
    `group.logic`, mirroring the nested AND/OR semantics of the serialized
    filter tree.
    """
    fragments = []
    for rule in group.rules:
        fragment = (
            build_filter_clause(rule, fields_by_name, registry, view, request)
            if isinstance(rule, FilterGroup)
            else _build_rule_clause(rule, fields_by_name, registry, view, request)
        )
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None
    combine = or_ if group.logic == "or" else and_
    return combine(*fragments)


def _build_rule_clause(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
    view: Any,
    request: Request,
) -> Any | None:
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

# Filters registered by plugins, merged into every SqlaFilterRegistry
# instance (see FilterRegistry._external_filters).
_EXTERNAL_FILTERS: dict[type["BaseField"], Sequence[type[BaseFilter]]] = {}


def register_filters(
    field_type: type["BaseField"], *filter_classes: type[BaseFilter]
) -> None:
    """Extend the default sqla `FilterRegistry`. Plugin API."""
    _EXTERNAL_FILTERS[field_type] = filter_classes


class SqlaFilterRegistry(FilterRegistry):
    """Default filter registry for SQLAlchemy-backed views, returned by
    `ModelView.get_filter_registry()`.

    Each `@filters`-decorated method below declares the filters available for
    one field type. Field types not listed explicitly still resolve to a
    filter set because `FilterRegistry.filters_for` walks the field's MRO:
    `EmailField`/`URLField` inherit `StringField`'s filters, `IntegerField`/
    `DecimalField` inherit `NumberField`'s, `ArrowField` inherits
    `DateTimeField`'s, and `TimeZoneField`/`CountryField`/`CurrencyField`
    inherit `EnumField`'s.

    To change what a field type offers, subclass this registry and override
    just that one method, for example:

        class MyRegistry(SqlaFilterRegistry):
            @filters(StringField)
            def string_filters(self, field):
                return [ContainsFilter, IsNullFilter]
    """

    def _external_filters(self) -> dict[type["BaseField"], Sequence[type[BaseFilter]]]:
        return _EXTERNAL_FILTERS

    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        """Filters for any `BaseField` without a more specific registration
        below (for example `TagsField`, `JSONField`, `FileField`,
        `CollectionField`, `ListField`), so every field type is at least
        filterable by whether its value is null.
        """
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            StartsWithFilter,
            EndsWithFilter,
            EqualFilter,
            NotEqualFilter,
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
        because it subclasses `StringField` directly rather than
        `NumberField`. Without this entry it would inherit string filters
        through the MRO walk instead of numeric ones.
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
        return [TimeEqualFilter, TimeBetweenFilter, IsNullFilter, IsNotNullFilter]

    @filters(BooleanField)
    def boolean_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsTrueFilter, IsFalseFilter, IsNullFilter, IsNotNullFilter]

    @filters(RelationField)
    def relation_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsNullFilter, IsNotNullFilter]
