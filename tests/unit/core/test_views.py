"""Unit tests for starlette_admin.views helpers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.datastructures import QueryParams, State
from starlette.exceptions import HTTPException
from starlette_admin import (
    CollectionField,
    IntegerField,
    StringField,
)
from starlette_admin.types import RequestAction
from starlette_admin.views import BaseModelView, CustomView, DefaultIndexView
from starlette_admin.widgets import (
    ColumnWidget,
    HtmlWidget,
    PanelWidget,
    StatWidget,
)

from tests.integration.core.tinydb_model_view import (
    TinydbBaseModel,
    TinydbInlineModelView,
    TinydbModelView,
)


class _NoPkModel(TinydbBaseModel):
    title: str


class _NoPkView(TinydbModelView):
    pk_attr = ""
    fields = [StringField("title")]


def test_init_fields_with_no_pk_attr():
    view = _NoPkView(_NoPkModel)
    assert view.pk_attr == ""


class _Child(TinydbBaseModel):
    parent_id: int = 0
    config: dict = {}


class _NoFkInline(TinydbInlineModelView):
    model = _Child
    fk_attr = ""
    fields = [IntegerField("id")]


def test_inline_model_view_requires_fk_attr():
    with pytest.raises(ValueError, match="must define a foreign-key attribute"):
        _NoFkInline()


class _ValidInline(TinydbInlineModelView):
    model = _Child
    fk_attr = "parent_id"
    fields = [IntegerField("id")]


@pytest.mark.asyncio
async def test_build_fk_value_without_parent_view_raises():
    inline = _ValidInline()
    with pytest.raises(RuntimeError, match="before the inline was wired"):
        await inline.build_fk_value(MagicMock(), MagicMock())


class _CollectionInline(TinydbInlineModelView):
    model = _Child
    fk_attr = "parent_id"
    fields = [
        IntegerField("id"),
        CollectionField("config", fields=[StringField("key"), IntegerField("value")]),
    ]


def test_set_row_field_ids_propagates_collection_field_ids():
    inline = _CollectionInline()
    collection = inline.fields[1]
    assert isinstance(collection, CollectionField)
    inline.set_row_field_ids(2)
    assert collection.id.endswith(".2.config")
    assert collection.fields[0].id == f"{collection.id}.key"
    assert collection.fields[1].id == f"{collection.id}.value"


# ── _parse_sorts ──────────────────────────────────────────────────────────────


class _SortableModel(TinydbBaseModel):
    title: str
    views: int = 0


class _SortableView(TinydbModelView):
    fields = [IntegerField("id"), StringField("title"), IntegerField("views")]
    sortable_fields = ("id", "title", "views")


def test_parse_sorts_skips_param_without_separator():
    """Sort parameters that contain no '__' are silently skipped."""
    view = _SortableView(_SortableModel)
    accessible = {"id", "title", "views"}
    result = view._parse_sorts(["noseparator", "title__asc"], accessible)
    assert result == [("title", "asc")]


def test_parse_sorts_normalises_unknown_direction_to_asc():
    view = _SortableView(_SortableModel)
    accessible = {"title"}
    result = view._parse_sorts(["title__RANDOM"], accessible)
    assert result == [("title", "asc")]


def test_parse_sorts_ignores_inaccessible_field_not_in_sortable_fields():
    view = _SortableView(_SortableModel)
    accessible = {"title"}
    result = view._parse_sorts(["unknown__asc"], accessible)
    assert result == []


# ── _parse_list_params page_size validation ───────────────────────────────────


def _list_request(params: dict) -> MagicMock:
    request = MagicMock()
    request.state = State()
    request.state.action = RequestAction.LIST
    request.query_params = QueryParams(params)
    return request


def test_parse_list_params_rejects_page_size_not_in_options():
    view = _SortableView(_SortableModel)
    request = _list_request({"page_size": "7"})
    with pytest.raises(HTTPException) as exc_info:
        view._parse_list_params(request)
    assert exc_info.value.status_code == 400
    assert "7" in exc_info.value.detail


def test_parse_list_params_accepts_page_size_in_options():
    view = _SortableView(_SortableModel)
    request = _list_request({"page_size": "25"})
    params = view._parse_list_params(request)
    assert params.page_size == 25


def test_parse_list_params_accepts_default_page_size():
    view = _SortableView(_SortableModel)
    request = _list_request({"page_size": "10"})
    params = view._parse_list_params(request)
    assert params.page_size == 10


def test_parse_list_params_rejects_minus_one_when_not_in_options():
    view = _SortableView(_SortableModel)
    request = _list_request({"page_size": "-1"})
    with pytest.raises(HTTPException) as exc_info:
        view._parse_list_params(request)
    assert exc_info.value.status_code == 400


def test_parse_list_params_accepts_minus_one_when_in_options():
    class _AllView(_SortableView):
        page_size_options = [10, 25, -1]

    view = _AllView(_SortableModel)
    request = _list_request({"page_size": "-1"})
    params = view._parse_list_params(request)
    assert params.page_size == -1


def test_parse_list_params_defaults_when_page_size_absent():
    view = _SortableView(_SortableModel)
    request = _list_request({})
    params = view._parse_list_params(request)
    assert params.page_size == view.page_size


def test_parse_list_params_defaults_when_page_size_not_an_int():
    view = _SortableView(_SortableModel)
    request = _list_request({"page_size": "abc"})
    params = view._parse_list_params(request)
    assert params.page_size == view.page_size


class _CustomPageSizeView(_SortableView):
    page_size = 15
    page_size_options = [15, 30, 60]


def test_parse_list_params_accepts_custom_page_size_in_options():
    view = _CustomPageSizeView(_SortableModel)
    request = _list_request({"page_size": "30"})
    params = view._parse_list_params(request)
    assert params.page_size == 30


def test_parse_list_params_rejects_value_outside_custom_options():
    view = _CustomPageSizeView(_SortableModel)
    request = _list_request({"page_size": "25"})
    with pytest.raises(HTTPException) as exc_info:
        view._parse_list_params(request)
    assert exc_info.value.status_code == 400


def test_parse_list_params_accepts_page_size_equal_to_default_outside_options():
    """page_size == self.page_size is always valid, even if page_size_options diverges."""

    class _OffsetView(_SortableView):
        page_size = 15
        page_size_options = [10, 25, 50]

    view = _OffsetView(_SortableModel)
    request = _list_request({"page_size": "15"})
    params = view._parse_list_params(request)
    assert params.page_size == 15


# ── CustomView._resolve_widget callable paths ─────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_widget_with_async_callable():
    async def _widget_factory(request):
        return StatWidget(title="Async", value_callback=AsyncMock(return_value=1))

    view = CustomView(menu_label="Test", widget=_widget_factory)
    request = MagicMock()
    result = await view._resolve_widget(request)

    assert isinstance(result, StatWidget)
    assert result.title == "Async"


@pytest.mark.asyncio
async def test_resolve_widget_with_sync_callable():
    def _widget_factory(request):
        return StatWidget(title="Sync", value_callback=AsyncMock(return_value=2))

    view = CustomView(menu_label="Test", widget=_widget_factory)
    request = MagicMock()
    result = await view._resolve_widget(request)

    assert isinstance(result, StatWidget)
    assert result.title == "Sync"


# ── BaseModelView._resolve_form callable paths ────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_form_with_non_callable_returns_as_is():
    result = await BaseModelView._resolve_form("<form>static</form>")
    assert result == "<form>static</form>"


@pytest.mark.asyncio
async def test_resolve_form_with_sync_callable():
    def _build_form(request):
        return f"<form>{request}</form>"

    result = await BaseModelView._resolve_form(_build_form, "request-marker")
    assert result == "<form>request-marker</form>"


@pytest.mark.asyncio
async def test_resolve_form_with_async_callable():
    async def _build_form(request, obj):
        return f"<form>{request}-{obj}</form>"

    result = await BaseModelView._resolve_form(
        _build_form, "request-marker", "obj-marker"
    )
    assert result == "<form>request-marker-obj-marker</form>"


# ── DefaultIndexView ──────────────────────────────────────────────────────────


def _mock_request() -> MagicMock:
    """Return a mock Request with a real State object and stub URL helpers."""
    request = MagicMock()
    request.state = State()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.return_value = "http://test/url"
    request.query_params = QueryParams()
    return request


def _mock_model_view(accessible: bool = True) -> MagicMock:
    """Return a mock BaseModelView suitable for DefaultIndexView tests."""
    view = MagicMock()
    view.is_accessible.return_value = accessible
    view.key = "article"
    view.menu_label = "Articles"
    view.icon = None
    view.count = AsyncMock(return_value=5)
    view.get_fields_list.return_value = []
    return view


@pytest.mark.asyncio
async def test_default_index_view_count_error_shows_question_mark():
    """_build_view_panel swallows count exceptions and shows '?' in the panel."""
    failing_view = _mock_model_view()
    failing_view.count = AsyncMock(side_effect=RuntimeError("db down"))

    index_view = DefaultIndexView(model_views=[failing_view], env=MagicMock())
    request = _mock_request()
    panel = await index_view._build_view_panel(request, failing_view)

    count_widget = panel.children[0]
    assert isinstance(count_widget, HtmlWidget)
    assert "?" in count_widget.html


@pytest.mark.asyncio
async def test_default_index_view_uses_custom_welcome_text():
    """welcome_text != None is forwarded directly."""
    mock_view = _mock_model_view()
    index_view = DefaultIndexView(
        model_views=[mock_view],
        env=MagicMock(),
        welcome_text="Hello custom world!",
    )
    request = _mock_request()
    result = await index_view._build_widget(request)

    assert isinstance(result, ColumnWidget)
    welcome_widget = result.children[0]
    assert isinstance(welcome_widget, HtmlWidget)
    assert welcome_widget.html == "Hello custom world!"


@pytest.mark.asyncio
async def test_build_view_panel_shows_count_and_links():
    """_build_view_panel returns a PanelWidget with a count text widget."""

    mock_view = _mock_model_view()
    mock_view.count = AsyncMock(return_value=42)
    index_view = DefaultIndexView(model_views=[], env=MagicMock())
    request = _mock_request()

    panel = await index_view._build_view_panel(request, mock_view)

    assert isinstance(panel, PanelWidget)
    assert panel.title == "Articles"
    assert len(panel.children) == 1
    count_widget = panel.children[0]
    assert isinstance(count_widget, HtmlWidget)
    assert "42" in count_widget.html


# ── InlineModelView._find_foreign_view without parent ────────────────────────


def test_find_foreign_view_without_parent_raises():
    """_find_foreign_view raises RuntimeError when parent_view is None."""
    inline = _ValidInline()
    with pytest.raises(RuntimeError, match="wired to a parent view"):
        inline._find_foreign_view("some-key")


def test_find_foreign_view_delegates_to_parent():
    """_find_foreign_view delegates to parent_view._find_foreign_view when set."""
    inline = _ValidInline()
    parent = MagicMock()
    parent._find_foreign_view.return_value = MagicMock()
    inline.parent_view = parent
    result = inline._find_foreign_view("post")
    parent._find_foreign_view.assert_called_once_with("post")
    assert result is parent._find_foreign_view.return_value


# ── select2_result: __admin_repr__ without __admin_select2_repr__ ────────────


class _ReprOnlyModel(TinydbBaseModel):
    title: str

    def __admin_repr__(self, request) -> str:
        return self.title


class _ReprOnlyView(TinydbModelView):
    fields = [StringField("title")]


@pytest.mark.asyncio
async def test_select2_result_falls_back_to_escaped_admin_repr():
    """When `__admin_select2_repr__` is absent but `__admin_repr__` is defined,
    select2_result wraps the escaped `__admin_repr__` output in a span."""
    view = _ReprOnlyView(_ReprOnlyModel)
    obj = _ReprOnlyModel(title="<b>bold</b>")
    request = MagicMock()
    result = await view.select2_result(obj, request)
    assert result == "<span>&lt;b&gt;bold&lt;/b&gt;</span>"
