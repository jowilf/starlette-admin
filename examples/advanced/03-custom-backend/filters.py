"""TinyDB implementations of the core filter contract.

Each class subclasses one of the core `BaseFilter`s and adds `apply()`, which
turns the parsed value into a TinyDB `QueryInstance`. `build_query` below
combines those fragments recursively per the `FilterGroup` tree.
"""

import re

from starlette_admin import IntegerField, ListField, StringField, TextAreaField
from starlette_admin.fields import BaseField
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRegistry,
    FilterRule,
)
from starlette_admin.filters.generic import (
    IsNotNullFilter,
    IsNullFilter,
)
from starlette_admin.filters.numeric import (
    BetweenFilter,
    EqualFilter,
    GreaterThanFilter,
    LessThanFilter,
    NotEqualFilter,
)
from starlette_admin.filters.string import (
    ContainsFilter,
    EndsWithFilter,
    NotContainsFilter,
    StartsWithFilter,
)
from tinydb import Query
from tinydb.queries import QueryInstance


def _field(ctx: FilterApplyContext) -> Query:
    return Query()[ctx.field_name]


# --- generic ------------------------------------------------------------------


class TinyDBEqualFilter(EqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) == ctx.value


class TinyDBNotEqualFilter(NotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) != ctx.value


class TinyDBIsNullFilter(IsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).test(lambda v: not v)


class TinyDBIsNotNullFilter(IsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).test(bool)


# --- numeric ------------------------------------------------------------------


class TinyDBNumericEqualFilter(EqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) == ctx.value


class TinyDBNumericNotEqualFilter(NotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) != ctx.value


class TinyDBGreaterThanFilter(GreaterThanFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) > ctx.value


class TinyDBLessThanFilter(LessThanFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) < ctx.value


class TinyDBBetweenFilter(BetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).test(lambda v: ctx.value <= v <= ctx.value2)


# --- string -------------------------------------------------------------------


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).search(re.escape(ctx.value), flags=re.IGNORECASE)


class TinyDBNotContainsFilter(NotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return ~_field(ctx).search(re.escape(ctx.value), flags=re.IGNORECASE)


class TinyDBStartsWithFilter(StartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).matches(f"{re.escape(ctx.value)}.*", flags=re.IGNORECASE)


class TinyDBEndsWithFilter(EndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).matches(f".*{re.escape(ctx.value)}", flags=re.IGNORECASE)


# --- registry -----------------------------------------------------------------

#: The `id` field is a TinyDB doc_id, not a real document field, so its
#: `IntegerField` sets `filters=[]` in `view.py` to opt out of numeric filters.
filter_registry = FilterRegistry()

#: Fallback for any `BaseField` without a more specific registration below, so
#: every field is at least filterable by null-ness.
filter_registry.register(BaseField, TinyDBIsNullFilter, TinyDBIsNotNullFilter)

_numeric_filters = (
    TinyDBNumericEqualFilter,
    TinyDBNumericNotEqualFilter,
    TinyDBGreaterThanFilter,
    TinyDBLessThanFilter,
    TinyDBBetweenFilter,
    TinyDBIsNullFilter,
    TinyDBIsNotNullFilter,
)
filter_registry.register(IntegerField, *_numeric_filters)
filter_registry.register(
    StringField,
    TinyDBContainsFilter,
    TinyDBNotContainsFilter,
    TinyDBStartsWithFilter,
    TinyDBEndsWithFilter,
    TinyDBEqualFilter,
    TinyDBNotEqualFilter,
    TinyDBIsNullFilter,
    TinyDBIsNotNullFilter,
)
filter_registry.register(
    TextAreaField,
    TinyDBContainsFilter,
    TinyDBNotContainsFilter,
    TinyDBStartsWithFilter,
    TinyDBEndsWithFilter,
    TinyDBIsNullFilter,
    TinyDBIsNotNullFilter,
)
filter_registry.register(ListField, TinyDBIsNullFilter, TinyDBIsNotNullFilter)


def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    """Recursively turn a `FilterGroup` tree into a single TinyDB `QueryInstance`."""
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (
            (combined | fragment) if group.logic == "or" else (combined & fragment)
        )
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)
