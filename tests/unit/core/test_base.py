"""Unit tests for starlette_admin.base.BaseAdmin."""

from unittest.mock import MagicMock

import pytest
from markupsafe import Markup
from starlette.datastructures import State
from starlette_admin import BaseAdmin, StringField
from starlette_admin.types import RequestAction
from starlette_admin.views import Link

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView


def test_add_link_registers_view():
    admin = BaseAdmin(secret_key="test-secret")
    link = Link(menu_label="Home Page", icon="fa fa-link", url="/")

    admin.add_link(link)

    assert admin._views == [link]
    assert link not in admin._model_views


class _Person(TinydbBaseModel):
    first_name: str = ""


class _AllFieldsHiddenView(TinydbModelView):
    """Every field excluded from create, so `resolve_form_layout` has
    nothing to wrap and returns `None`."""

    fields = [StringField("first_name", exclude_from_create=True)]


class _VisibleFieldView(TinydbModelView):
    fields = [StringField("first_name")]


def _fake_request(action: str = "CREATE"):
    request = MagicMock()
    request.state = State()
    request.state.action = RequestAction(action)
    return request


class TestRenderFormBody:
    """Tests for `BaseAdmin._render_form_body`."""

    @pytest.mark.asyncio
    async def test_none_tree_yields_empty_form_body(self):
        """When `resolve_form_layout` returns `None`, `config` must be
        populated with empty placeholders instead of being left unset."""
        admin = BaseAdmin(secret_key="test-secret")
        view = _AllFieldsHiddenView(_Person)
        config: dict = {}

        await admin._render_form_body(_fake_request(), view, {}, None, config)

        assert config["form_body"] == Markup("")
        assert config["widget_additional_css"] == []
        assert config["widget_additional_js"] == []

    @pytest.mark.asyncio
    async def test_resolved_tree_populates_form_body_and_links(self):
        """When a widget tree resolves, `config` holds the rendered HTML
        plus the tree's additional CSS/JS links, rather than the
        `tree is None` placeholders."""
        admin = BaseAdmin(secret_key="test-secret")
        view = _VisibleFieldView(_Person)
        config: dict = {}

        await admin._render_form_body(
            _fake_request(), view, {"first_name": ""}, None, config
        )

        assert "first_name" in config["form_body"]
        assert isinstance(config["widget_additional_css"], list)
        assert isinstance(config["widget_additional_js"], list)
