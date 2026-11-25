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

import enum
from collections.abc import Sequence
from typing import Any

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    String,
    TypeDecorator,
    and_,
    bindparam,
    cast,
    false,
    func,
    not_,
    or_,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.visitors import InternalTraversal
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
from starlette_admin.filters.base import BaseFilter, FilterValidationError
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
from starlette_admin.filters.date import DateTimeEqualFilter as BaseDateTimeEqualFilter
from starlette_admin.filters.date import TimeBetweenFilter as BaseTimeBetweenFilter
from starlette_admin.filters.date import TimeEqualFilter as BaseTimeEqualFilter
from starlette_admin.filters.enum import AllOfFilter as BaseEnumAllOfFilter
from starlette_admin.filters.enum import AnyOfFilter as BaseEnumAnyOfFilter
from starlette_admin.filters.enum import InFilter as BaseInFilter
from starlette_admin.filters.enum import NoneOfFilter as BaseEnumNoneOfFilter
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
    return getattr(ctx.view.model, ctx.field_name)  # ty: ignore[missing-attribute]


def _is_null(column: InstrumentedAttribute) -> Any:
    if isinstance(column.property, RelationshipProperty):
        if not column.property.uselist:
            return ~column.has()
        return ~column.any()
    return column.is_(None)


def _is_not_null(column: InstrumentedAttribute) -> Any:
    if isinstance(column.property, RelationshipProperty):
        if not column.property.uselist:
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


# Enum (scalar and multi-value ARRAY / JSONB / JSON columns)


class _JsonArrayContains(ColumnElement[bool]):
    """Dialect-portable predicate testing whether a `JSON` array column
    contains a single scalar element `value`.

    All three dialect-specific `bindparam`s are held on the element and listed
    in `_traverse_internals` so SQLAlchemy's statement cache rebinds fresh
    values cleanly across executions.
    """

    type = Boolean()
    inherit_cache = True
    _traverse_internals = [  # noqa: RUF012
        ("column", InternalTraversal.dp_clauseelement),
        ("scalar_param", InternalTraversal.dp_clauseelement),
        ("json_param", InternalTraversal.dp_clauseelement),
        ("jsonb_param", InternalTraversal.dp_clauseelement),
    ]

    def __init__(self, column: Any, value: Any) -> None:
        self.column = column
        self.scalar_param = bindparam(None, value)
        self.json_param = bindparam(None, [value], type_=JSON())
        self.jsonb_param = bindparam(None, [value], type_=JSONB())


@compiles(_JsonArrayContains, "sqlite")
def _compile_json_array_contains_sqlite(
    element: _JsonArrayContains, compiler: Any, **kw: Any
) -> str:
    col = compiler.process(element.column, **kw)
    val = compiler.process(element.scalar_param, **kw)
    return f"EXISTS (SELECT 1 FROM json_each({col}) WHERE json_each.value = {val})"


@compiles(_JsonArrayContains, "postgresql")
def _compile_json_array_contains_postgresql(
    element: _JsonArrayContains, compiler: Any, **kw: Any
) -> str:
    col = compiler.process(cast(element.column, JSONB), **kw)
    val = compiler.process(element.jsonb_param, **kw)
    return f"({col} @> {val})"


@compiles(_JsonArrayContains, "mysql")
@compiles(_JsonArrayContains, "mariadb")
def _compile_json_array_contains_mysql(
    element: _JsonArrayContains, compiler: Any, **kw: Any
) -> str:
    col = compiler.process(element.column, **kw)
    val = compiler.process(element.json_param, **kw)
    return f"JSON_CONTAINS({col}, {val})"


@compiles(_JsonArrayContains)
def _compile_json_array_contains_default(
    element: _JsonArrayContains, compiler: Any, **kw: Any
) -> str:
    raise NotImplementedError(
        f"JSON array filtering is not supported for dialect {compiler.dialect.name!r}"
    )


def _unwrap_column_type(column: InstrumentedAttribute) -> Any:
    """Return the underlying SQLAlchemy type, unwrapping any `TypeDecorator`."""
    col_type = getattr(column, "type", None)
    while isinstance(col_type, TypeDecorator):
        col_type = col_type.impl_instance
    return col_type


def _unwrap_array_type(column: InstrumentedAttribute) -> ARRAY | None:
    """Return the underlying `ARRAY` type when `column` is an array column."""
    col_type = _unwrap_column_type(column)
    return col_type if isinstance(col_type, ARRAY) else None


def _is_jsonb_column(column: InstrumentedAttribute) -> bool:
    """Return `True` when `column` is backed by a PostgreSQL `JSONB` type."""
    return isinstance(_unwrap_column_type(column), JSONB)


def _is_json_column(column: InstrumentedAttribute) -> bool:
    """Return `True` when `column` is backed by a SQLAlchemy `JSON` type."""
    return isinstance(_unwrap_column_type(column), JSON)


def _is_multi_value_column(column: InstrumentedAttribute) -> bool:
    """Return `True` when `column` stores a collection (`ARRAY`, `JSONB`, or `JSON`)."""
    return _unwrap_array_type(column) is not None or _is_json_column(column)


