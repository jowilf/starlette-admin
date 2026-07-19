"""Pure unit tests for `starlette_admin.contrib.sqla.filters`.

No database session is required. This module covers `parse_value` helpers, filter registry registrations, and `build_filter_clause` / `_build_rule_clause` behavior with mock or empty registries."""

import datetime
from unittest.mock import MagicMock

import pytest
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    ContainsFilter,
    DateBetweenFilter,
    DateEqualFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    GreaterThanFilter,
    GreaterThanOrEqualFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    SqlaFilterRegistry,
    TimeBetweenFilter,
    TimeEqualFilter,
    _build_rule_clause,
    build_filter_clause,
)
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
from starlette_admin.filters import FilterGroup, FilterRule
from starlette_admin.filters.registry import FilterRegistry

filter_registry = SqlaFilterRegistry()

# ── parse_value ───────────────────────────────────────────────────────────────


def test_numeric_parse_value_int():
    assert GreaterThanFilter().parse_value("42") == 42
    assert isinstance(GreaterThanFilter().parse_value("42"), int)


def test_numeric_parse_value_float():
    assert LessThanFilter().parse_value("3.14") == pytest.approx(3.14)
    assert isinstance(LessThanFilter().parse_value("3.14"), float)


def test_greater_than_or_equal_parse_value():
    assert GreaterThanOrEqualFilter().parse_value("42") == 42


def test_less_than_or_equal_parse_value():
    assert LessThanOrEqualFilter().parse_value("3.14") == pytest.approx(3.14)


def test_between_parse_value():
    assert BetweenFilter().parse_value("7") == 7


def test_date_parse_value():
    assert DateEqualFilter().parse_value("2024-01-15") == datetime.date(2024, 1, 15)


def test_datetime_parse_value():
    assert DateTimeEqualFilter().parse_value(
        "2024-01-15T10:30:00"
    ) == datetime.datetime(2024, 1, 15, 10, 30)


def test_time_parse_value():
    assert TimeEqualFilter().parse_value("09:00:00") == datetime.time(9, 0)


def test_date_between_parse_value():
    assert DateBetweenFilter().parse_value("2024-06-01") == datetime.date(2024, 6, 1)


def test_datetime_between_parse_value():
    result = DateTimeBetweenFilter().parse_value("2024-06-01T00:00:00")
    assert result == datetime.datetime(2024, 6, 1, 0, 0)


def test_time_between_parse_value():
    assert TimeBetweenFilter().parse_value("12:30:00") == datetime.time(12, 30)


def test_datetime_parse_value_with_timezone_conversion():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        result = DateTimeEqualFilter().parse_value("2024-01-15T10:30:00")
        assert result == datetime.datetime(2024, 1, 15, 15, 30, 0)
        assert result.tzinfo is None
    finally:
        _timezone_conversion_enabled.set(original_enabled)


def test_date_parse_value_unaffected_by_timezone_conversion():
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        assert DateEqualFilter().parse_value("2024-01-15") == datetime.date(2024, 1, 15)
    finally:
        _timezone_conversion_enabled.set(original_enabled)


# ── build_filter_clause: no-session paths ────────────────────────────────────


class _DummyView:
    model = None


def _registry() -> FilterRegistry:
    r = FilterRegistry()
    r.register(StringField, ContainsFilter)
    r.register(NumberField, GreaterThanFilter, BetweenFilter)
    return r


def test_build_filter_clause_empty_group():
    result = build_filter_clause(
        FilterGroup(logic="and", rules=[]),
        {"name": StringField("name")},
        _registry(),
        _DummyView(),
        MagicMock(),
    )
    assert result is None


def test_build_filter_clause_all_fragments_none():
    """If every leaf has no matching filter, the result is `None`."""
    empty = FilterRegistry()
    empty.register(StringField)  # No filters attached.

    result = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[FilterRule(field="name", filter="contains", value="x")],
        ),
        {"name": StringField("name")},
        empty,
        _DummyView(),
        MagicMock(),
    )
    assert result is None


def test_build_rule_clause_filter_not_registered():
    empty = FilterRegistry()
    empty.register(StringField)

    result = _build_rule_clause(
        FilterRule(field="name", filter="nonexistent", value="x"),
        {"name": StringField("name")},
        empty,
        _DummyView(),
        MagicMock(),
    )
    assert result is None


# ── filter_registry registrations ────────────────────────────────────────────


def test_registry_string_field():
    names = {f.name for f in filter_registry.filters_for(StringField("x"))}
    assert names >= {
        "contains",
        "not_contains",
        "startswith",
        "endswith",
        "eq",
        "neq",
        "is_null",
        "is_not_null",
    }


def test_registry_textarea_field():
    names = {f.name for f in filter_registry.filters_for(TextAreaField("x"))}
    assert "contains" in names
    assert "is_null" in names
    assert "eq" not in names


def test_registry_number_field():
    names = {f.name for f in filter_registry.filters_for(NumberField("x"))}
    assert names >= {
        "eq",
        "neq",
        "gt",
        "lt",
        "gte",
        "lte",
        "between",
        "is_null",
        "is_not_null",
    }


def test_registry_float_field():
    names = {f.name for f in filter_registry.filters_for(FloatField("x"))}
    assert names >= {
        "eq",
        "neq",
        "gt",
        "lt",
        "gte",
        "lte",
        "between",
        "is_null",
        "is_not_null",
    }


def test_registry_date_field():
    names = {f.name for f in filter_registry.filters_for(DateField("x"))}
    assert names >= {"eq", "between", "in_past", "in_future", "is_null", "is_not_null"}


def test_registry_datetime_field():
    names = {f.name for f in filter_registry.filters_for(DateTimeField("x"))}
    assert names >= {"eq", "between", "in_past", "in_future", "is_null", "is_not_null"}


def test_registry_time_field():
    names = {f.name for f in filter_registry.filters_for(TimeField("x"))}
    assert names >= {"eq", "between", "is_null", "is_not_null"}


def test_registry_boolean_field():
    names = {f.name for f in filter_registry.filters_for(BooleanField("x"))}
    assert names >= {"is_true", "is_false", "is_null", "is_not_null"}


def test_registry_enum_field():
    names = {
        f.name
        for f in filter_registry.filters_for(EnumField("x", choices=[("a", "A")]))
    }
    assert names >= {"eq", "neq", "in", "not_in", "is_null", "is_not_null"}


def test_registry_relation_field():
    names = {f.name for f in filter_registry.filters_for(RelationField("x"))}
    assert names == {"is_null", "is_not_null"}


def test_registry_base_field_fallback():
    """A field type without a dedicated registration still receives null filters."""
    names = {f.name for f in filter_registry.filters_for(BaseField("x"))}
    assert names == {"is_null", "is_not_null"}
