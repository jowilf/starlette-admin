"""Pure unit tests for `starlette_admin.contrib.sqla.filters`.

No database session is required. This module covers `parse_value` helpers, filter registry registrations, and `build_filter_clause` / `_build_rule_clause` behavior with mock or empty registries.
"""

import datetime
import enum
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import mysql, sqlite
from sqlalchemy.dialects.postgresql import JSONB, asyncpg
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    ContainsFilter,
    DateBetweenFilter,
    DateEqualFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    EnumAllOfFilter,
    EnumAnyOfFilter,
    EnumNoneOfFilter,
    GreaterThanFilter,
    GreaterThanOrEqualFilter,
    InFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    NotInFilter,
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
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRule,
    FilterValidationError,
)
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
    assert names == {"eq", "neq", "in", "not_in", "is_null", "is_not_null"}


def test_registry_enum_field_multiple():
    names = {
        f.name
        for f in filter_registry.filters_for(
            EnumField("permissions", choices=[("*:*", "All")], multiple=True)
        )
    }
    assert names == {"any_of", "all_of", "none_of", "is_null", "is_not_null"}


def test_registry_relation_field():
    names = {f.name for f in filter_registry.filters_for(RelationField("x"))}
    assert names == {"is_null", "is_not_null"}


def test_registry_base_field_fallback():
    """A field type without a dedicated registration still receives null filters."""
    names = {f.name for f in filter_registry.filters_for(BaseField("x"))}
    assert names == {"is_null", "is_not_null"}


def test_register_filters_plugin_api():
    """`register_filters` (the plugin API) extends every new
    `SqlaFilterRegistry` instance, since it feeds `_external_filters`."""
    from starlette_admin.contrib.sqla import filters as sqla_filters

    class _PluginField(BaseField):
        pass

    class _PluginFilter(ContainsFilter):
        name = "plugin-filter"

    sqla_filters.register_filters(_PluginField, _PluginFilter)
    try:
        registry = sqla_filters.SqlaFilterRegistry()
        assert registry.filters_for(_PluginField("x")) == [_PluginFilter]
    finally:
        del sqla_filters._EXTERNAL_FILTERS[_PluginField]


# ── Multi-value enum filters (ARRAY / JSONB / JSON) ──────────────────────────


class _ArrayBase(DeclarativeBase):
    pass


class _PermEnum(enum.StrEnum):
    ALL = "*:*"
    ADMIN = "admin:access"


class _PriorityEnum(enum.IntEnum):
    LOW = 1
    HIGH = 2


class _WrappedArray(sa.TypeDecorator):
    impl = sa.ARRAY(sa.String(100))
    cache_ok = True


class _RoleModel(_ArrayBase):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    permissions: Mapped[list[str]] = mapped_column(sa.ARRAY(sa.String(100)))
    wrapped_permissions: Mapped[list[str]] = mapped_column(_WrappedArray())
    enum_permissions: Mapped[list[_PermEnum]] = mapped_column(
        sa.ARRAY(sa.Enum(_PermEnum))
    )
    priorities: Mapped[list[_PriorityEnum]] = mapped_column(
        sa.ARRAY(sa.Enum(_PriorityEnum))
    )
    int_tags: Mapped[list[int]] = mapped_column(sa.ARRAY(sa.Integer))
    bool_flags: Mapped[list[bool]] = mapped_column(sa.ARRAY(sa.Boolean))
    jsonb_permissions: Mapped[list[str]] = mapped_column(JSONB)
    json_permissions: Mapped[list[str]] = mapped_column(sa.JSON)
    single_status: Mapped[str] = mapped_column(sa.String(50))


class _RoleView:
    model = _RoleModel


def _role_ctx(field_name: str, value) -> FilterApplyContext:
    return FilterApplyContext(
        query=None,
        field_name=field_name,
        value=value,
        view=_RoleView(),  # type: ignore[arg-type]
    )


