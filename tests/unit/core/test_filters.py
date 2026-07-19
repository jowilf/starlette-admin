"""Unit tests for all starlette_admin.filters.* modules."""

import datetime

import pytest
from starlette_admin.filters.array import InFilter as ArrayInFilter
from starlette_admin.filters.array import NotInFilter as ArrayNotInFilter
from starlette_admin.filters.array import _parse_array
from starlette_admin.filters.base import (
    BaseFilter,
    FilterApplyContext,
    FilterDataType,
    FilterGroup,
    FilterRule,
    FilterValidationError,
)
from starlette_admin.filters.date import (
    DateBetweenFilter,
    DateEqualFilter,
    DateInFutureFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    TimeBetweenFilter,
    TimeEqualFilter,
    _parse_temporal,
)
from starlette_admin.filters.enum import InFilter, NotInFilter, _parse_choices
from starlette_admin.filters.generic import (
    EqualFilter,
    IsNotNullFilter,
    IsNullFilter,
    NotEqualFilter,
)
from starlette_admin.filters.numeric import (
    BetweenFilter,
    GreaterThanFilter,
    GreaterThanOrEqualFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    _parse_number,
)
from starlette_admin.filters.numeric import (
    EqualFilter as NumericEqualFilter,
)
from starlette_admin.filters.numeric import (
    NotEqualFilter as NumericNotEqualFilter,
)
from starlette_admin.filters.registry import FilterRegistry
from starlette_admin.filters.string import (
    ContainsFilter,
    EndsWithFilter,
    NotContainsFilter,
    StartsWithFilter,
)

# ── FilterValidationError ─────────────────────────────────────────────────────


def test_filter_validation_error_msg():
    err = FilterValidationError("bad value")
    assert err.msg == "bad value"
    assert str(err) == "bad value"


class _ConcreteFilter(BaseFilter):
    name = "test"
    label = "Test"
    data_type = FilterDataType.STRING


_ConcreteFilter.__abstractmethods__ = frozenset()


def test_base_filter_parse_value_passthrough():
    f = _ConcreteFilter()
    assert f.parse_value("hello") == "hello"


def _concrete(cls):
    """Return an instantiatable subclass of a BaseFilter for unit tests."""
    sub = type(cls.__name__, (cls,), {})
    sub.__abstractmethods__ = frozenset()
    return sub


_DateEqualFilter = _concrete(DateEqualFilter)
_DateTimeEqualFilter = _concrete(DateTimeEqualFilter)
_TimeEqualFilter = _concrete(TimeEqualFilter)
_DateBetweenFilter = _concrete(DateBetweenFilter)
_DateTimeBetweenFilter = _concrete(DateTimeBetweenFilter)
_TimeBetweenFilter = _concrete(TimeBetweenFilter)
_DateInPastFilter = _concrete(DateInPastFilter)
_DateInFutureFilter = _concrete(DateInFutureFilter)
_InFilter = _concrete(InFilter)
_NotInFilter = _concrete(NotInFilter)
_ArrayInFilter = _concrete(ArrayInFilter)
_ArrayNotInFilter = _concrete(ArrayNotInFilter)
_NumericEqualFilter = _concrete(NumericEqualFilter)
_NumericNotEqualFilter = _concrete(NumericNotEqualFilter)
_GreaterThanFilter = _concrete(GreaterThanFilter)
_LessThanFilter = _concrete(LessThanFilter)
_GreaterThanOrEqualFilter = _concrete(GreaterThanOrEqualFilter)
_LessThanOrEqualFilter = _concrete(LessThanOrEqualFilter)
_BetweenFilter = _concrete(BetweenFilter)


# ── date filters ──────────────────────────────────────────────────────────────


def test_parse_temporal_date():
    result = _parse_temporal(FilterDataType.DATE, "2024-01-15")
    assert result == datetime.date(2024, 1, 15)


