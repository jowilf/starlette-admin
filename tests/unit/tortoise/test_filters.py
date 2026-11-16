"""Unit tests for starlette_admin.contrib.tortoise.filters."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from starlette_admin.contrib.tortoise import filters as tortoise_filters
from starlette_admin.contrib.tortoise.fields import BackwardHasOne
from starlette_admin.contrib.tortoise.filters import (
    BackwardRelationInFilter,
    BackwardRelationNotInFilter,
    ContainsFilter,
    RelationAnyOfFilter,
    RelationInFilter,
    RelationNoneOfFilter,
    RelationNotInFilter,
    TortoiseFilterRegistry,
)
from starlette_admin.contrib.tortoise.view import ModelView as TortoiseModelView
from starlette_admin.fields import BaseField, HasMany, HasOne
from starlette_admin.filters import FilterApplyContext, FilterValidationError
from tortoise import fields as t_fields
from tortoise.models import Model as TortoiseModel


def test_register_filters_plugin_api():
    """`register_filters` (the plugin API) extends every new
    `TortoiseFilterRegistry` instance, since it feeds `_external_filters`."""

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


def test_tortoise_relation_filters_and_registry():
    registry = TortoiseFilterRegistry()
    assert {f.name for f in registry.filters_for(HasOne("a", key="a"))} == {
        "in",
        "not_in",
        "is_null",
        "is_not_null",
    }
    assert {f.name for f in registry.filters_for(BackwardHasOne("a", key="a"))} == {
        "in",
        "not_in",
    }
    assert {f.name for f in registry.filters_for(HasMany("a", key="a"))} == {
        "any_of",
        "none_of",
    }

    pk_field = SimpleNamespace(to_python_value=int)
    related_model = SimpleNamespace(_meta=SimpleNamespace(pk=pk_field, pk_attr="id"))
    rel_field = SimpleNamespace(related_model=related_model, source_field="author_id")
    model = MagicMock()
    model._meta.pk_attr = "id"
    model._meta.fields_map = {"author": rel_field, "tags": rel_field}
    view = MagicMock(model=model)
    ctx_one = FilterApplyContext(
        query=None,
        field_name="author",
        value=["1", "2"],
        view=view,
    )
    ctx_many = FilterApplyContext(
        query=None,
        field_name="tags",
        value=["1", "2"],
        view=view,
    )
    assert RelationInFilter().apply(ctx_one).filters == {"author_id__in": [1, 2]}
    assert len(RelationNotInFilter().apply(ctx_one).children) == 2
    assert "id__in" in BackwardRelationInFilter().apply(ctx_one).filters
    assert "id__not_in" in BackwardRelationNotInFilter().apply(ctx_one).filters
    assert "id__in" in RelationAnyOfFilter().apply(ctx_many).filters
    assert "id__not_in" in RelationNoneOfFilter().apply(ctx_many).filters

    bad_ctx = FilterApplyContext(
        query=None,
        field_name="author",
        value=["not-an-int"],
        view=view,
    )
    with pytest.raises(FilterValidationError, match="Invalid primary key"):
        RelationInFilter().apply(bad_ctx)

    class _Item(TortoiseModel):
        id = t_fields.IntField(pk=True)

    item_view = TortoiseModelView(_Item)
    item_view._validate_relation_pks(["1", "2"])
    with pytest.raises(FilterValidationError, match="Invalid primary key"):
        item_view._validate_relation_pks(["not-an-int"])
