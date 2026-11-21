"""Unit tests for starlette_admin.contrib.tortoise.filters plugin API.

No database connection required: covers the registration hook that lets a
plugin extend the default TortoiseFilterRegistry.
"""

import uuid

import pytest
from starlette_admin.contrib.tortoise.filters import (
    ContainsFilter,
    TortoiseFilterRegistry,
    UUIDEqualFilter,
    UUIDNotEqualFilter,
)
from starlette_admin.fields import BaseField, UUIDField
from starlette_admin.filters import FilterApplyContext, FilterValidationError


def test_register_filters_plugin_api():
    """`register_filters` (the plugin API) extends every new
    `TortoiseFilterRegistry` instance, since it feeds `_external_filters`."""
    from starlette_admin.contrib.tortoise import filters as tortoise_filters

    class _PluginField(BaseField):
        pass

    class _PluginFilter(ContainsFilter):
        name = "plugin-filter"

    tortoise_filters.register_filters(_PluginField, _PluginFilter)
    try:
        registry = TortoiseFilterRegistry()
        assert registry.filters_for(_PluginField("x")) == [_PluginFilter]
    finally:
        del tortoise_filters._EXTERNAL_FILTERS[_PluginField]


def test_registry_uuid_field():
    registry = TortoiseFilterRegistry()
    filters = registry.filters_for(UUIDField("token"))
    by_name = {f.name: f for f in filters}
    assert set(by_name) == {
        "contains",
        "not_contains",
        "startswith",
        "endswith",
        "eq",
        "neq",
        "is_null",
        "is_not_null",
    }
    assert by_name["eq"] is UUIDEqualFilter
    assert by_name["neq"] is UUIDNotEqualFilter


def test_uuid_filter_parse_and_apply():
    expected = uuid.UUID("01a1771e-8578-70b4-b57b-8f331bba0c4c")
    assert UUIDEqualFilter().parse_value(str(expected)) == expected
    with pytest.raises(FilterValidationError):
        UUIDEqualFilter().parse_value("not-a-uuid")
    eq_q = UUIDEqualFilter().apply(FilterApplyContext(None, "token", expected))
    neq_q = UUIDNotEqualFilter().apply(FilterApplyContext(None, "token", expected))
    assert eq_q.filters == {"token": expected}
    assert neq_q._is_negated is True
