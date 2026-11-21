"""Unit tests for starlette_admin.contrib.tortoise.filters plugin API.

No database connection required: covers the registration hook that lets a
plugin extend the default TortoiseFilterRegistry.
"""

import datetime
from zoneinfo import ZoneInfo

from starlette_admin.contrib.tortoise.filters import (
    ContainsFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    TortoiseFilterRegistry,
)
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterApplyContext


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

    ctx = FilterApplyContext(
        query=None,
        field_name="created_at",
        value=datetime.datetime(2024, 3, 1, 12, 0),
        value2=datetime.datetime(2024, 3, 2, 12, 0),
    )
    expected_dt1 = datetime.datetime(2024, 3, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
    expected_dt2 = datetime.datetime(2024, 3, 2, 12, 0, tzinfo=ZoneInfo("UTC"))
    eq_q = DateTimeEqualFilter().apply(ctx)
    assert eq_q.filters == {"created_at": expected_dt1}
    between_q = DateTimeBetweenFilter().apply(ctx)
    assert between_q.filters == {
        "created_at__gte": expected_dt1,
        "created_at__lte": expected_dt2,
    }