def _coerce_enum_element(enum_cls: type[enum.Enum], raw: Any) -> enum.Enum:
    try:
        return enum_cls(raw)
    except ValueError:
        pass
    if isinstance(raw, str) and raw in enum_cls.__members__:
        return enum_cls[raw]
    raw_str = str(raw)
    for member in enum_cls:
        if str(member.value) == raw_str:
            return member
    raise FilterValidationError(f"Invalid value {raw!r} for {enum_cls.__name__}")


def _coerce_array_element(py_type: type, raw: Any) -> Any:
    """Coerce a raw filter value string to an array element's Python type."""
    if isinstance(raw, py_type):
        return raw
    if issubclass(py_type, enum.Enum):
        return _coerce_enum_element(py_type, raw)
    if py_type is bool:
        lower = str(raw).strip().lower()
        if lower in ("true", "1"):
            return True
        if lower in ("false", "0"):
            return False
        raise FilterValidationError(f"Invalid boolean value {raw!r}")
    try:
        return py_type(raw)
    except (ValueError, TypeError) as exc:
        raise FilterValidationError(f"Invalid value {raw!r}: {exc}") from exc


def _coerce_array_values(
    column: InstrumentedAttribute, values: Sequence[Any]
) -> list[Any]:
    """Coerce raw string values to the element Python type of an `ARRAY` column."""
    array_type = _unwrap_array_type(column)
    if array_type is None:
        return list(values)
    try:
        py_type = array_type.item_type.python_type
    except NotImplementedError:
        return list(values)
    return [_coerce_array_element(py_type, v) for v in values]


def _array_any_of(column: InstrumentedAttribute, values: Sequence[Any]) -> Any:
    """Match rows whose `ARRAY`/`JSONB`/`JSON` column contains at least one
    value from `values`.
    """
    if _unwrap_array_type(column) is not None:
        coerced = _coerce_array_values(column, values)
        return column.op("&&", return_type=Boolean())(
            bindparam(None, coerced, type_=column.type)
        )
    if _is_jsonb_column(column):
        return or_(*[column.contains([v]) for v in values])
    if _is_json_column(column):
        return or_(*[_JsonArrayContains(column, v) for v in values])
    return column.in_(values)


def _array_all_of(column: InstrumentedAttribute, values: Sequence[Any]) -> Any:
    """Match rows whose `ARRAY`/`JSONB`/`JSON` column contains every value in
    `values`.
    """
    if _unwrap_array_type(column) is not None:
        coerced = _coerce_array_values(column, values)
        return column.op("@>", return_type=Boolean())(
            bindparam(None, coerced, type_=column.type)
        )
    if _is_jsonb_column(column):
        return column.contains(list(values))
    if _is_json_column(column):
        return and_(*[_JsonArrayContains(column, v) for v in values])
    return and_(*[column == v for v in values])


def _array_none_of(column: InstrumentedAttribute, values: Sequence[Any]) -> Any:
    """Match rows whose `ARRAY`/`JSONB`/`JSON` column contains none of `values`
    (including `NULL` or empty collections).
    """
    if _is_multi_value_column(column):
        return or_(column.is_(None), not_(_array_any_of(column, values)))
    return or_(column.is_(None), column.not_in(values))


class InFilter(BaseInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        column = _column(ctx)
        if _is_multi_value_column(column):
            return _array_any_of(column, ctx.value)
        return column.in_(ctx.value)


class NotInFilter(BaseNotInFilter):
    def apply(self, ctx: FilterApplyContext) -> Any:
        column = _column(ctx)
        if _is_multi_value_column(column):
            return _array_none_of(column, ctx.value)
        return column.not_in(ctx.value)


class EnumAnyOfFilter(BaseEnumAnyOfFilter):
    """Multi-value enum filter (`any_of`) for `ARRAY`, `JSONB`, and `JSON` columns."""

    def apply(self, ctx: FilterApplyContext) -> Any:
        return _array_any_of(_column(ctx), ctx.value)


class EnumAllOfFilter(BaseEnumAllOfFilter):
    """Multi-value enum filter (`all_of`) for `ARRAY`, `JSONB`, and `JSON` columns."""

    def apply(self, ctx: FilterApplyContext) -> Any:
        return _array_all_of(_column(ctx), ctx.value)


class EnumNoneOfFilter(BaseEnumNoneOfFilter):
    """Multi-value enum filter (`none_of`) for `ARRAY`, `JSONB`, and `JSON` columns."""

    def apply(self, ctx: FilterApplyContext) -> Any:
        return _array_none_of(_column(ctx), ctx.value)


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
        """Filters for `EnumField`. Multi-value fields (`multiple=True`) get
        collection-aware filters (`any_of`, `all_of`, `none_of`) instead of
        scalar comparisons.
        """
        if getattr(field, "multiple", False):
            return [
                EnumAnyOfFilter,
                EnumAllOfFilter,
                EnumNoneOfFilter,
                IsNullFilter,
                IsNotNullFilter,
            ]
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
