"""Unit tests for starlette_admin.contrib.tortoise.filters plugin API.

No database connection required: covers the registration hook that lets a
plugin extend the default TortoiseFilterRegistry.
"""

from starlette_admin.contrib.tortoise.filters import (
    ContainsFilter,
    TortoiseFilterRegistry,
)
from starlette_admin.fields import BaseField


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
