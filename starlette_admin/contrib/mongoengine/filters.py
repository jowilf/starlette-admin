"""MongoEngine implementations of the core filter contract.

Each `apply()` returns a MongoEngine `Q` fragment for its own condition.
`build_filter_query` combines a `FilterGroup` tree into a single `QNode` via
`&` / `|`, which is then ANDed with the full-text search `QNode` in `_build_query`.
"""

import datetime
from collections.abc import Sequence
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from mongoengine.queryset import Q, QNode
from starlette.requests import Request
from starlette_admin.contrib.mongoengine.fields import ObjectIdField
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
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: ctx.value})


class NotEqualFilter(BaseNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__ne": ctx.value})


class IsNullFilter(BaseIsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: None})


class IsNotNullFilter(BaseIsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__ne": None})


# String


class ContainsFilter(BaseContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__icontains": ctx.value})


class NotContainsFilter(BaseNotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__not__icontains": ctx.value})


class StartsWithFilter(BaseStartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__istartswith": ctx.value})


class EndsWithFilter(BaseEndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__iendswith": ctx.value})


# Numeric


class NumericEqualFilter(BaseNumericEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: ctx.value})


class NumericNotEqualFilter(BaseNumericNotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__ne": ctx.value})


class GreaterThanFilter(BaseGreaterThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__gt": ctx.value})


class LessThanFilter(BaseLessThanFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__lt": ctx.value})


class GreaterThanOrEqualFilter(BaseGreaterThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__gte": ctx.value})


class LessThanOrEqualFilter(BaseLessThanOrEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__lte": ctx.value})


class BetweenFilter(BaseBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__gte": ctx.value}) & Q(
            **{f"{ctx.field_name}__lte": ctx.value2}
        )


# Date / datetime


class DateEqualFilter(BaseDateEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: ctx.value})


class DateTimeEqualFilter(BaseDateTimeEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: ctx.value})


class DateBetweenFilter(BaseDateBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__gte": ctx.value}) & Q(
            **{f"{ctx.field_name}__lte": ctx.value2}
        )


class DateTimeBetweenFilter(BaseDateTimeBetweenFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__gte": ctx.value}) & Q(
            **{f"{ctx.field_name}__lte": ctx.value2}
        )


class DateInPastFilter(BaseDateInPastFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(
            **{
                f"{ctx.field_name}__lt": datetime.datetime.now(datetime.UTC).replace(
                    tzinfo=None
                )
            }
        )


class DateInFutureFilter(BaseDateInFutureFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(
            **{
                f"{ctx.field_name}__gt": datetime.datetime.now(datetime.UTC).replace(
                    tzinfo=None
                )
            }
        )


# Boolean


class IsTrueFilter(BaseIsTrueFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: True})


class IsFalseFilter(BaseIsFalseFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: False})


# Array (TagsField / ListField) # noqa: ERA001


class ArrayInFilter(BaseArrayInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__in": ctx.value})


class ArrayNotInFilter(BaseArrayNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__nin": ctx.value})


# Enum


class InFilter(BaseInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__in": ctx.value})


class NotInFilter(BaseNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__nin": ctx.value})


# ObjectId filters


def _parse_object_id(raw: Any) -> ObjectId:
    """Parse a raw filter value into a MongoDB `ObjectId`.

    Raises:
        FilterValidationError: If `raw` is not a valid ObjectId.
    """
    try:
        return ObjectId(str(raw).strip())
    except (InvalidId, TypeError):
        raise FilterValidationError(
            _("Invalid ObjectId: %(value)s") % {"value": raw}
        ) from None


def _parse_object_id_list(raw: Any) -> list[ObjectId]:
    """Parse a raw filter value into a list of `ObjectId`.

    Accepts a list/tuple of values or a comma-separated string; blank entries
    are dropped.

    Raises:
        FilterValidationError: If no values remain after filtering, or if any
            remaining value is not a valid ObjectId.
    """
    if isinstance(raw, (list, tuple)):
        values = [str(v).strip() for v in raw]
    else:
        values = [v.strip() for v in str(raw).split(",")]
    values = [v for v in values if v]
    if not values:
        raise FilterValidationError(_("At least one value is required")) from None
    try:
        return [ObjectId(v) for v in values]
    except (InvalidId, TypeError) as exc:
        raise FilterValidationError(
            _("Invalid ObjectId in list: %(value)s") % {"value": exc}
        ) from exc


class ObjectIdEqualFilter(BaseFilter):
    """ObjectId field equals the given ObjectId."""

    name = "eq"
    label = _("Equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> ObjectId:
        return _parse_object_id(raw)

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{ctx.field_name: ctx.value})


class ObjectIdNotEqualFilter(BaseFilter):
    """ObjectId field does not equal the given ObjectId."""

    name = "neq"
    label = _("Not equal")
    data_type = FilterDataType.STRING

    def parse_value(self, raw: Any) -> ObjectId:
        return _parse_object_id(raw)

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__ne": ctx.value})


class ObjectIdInFilter(BaseArrayInFilter):
    """ObjectId field is one of the given ObjectIds (tag-style input)."""

    def parse_value(self, raw: Any) -> list[ObjectId]:  # ty: ignore[invalid-method-override]
        return _parse_object_id_list(raw)

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__in": ctx.value})


class ObjectIdNotInFilter(BaseArrayNotInFilter):
    """ObjectId field is not one of the given ObjectIds."""

    def parse_value(self, raw: Any) -> list[ObjectId]:  # ty: ignore[invalid-method-override]
        return _parse_object_id_list(raw)

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Q(**{f"{ctx.field_name}__nin": ctx.value})


# Combine a parsed FilterGroup tree into a single QNode


def build_filter_query(
    group: FilterGroup,
    fields_by_name: dict,
    registry: "FilterRegistry",
    view: Any,
    request: Request,
) -> QNode | None:
    """Recursively combine a `FilterGroup` tree into a single MongoEngine `QNode`.

    Fragments at a single level are combined with `&` (AND) or `|` (OR)
    according to `group.logic`. Nested groups are resolved recursively before
    being merged into their parent.

    Parameters:
        group: The parsed filter tree to convert.
        fields_by_name: Mapping of field name to the field instance that owns
            it, used to resolve which filter applies to each rule.
        registry: The registry used to look up the filter class for each rule.
        view: The view the filters apply to, forwarded to each filter's
            `apply()` via `FilterApplyContext`.
        request: The current request, forwarded to each filter's `apply()`.

    Returns:
        The combined `QNode`, or `None` if the group has no rules to apply.
    """
    fragments: list[QNode] = []
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
    for f in fragments[1:]:
        result = result | f if group.logic == "or" else result & f
    return result


def _build_rule_query(
    rule: FilterRule,
    fields_by_name: dict,
    registry: "FilterRegistry",
    view: Any,
    request: Request,
) -> QNode | None:
    """Resolve the filter class for `rule` and apply it, returning its `QNode`
    fragment, or `None` if no filter is registered for `rule.filter` on this field.
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


# Default registry

# Filters registered by plugins, merged into every MongoEngineFilterRegistry
# instance (see FilterRegistry._external_filters).
_EXTERNAL_FILTERS: dict[type["BaseField"], Sequence[type[BaseFilter]]] = {}


def register_filters(
    field_type: type["BaseField"], *filter_classes: type[BaseFilter]
) -> None:
    """Extend the default mongoengine `FilterRegistry`. Plugin API."""
    _EXTERNAL_FILTERS[field_type] = filter_classes


class MongoEngineFilterRegistry(FilterRegistry):
    """Default filter registry for MongoEngine-backed views, returned by
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
        because in starlette_admin it subclasses `StringField` directly
        rather than `NumberField`. Without this entry it would inherit string
        filters through the MRO walk instead of numeric ones.
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

    @filters(RelationField)
    def relation_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [IsNullFilter, IsNotNullFilter]

    @filters(TagsField)
    def tags_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [ArrayInFilter, ArrayNotInFilter, IsNullFilter, IsNotNullFilter]

    @filters(ObjectIdField)
    def object_id_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ObjectIdEqualFilter,
            ObjectIdNotEqualFilter,
            ObjectIdInFilter,
            ObjectIdNotInFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]