def test_array_and_jsonb_enum_filters_compile_for_asyncpg():
    dialect = asyncpg.dialect()

    for col in ("permissions", "wrapped_permissions"):
        any_c = (
            sa.select(_RoleModel)
            .where(EnumAnyOfFilter().apply(_role_ctx(col, ["*:*"])))
            .compile(dialect=dialect)
        )
        assert f"roles.{col} && $1::VARCHAR(100)[]" in str(any_c)
        assert list(any_c.params.values()) == [["*:*"]]

        all_c = (
            sa.select(_RoleModel)
            .where(EnumAllOfFilter().apply(_role_ctx(col, ["*:*", "admin:access"])))
            .compile(dialect=dialect)
        )
        assert f"roles.{col} @> $1::VARCHAR(100)[]" in str(all_c)
        assert list(all_c.params.values()) == [["*:*", "admin:access"]]

        none_c = (
            sa.select(_RoleModel)
            .where(EnumNoneOfFilter().apply(_role_ctx(col, ["*:*"])))
            .compile(dialect=dialect)
        )
        assert f"roles.{col} IS NULL OR NOT (roles.{col} && $1::VARCHAR(100)[])" in str(
            none_c
        )

    # Multiple rules on the same ARRAY column bind distinct anonymous params.
    multi_c = (
        sa.select(_RoleModel)
        .where(
            sa.or_(
                InFilter().apply(_role_ctx("permissions", ["*:*"])),
                NotInFilter().apply(_role_ctx("permissions", ["admin:access"])),
            )
        )
        .compile(dialect=dialect)
    )
    assert "IN (" not in str(multi_c)
    assert "$1::VARCHAR(100)[]" in str(multi_c)
    assert "$2::VARCHAR(100)[]" in str(multi_c)

    # JSONB uses native @> containment; scalar columns still use IN (...).
    jb_all = (
        sa.select(_RoleModel)
        .where(
            EnumAllOfFilter().apply(
                _role_ctx("jsonb_permissions", ["*:*", "admin:access"])
            )
        )
        .compile(dialect=dialect)
    )
    assert "roles.jsonb_permissions @> $1::JSONB" in str(jb_all)
    assert list(jb_all.params.values()) == [["*:*", "admin:access"]]

    scalar_in = (
        sa.select(_RoleModel)
        .where(InFilter().apply(_role_ctx("single_status", ["active", "draft"])))
        .compile(dialect=dialect)
    )
    assert "roles.single_status IN (" in str(scalar_in)


def test_json_enum_filters_compile_per_dialect():
    clause = EnumAllOfFilter().apply(
        _role_ctx("json_permissions", ["*:*", "admin:access"])
    )
    stmt = sa.select(_RoleModel).where(clause)

    assert "json_each(roles.json_permissions)" in str(
        stmt.compile(dialect=sqlite.dialect())
    )
    assert "CAST(roles.json_permissions AS JSONB) @> $1::JSONB" in str(
        stmt.compile(dialect=asyncpg.dialect())
    )
    assert "JSON_CONTAINS(roles.json_permissions," in str(
        stmt.compile(dialect=mysql.dialect())
    )


def test_array_enum_filters_element_coercion():
    dialect = asyncpg.dialect()

    assert list(
        sa.select(_RoleModel)
        .where(EnumAnyOfFilter().apply(_role_ctx("enum_permissions", ["*:*", "ADMIN"])))
        .compile(dialect=dialect)
        .params.values()
    ) == [[_PermEnum.ALL, _PermEnum.ADMIN]]
    assert list(
        sa.select(_RoleModel)
        .where(EnumAnyOfFilter().apply(_role_ctx("priorities", ["1", "HIGH"])))
        .compile(dialect=dialect)
        .params.values()
    ) == [[_PriorityEnum.LOW, _PriorityEnum.HIGH]]
    assert list(
        sa.select(_RoleModel)
        .where(EnumAllOfFilter().apply(_role_ctx("int_tags", ["10", "20"])))
        .compile(dialect=dialect)
        .params.values()
    ) == [[10, 20]]
    assert list(
        sa.select(_RoleModel)
        .where(EnumAnyOfFilter().apply(_role_ctx("bool_flags", ["true", "0"])))
        .compile(dialect=dialect)
        .params.values()
    ) == [[True, False]]

    for col, bad in (
        ("int_tags", "not-an-int"),
        ("enum_permissions", "invalid"),
        ("bool_flags", "maybe"),
    ):
        with pytest.raises(FilterValidationError):
            EnumAnyOfFilter().apply(_role_ctx(col, [bad]))