def test_parse_temporal_time():
    result = _parse_temporal(FilterDataType.TIME, "10:30:00")
    assert result == datetime.time(10, 30, 0)


def test_parse_temporal_datetime():
    result = _parse_temporal(FilterDataType.DATETIME, "2024-01-15T10:30:00")
    assert result == datetime.datetime(2024, 1, 15, 10, 30, 0)


def test_parse_temporal_invalid():
    with pytest.raises(FilterValidationError, match="not a valid ISO-8601"):
        _parse_temporal(FilterDataType.DATE, "not-a-date")


def test_date_equal_filter():
    f = _DateEqualFilter()
    assert f.parse_value("2024-03-01") == datetime.date(2024, 3, 1)
    assert f.data_type == FilterDataType.DATE


def test_datetime_equal_filter():
    f = _DateTimeEqualFilter()
    assert f.data_type == FilterDataType.DATETIME


def test_time_equal_filter():
    f = _TimeEqualFilter()
    assert f.data_type == FilterDataType.TIME
    assert f.parse_value("09:00:00") == datetime.time(9, 0, 0)


def test_date_between_filter():
    f = _DateBetweenFilter()
    assert f.has_value2 is True
    assert f.parse_value("2024-01-01") == datetime.date(2024, 1, 1)


def test_datetime_between_filter():
    f = _DateTimeBetweenFilter()
    assert f.data_type == FilterDataType.DATETIME
    assert f.has_value2 is True


def test_time_between_filter():
    f = _TimeBetweenFilter()
    assert f.data_type == FilterDataType.TIME
    assert f.has_value2 is True


def test_date_in_past_filter():
    f = _DateInPastFilter()
    assert f.data_type == FilterDataType.NONE
    assert f.name == "in_past"


def test_date_in_future_filter():
    f = _DateInFutureFilter()
    assert f.data_type == FilterDataType.NONE
    assert f.name == "in_future"


def test_parse_temporal_datetime_with_timezone_conversion():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        result = _parse_temporal(FilterDataType.DATETIME, "2024-01-15T10:30:00")
        # 10:30 in NYC (UTC-5 in January) -> 15:30 UTC
        assert result == datetime.datetime(2024, 1, 15, 15, 30, 0)
        assert result.tzinfo is None
    finally:
        _timezone_conversion_enabled.set(original_enabled)


def test_parse_temporal_datetime_with_explicit_tz_offset():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        result = _parse_temporal(FilterDataType.DATETIME, "2024-01-15T10:30:00+02:00")
        # Explicit +02:00 overrides the user timezone assumption.
        assert result == datetime.datetime(2024, 1, 15, 8, 30, 0)
        assert result.tzinfo is None
    finally:
        _timezone_conversion_enabled.set(original_enabled)


def test_parse_temporal_date_unaffected_by_timezone_conversion():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        result = _parse_temporal(FilterDataType.DATE, "2024-01-15")
        assert result == datetime.date(2024, 1, 15)
    finally:
        _timezone_conversion_enabled.set(original_enabled)


def test_parse_temporal_time_unaffected_by_timezone_conversion():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        result = _parse_temporal(FilterDataType.TIME, "10:30:00")
        assert result == datetime.time(10, 30, 0)
    finally:
        _timezone_conversion_enabled.set(original_enabled)


# ── enum filters ──────────────────────────────────────────────────────────────


def test_parse_choices_list():
    assert _parse_choices(["a", "b", "c"]) == ["a", "b", "c"]


def test_parse_choices_csv_string():
    assert _parse_choices("a,b, c") == ["a", "b", "c"]


def test_parse_choices_empty_raises():
    with pytest.raises(FilterValidationError, match="At least one value"):
        _parse_choices("")


def test_in_filter():
    f = _InFilter()
    assert f.data_type == FilterDataType.ENUM
    assert f.parse_value("x,y") == ["x", "y"]


def test_not_in_filter():
    f = _NotInFilter()
    assert f.data_type == FilterDataType.ENUM
    assert f.parse_value(["p", "q"]) == ["p", "q"]


# ── array filters ─────────────────────────────────────────────────────────────


def test_parse_array_list():
    assert _parse_array(["a", "b", "c"]) == ["a", "b", "c"]


def test_parse_array_csv_string():
    assert _parse_array("a,b, c") == ["a", "b", "c"]


def test_parse_array_quoted_string_with_comma():
    assert _parse_array('"a, b",c') == ["a, b", "c"]


def test_parse_array_quoted_string_with_escaped_quote():
    assert _parse_array('"a \\"b\\" c",d') == ['a "b" c', "d"]


def test_parse_array_empty_raises():
    with pytest.raises(FilterValidationError, match="At least one value"):
        _parse_array("")


def test_parse_array_whitespace_only_raises():
    with pytest.raises(FilterValidationError, match="At least one value"):
        _parse_array("  ,  ")


def test_array_in_filter():
    f = _ArrayInFilter()
    assert f.data_type == FilterDataType.ARRAY
    assert f.parse_value("x,y") == ["x", "y"]


def test_array_not_in_filter():
    f = _ArrayNotInFilter()
    assert f.data_type == FilterDataType.ARRAY
    assert f.parse_value(["p", "q"]) == ["p", "q"]


# ── numeric filters ───────────────────────────────────────────────────────────


def test_parse_number_int():
    assert _parse_number("42") == 42
    assert isinstance(_parse_number("42"), int)


def test_parse_number_float():
    assert _parse_number("3.14") == pytest.approx(3.14)
    assert isinstance(_parse_number("3.14"), float)


def test_parse_number_invalid():
    with pytest.raises(FilterValidationError, match="not a valid number"):
        _parse_number("not-a-number")


def test_numeric_equal_filter():
    f = _NumericEqualFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.parse_value("7") == 7
    assert f.parse_value("2.5") == pytest.approx(2.5)


def test_numeric_not_equal_filter():
    f = _NumericNotEqualFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.parse_value("0") == 0
    assert f.parse_value("1.1") == pytest.approx(1.1)


def test_greater_than_filter():
    f = _GreaterThanFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.parse_value("10") == 10


def test_less_than_filter():
    f = _LessThanFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.parse_value("5") == 5


def test_greater_than_or_equal_filter():
    f = _GreaterThanOrEqualFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.name == "gte"
    assert f.parse_value("10") == 10


def test_less_than_or_equal_filter():
    f = _LessThanOrEqualFilter()
    assert f.data_type == FilterDataType.NUMBER
    assert f.name == "lte"
    assert f.parse_value("5") == 5


def test_between_filter():
    f = _BetweenFilter()
    assert f.has_value2 is True
    assert f.parse_value("1.5") == pytest.approx(1.5)


# ── string and generic filter attrs ─────────────────────────────────────────


def test_string_filter_attrs():
    assert ContainsFilter.data_type == FilterDataType.STRING
    assert NotContainsFilter.data_type == FilterDataType.STRING
    assert StartsWithFilter.data_type == FilterDataType.STRING
    assert EndsWithFilter.data_type == FilterDataType.STRING
    assert EqualFilter.data_type == FilterDataType.STRING
    assert NotEqualFilter.data_type == FilterDataType.STRING
    assert IsNullFilter.data_type == FilterDataType.NONE
    assert IsNotNullFilter.data_type == FilterDataType.NONE


# ── FilterRegistry ────────────────────────────────────────────────────────────


def test_registry_filters_for_field_with_explicit_override():
    from starlette_admin import StringField

    registry = FilterRegistry()
    registry.register(StringField, ContainsFilter, EqualFilter)

    field = StringField("title", filters=[StartsWithFilter])
    # explicit field.filters override wins over registry
    assert registry.filters_for(field) == [StartsWithFilter]


def test_registry_get_filter_not_found():
    from starlette_admin import StringField

    registry = FilterRegistry()
    registry.register(StringField, ContainsFilter)

    field = StringField("title")
    assert registry.get_filter(field, "nonexistent_filter") is None


def test_registry_get_filter_found():
    from starlette_admin import StringField

    registry = FilterRegistry()
    registry.register(StringField, ContainsFilter, EqualFilter)

    field = StringField("title")
    assert registry.get_filter(field, "contains") is ContainsFilter
    assert registry.get_filter(field, "eq") is EqualFilter


def test_registry_mro_lookup():
    from starlette_admin import StringField, TextAreaField

    registry = FilterRegistry()
    registry.register(StringField, ContainsFilter)
    # TextAreaField is a subclass of StringField, should inherit filters
    field = TextAreaField("body")
    assert registry.filters_for(field) == [ContainsFilter]


def test_registry_unregistered_field_returns_empty():
    from starlette_admin import IntegerField

    registry = FilterRegistry()
    field = IntegerField("count")
    assert registry.filters_for(field) == []


def test_registry_decorator_collects_methods_on_construction():
    from starlette_admin import StringField
    from starlette_admin.filters.registry import filters

    class MyRegistry(FilterRegistry):
        @filters(StringField)
        def string_filters(self, field):
            return [ContainsFilter, EqualFilter]

    registry = MyRegistry()
    field = StringField("title")
    assert registry.filters_for(field) == [ContainsFilter, EqualFilter]


def test_registry_decorator_receives_field_instance():
    from starlette_admin import StringField
    from starlette_admin.filters.registry import filters

    seen = []

    class MyRegistry(FilterRegistry):
        @filters(StringField)
        def string_filters(self, field):
            seen.append(field)
            return [ContainsFilter]

    registry = MyRegistry()
    field = StringField("title")
    registry.filters_for(field)
    assert seen == [field]


def test_registry_subclass_overrides_parent_method():
    from starlette_admin import StringField
    from starlette_admin.filters.registry import filters

    class BaseRegistry(FilterRegistry):
        @filters(StringField)
        def string_filters(self, field):
            return [ContainsFilter, EqualFilter]

    class ChildRegistry(BaseRegistry):
        @filters(StringField)
        def string_filters(self, field):
            return [ContainsFilter]

    field = StringField("title")
    assert BaseRegistry().filters_for(field) == [ContainsFilter, EqualFilter]
    assert ChildRegistry().filters_for(field) == [ContainsFilter]


def test_registry_constructor_dict_overrides_decorated_method():
    from starlette_admin import StringField
    from starlette_admin.filters.registry import filters

    class MyRegistry(FilterRegistry):
        @filters(StringField)
        def string_filters(self, field):
            return [ContainsFilter, EqualFilter]

    registry = MyRegistry(filters={StringField: [StartsWithFilter]})
    field = StringField("title")
    assert registry.filters_for(field) == [StartsWithFilter]


def test_registry_two_field_types_one_method():
    from starlette_admin import IntegerField, StringField
    from starlette_admin.filters.registry import filters

    class MyRegistry(FilterRegistry):
        @filters(StringField, IntegerField)
        def shared_filters(self, field):
            return [EqualFilter]

    registry = MyRegistry()
    assert registry.filters_for(StringField("title")) == [EqualFilter]
    assert registry.filters_for(IntegerField("count")) == [EqualFilter]


# ── FilterGroup helpers ───────────────────────────────────────────────────────


def test_filter_group_is_empty():
    assert FilterGroup().is_empty() is True
    assert FilterGroup(rules=[FilterRule("f", "eq", "x")]).is_empty() is False


def test_filter_apply_context_defaults():
    ctx = FilterApplyContext(query=None, field_name="title", value="hello")
    assert ctx.value2 is None
    assert ctx.request is None
    assert ctx.view is None
