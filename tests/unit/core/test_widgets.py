"""Unit tests for starlette_admin.widgets."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from jinja2 import Environment, PackageLoader
from markupsafe import Markup
from starlette.requests import Request
from starlette_admin.theme import CoreIcons
from starlette_admin.widgets import (
    BaseWidget,
    Breakpoints,
    CardRowWidget,
    ChartWidget,
    Col,
    ColumnWidget,
    DividerWidget,
    FieldRef,
    FieldsetWidget,
    GridWidget,
    HtmlWidget,
    PanelWidget,
    RowWidget,
    StatWidget,
    TableWidget,
    TabsWidget,
    TextWidget,
    normalize_widget,
    render_widget,
)


@pytest.fixture
def widget_env() -> Environment:
    env = Environment(
        loader=PackageLoader("starlette_admin", "templates"),
        extensions=["jinja2.ext.i18n"],
        autoescape=True,
    )
    env.install_gettext_callables(lambda x: x, lambda s, p, n: s if n == 1 else p)
    env.globals["icon"] = lambda name: CoreIcons.icons.get(name, name)
    return env


def _make_url_for():
    """Return a side_effect for url_for that yields URL-like objects supporting include_query_params."""

    def _url_for(_route_name, *, path):
        url_obj = MagicMock()
        url_str = f"http://testserver/admin/static/{path}"
        url_obj.__str__ = lambda _self: url_str
        url_obj.include_query_params.return_value = url_obj
        return url_obj

    return _url_for


# ── BaseWidget ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_base_widget_get_context_returns_empty_dict():
    class ConcreteWidget(BaseWidget):
        template = "widgets/dummy.html"

    widget = ConcreteWidget()
    ctx = await widget.get_context(MagicMock())
    assert ctx == {}


# ── TableWidget ───────────────────────────────────────────────────────────────


def test_table_widget_default_limit():
    rows_callback = AsyncMock(return_value=[])
    widget = TableWidget(title="Test", columns=["Name"], rows_callback=rows_callback)
    assert widget.title == "Test"
    assert widget.columns == ["Name"]


def test_table_widget_template():
    assert TableWidget.template == "widgets/table_widget.html"


@pytest.mark.asyncio
async def test_table_widget_get_context_empty_rows():
    rows_callback = AsyncMock(return_value=[])
    widget = TableWidget(title="Empty", columns=["A", "B"], rows_callback=rows_callback)
    ctx = await widget.get_context(MagicMock())

    assert ctx["title"] == "Empty"
    assert ctx["columns"] == ["A", "B"]
    assert ctx["rows"] == []
    assert ctx["widget"] is widget


@pytest.mark.asyncio
async def test_table_widget_get_context_builds_rows():
    """rows_callback result is returned verbatim as rows."""
    rows = [["Alice", 30], ["Bob", 25]]
    rows_callback = AsyncMock(return_value=rows)
    widget = TableWidget(
        title="People", columns=["Name", "Age"], rows_callback=rows_callback
    )
    ctx = await widget.get_context(MagicMock())

    assert ctx["title"] == "People"
    assert ctx["columns"] == ["Name", "Age"]
    assert len(ctx["rows"]) == 2
    assert ctx["rows"][0] == ["Alice", 30]
    assert ctx["rows"][1] == ["Bob", 25]


@pytest.mark.asyncio
async def test_table_widget_passes_limit_to_find_all():
    """rows_callback is called with the request object."""
    request = MagicMock()
    rows_callback = AsyncMock(return_value=[])
    widget = TableWidget(title="T", columns=[], rows_callback=rows_callback)
    await widget.get_context(request)

    rows_callback.assert_called_once_with(request)


# ── StatWidget ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stat_widget_get_context():
    async def _value(request):
        return 42

    widget = StatWidget(
        title="Sales",
        value_callback=_value,
        description="2% increase",
        description_icon="fa-solid fa-arrow-trend-up",
        color="success",
        description_icon_position="before",
    )
    ctx = await widget.get_context(MagicMock())

    assert ctx["title"] == "Sales"
    assert ctx["value"] == 42
    assert ctx["description"] == "2% increase"
    assert ctx["description_icon"] == "fa-solid fa-arrow-trend-up"
    assert ctx["color"] == "success"
    assert ctx["description_icon_position"] == "before"
    assert ctx["chart_data"] is None
    assert ctx["chart_id"] == ""


@pytest.mark.asyncio
async def test_stat_widget_get_context_with_chart():
    async def _value(request):
        return 100

    async def _chart(request):
        return {"labels": ["Mon", "Tue"], "datasets": [{"data": [10, 20]}]}

    widget = StatWidget(
        title="Visits",
        value_callback=_value,
        chart_callback=_chart,
        chart_type="line",
        chart_height="50px",
    )
    ctx = await widget.get_context(MagicMock())

    assert ctx["chart_data"] == {
        "labels": ["Mon", "Tue"],
        "datasets": [{"data": [10, 20]}],
    }
    assert ctx["chart_id"].startswith("stat-chart-")
    assert ctx["chart_type"] == "line"
    assert ctx["chart_height"] == "50px"


@pytest.mark.asyncio
async def test_stat_widget_link_makes_card_anchor(widget_env):
    async def _value(request):
        return 5

    widget = StatWidget(title="Orders", value_callback=_value, link="/orders")
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert 'href="/orders"' in html
    assert "<a " in html


@pytest.mark.asyncio
async def test_stat_widget_no_js_without_chart():
    async def _value(request):
        return 0

    widget = StatWidget(title="T", value_callback=_value)
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()
    links = widget.additional_js_links(request)
    assert len(links) == 1
    assert any("stat_widget.js" in link for link in links)
    assert widget.additional_css_links(MagicMock(spec=Request)) == []


@pytest.mark.asyncio
async def test_stat_widget_js_links_with_chart():
    async def _value(request):
        return 0

    async def _chart(request):
        return [{"name": "Views", "data": [1, 2, 3]}]

    widget = StatWidget(title="T", value_callback=_value, chart_callback=_chart)
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()

    links = widget.additional_js_links(request)

    assert len(links) == 2
    assert any("apexcharts" in link for link in links)
    assert any("stat_widget.js" in link for link in links)
    request.url_for.assert_any_call("admin:static", path="js/vendor/apexcharts.min.js")
    request.url_for.assert_any_call("admin:static", path="js/stat_widget.js")


@pytest.mark.asyncio
async def test_stat_widget_render(widget_env):
    async def _value(request):
        return 123

    widget = StatWidget(
        title="Orders",
        value_callback=_value,
        description="Up from last week",
        description_icon="fa-solid fa-arrow-trend-up",
        color="success",
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "Orders" in html
    assert "123" in html
    assert "Up from last week" in html
    assert "fa-solid fa-arrow-trend-up" in html
    assert "text-success" in html


# ── ChartWidget ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chart_widget_get_context():
    async def _series(request):
        return [{"name": "Revenue", "data": [10, 20, 30]}]

    widget = ChartWidget(
        title="Revenue", chart_type="line", series_callback=_series, height=250
    )
    ctx = await widget.get_context(MagicMock())

    assert ctx["title"] == "Revenue"
    assert ctx["chart_type"] == "line"
    assert ctx["series"] == [{"name": "Revenue", "data": [10, 20, 30]}]
    assert ctx["height"] == 250
    assert ctx["options"] == {}
    assert ctx["chart_id"].startswith("chart-")


@pytest.mark.asyncio
async def test_chart_widget_render(widget_env):
    async def _series(request):
        return [{"name": "Sales", "data": [1, 2, 3]}]

    widget = ChartWidget(title="Chart", chart_type="bar", series_callback=_series)
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "Chart" in html
    assert "apex-chart" in html
    assert "bar" in html


@pytest.mark.asyncio
async def test_chart_widget_js_links():
    async def _series(request):
        return []

    widget = ChartWidget(title="T", chart_type="line", series_callback=_series)
    mock_request = MagicMock()
    mock_request.app.state.ROUTE_NAME = "admin"
    mock_request.url_for.side_effect = _make_url_for()

    links = widget.additional_js_links(mock_request)

    assert any("apexcharts" in link for link in links)
    assert any("chart_widget.js" in link for link in links)


# ── TextWidget ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_text_widget_plain_rendering(widget_env):
    widget = TextWidget(content="Hello\nWorld", markdown=False)
    ctx = await widget.get_context(MagicMock())

    assert ctx["content"] == "Hello\nWorld"
    assert ctx["markdown"] is False


@pytest.mark.asyncio
async def test_text_widget_markdown_rendering(widget_env):
    widget = TextWidget(content="# Hello", markdown=True)
    ctx = await widget.get_context(MagicMock())

    if TextWidget.__module__ == "starlette_admin.widgets":
        assert "<h1>Hello</h1>" in ctx["content"]


@pytest.mark.asyncio
async def test_text_widget_markdown_default_is_false(widget_env):
    widget = TextWidget(content="# Hello")
    assert widget.markdown is False
    ctx = await widget.get_context(MagicMock())
    assert ctx["content"] == "# Hello"


# ── HtmlWidget ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_html_widget_render(widget_env):
    widget = HtmlWidget(html="<p>Raw HTML</p>")
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "<p>Raw HTML</p>" in html


# ── DividerWidget ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_divider_widget_render(widget_env):
    widget = DividerWidget()
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "<hr" in html


# ── FieldRef ─────────────────────────────────────────────────────────────────


def test_form_field_prepend_append_default_to_none():
    widget = FieldRef("email")
    assert widget.prepend is None
    assert widget.append is None
    assert widget.flat is False


@pytest.mark.asyncio
async def test_form_field_get_context_wraps_prepend_append_in_markup():
    widget = FieldRef("phone", prepend="@", append='<i class="fa fa-phone"></i>')
    ctx = await widget.get_context(MagicMock())
    assert isinstance(ctx["input_group_prepend"], Markup)
    assert ctx["input_group_prepend"] == Markup("@")
    assert isinstance(ctx["input_group_append"], Markup)
    assert ctx["input_group_append"] == Markup('<i class="fa fa-phone"></i>')


@pytest.mark.asyncio
async def test_form_field_get_context_without_prepend_append_is_none():
    widget = FieldRef("email")
    ctx = await widget.get_context(MagicMock())
    assert ctx["input_group_prepend"] is None
    assert ctx["input_group_append"] is None
    assert ctx["input_group_flat"] is False


@pytest.mark.asyncio
async def test_form_field_get_context_passes_flat():
    widget = FieldRef("phone", prepend="@", flat=True)
    ctx = await widget.get_context(MagicMock())
    assert ctx["input_group_flat"] is True


# ── Layout widgets ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_row_widget_renders_children(widget_env):
    async def _value(request):
        return 7

    widget = RowWidget(
        children=[
            Col(StatWidget(title="A", value_callback=_value), Breakpoints(default=4)),
            Col(StatWidget(title="B", value_callback=_value), Breakpoints(default=8)),
        ],
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "A" in html
    assert "B" in html
    assert 'class="row"' in html
    assert "row-deck row-cards" not in html
    assert 'class="col-4"' in html
    assert 'class="col-8"' in html


@pytest.mark.asyncio
async def test_card_row_widget_adds_row_deck_row_cards_classes(widget_env):
    async def _value(request):
        return 7

    widget = CardRowWidget(
        children=[
            Col(StatWidget(title="A", value_callback=_value), Breakpoints(default=4)),
            Col(StatWidget(title="B", value_callback=_value), Breakpoints(default=8)),
        ],
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "A" in html
    assert "B" in html
    assert 'class="row row-deck row-cards"' in html
    assert 'class="col-4"' in html
    assert 'class="col-8"' in html


@pytest.mark.asyncio
async def test_column_widget_renders_children(widget_env):
    async def _value(request):
        return 1

    widget = ColumnWidget(
        children=[
            StatWidget(title="Top", value_callback=_value),
            StatWidget(title="Bottom", value_callback=_value),
        ]
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "Top" in html
    assert "Bottom" in html
    assert 'class="d-flex flex-column gap-3"' in html


@pytest.mark.asyncio
async def test_grid_widget_renders_children(widget_env):
    async def _value(request):
        return 1

    widget = GridWidget(
        children=[StatWidget(title="One", value_callback=_value)],
        breakpoints=Breakpoints(default=3),
        gutter=2,
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "One" in html
    assert "row-cols-3" in html
    assert "g-2" in html


@pytest.mark.asyncio
async def test_panel_widget_renders_children(widget_env):
    async def _value(request):
        return 1

    widget = PanelWidget(
        title="Summary",
        children=[StatWidget(title="Count", value_callback=_value)],
        collapsible=True,
        collapsed=True,
        icon="fa fa-list",
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "Summary" in html
    assert "Count" in html
    assert "fa-list" in html
    assert 'data-bs-toggle="collapse"' in html
    assert "collapse" in html


@pytest.mark.asyncio
async def test_fieldset_widget_renders_children(widget_env):
    async def _value(request):
        return 1

    widget = FieldsetWidget(
        legend="Summary",
        children=[StatWidget(title="Count", value_callback=_value)],
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "<fieldset" in html
    assert "<legend" in html
    assert "Summary" in html
    assert "Count" in html
    assert "disabled" not in html


@pytest.mark.asyncio
async def test_fieldset_widget_disabled(widget_env):
    widget = FieldsetWidget(legend="Locked", children=[], disabled=True)
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert '<fieldset class="form-fieldset" disabled>' in html


@pytest.mark.asyncio
async def test_tabs_widget_renders_panes(widget_env):
    async def _value(request):
        return 1

    widget = TabsWidget(
        tabs=[
            ("First", StatWidget(title="One", value_callback=_value)),
            ("Second", StatWidget(title="Two", value_callback=_value)),
        ]
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "First" in html
    assert "Second" in html
    assert "One" in html
    assert "Two" in html
    assert "nav-tabs" in html
    assert "tab-content" in html


# ── Grouping widget link collection ──────────────────────────────────────────


def _stat_with_chart(title: str) -> StatWidget:
    async def _value(request):
        return 0

    async def _chart(request):
        return [{"name": "x", "data": [1]}]

    return StatWidget(title=title, value_callback=_value, chart_callback=_chart)


def _mock_request_for_links() -> MagicMock:
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()
    return request


def test_row_widget_collects_js_links_from_children():
    child = _stat_with_chart("A")
    widget = RowWidget(children=[child])
    request = _mock_request_for_links()
    links = widget.additional_js_links(request)
    assert any("apexcharts" in link for link in links)
    assert any("stat_widget.js" in link for link in links)


def test_row_widget_deduplicates_links_across_children():
    child1 = _stat_with_chart("A")
    child2 = _stat_with_chart("B")
    widget = RowWidget(children=[child1, child2])
    request = _mock_request_for_links()
    links = widget.additional_js_links(request)
    assert len([lnk for lnk in links if "apexcharts" in lnk]) == 1


def test_column_widget_collects_js_links_from_children():
    widget = ColumnWidget(children=[_stat_with_chart("A")])
    links = widget.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_grid_widget_collects_js_links_from_children():
    widget = GridWidget(children=[_stat_with_chart("A")])
    links = widget.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_panel_widget_collects_js_links_from_children():
    widget = PanelWidget(title="P", children=[_stat_with_chart("A")])
    links = widget.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_tabs_widget_collects_js_links_from_tabs():
    widget = TabsWidget(tabs=[("Tab1", _stat_with_chart("A"))])
    links = widget.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_fieldset_widget_collects_js_links_from_children():
    widget = FieldsetWidget(legend="F", children=[_stat_with_chart("A")])
    links = widget.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_fieldset_widget_collects_css_links_from_children():
    widget = FieldsetWidget(legend="F", children=[_stat_with_chart("A")])
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()
    links = widget.additional_css_links(request)
    assert isinstance(links, list)


def test_grouping_widget_collects_links_from_nested_grouping():
    inner = RowWidget(children=[_stat_with_chart("A")])
    outer = ColumnWidget(children=[inner])
    links = outer.additional_js_links(_mock_request_for_links())
    assert any("apexcharts" in link for link in links)


def test_grouping_widget_returns_empty_when_no_child_links():
    async def _value(request):
        return 0

    child = StatWidget(title="X", value_callback=_value)
    widget = RowWidget(children=[child])
    request = _mock_request_for_links()
    links = widget.additional_js_links(request)
    assert len(links) == 1
    assert any("stat_widget.js" in link for link in links)
    assert widget.additional_css_links(_mock_request_for_links()) == []


# ── render_widget helper ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_render_widget_helper(widget_env):
    async def _value(request):
        return 99

    widget = StatWidget(title="Total", value_callback=_value)
    request = MagicMock(spec=Request)
    html = await render_widget(widget, request, widget_env)

    assert "Total" in html
    assert "99" in html


# ── BaseWidget.additional_js_links default ───────────────────────────────────


def test_base_widget_additional_js_links_returns_empty():
    widget = TextWidget(content="hello")
    assert widget.additional_js_links(MagicMock()) == []


# ── StatWidget countup JS link ────────────────────────────────────────────────


def test_stat_widget_js_links_with_countup():
    async def _value(request):
        return 0

    widget = StatWidget(title="T", value_callback=_value, countup=True)
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()

    links = widget.additional_js_links(request)

    assert any("countUp" in link for link in links)
    request.url_for.assert_any_call("admin:static", path="js/vendor/countUp.umd.js")


# ── _col_class breakpoint branches ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_row_widget_renders_bare_child_as_col(widget_env):
    """A RowWidget child passed without Col wrapper defaults to class="col"."""

    async def _value(request):
        return 5

    widget = RowWidget(children=[StatWidget(title="Bare", value_callback=_value)])
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "Bare" in html
    assert 'class="col"' in html


@pytest.mark.asyncio
async def test_row_widget_renders_all_col_breakpoints(widget_env):
    async def _value(request):
        return 1

    widget = RowWidget(
        children=[
            Col(
                StatWidget(title="X", value_callback=_value),
                Breakpoints(sm=6, md=4, lg=3, xl=2, xxl=1),
            ),
        ],
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "col-sm-6" in html
    assert "col-md-4" in html
    assert "col-lg-3" in html
    assert "col-xl-2" in html
    assert "col-xxl-1" in html


# ── _row_col_class breakpoint branches ────────────────────────────────────────


@pytest.mark.asyncio
async def test_grid_widget_renders_all_row_col_breakpoints(widget_env):
    async def _value(request):
        return 1

    widget = GridWidget(
        children=[StatWidget(title="Y", value_callback=_value)],
        breakpoints=Breakpoints(sm=2, md=3, lg=4, xl=5, xxl=6),
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "row-cols-sm-2" in html
    assert "row-cols-md-3" in html
    assert "row-cols-lg-4" in html
    assert "row-cols-xl-5" in html
    assert "row-cols-xxl-6" in html


# ── additional_css_links for layout widgets ───────────────────────────────────


def test_column_widget_additional_css_links_returns_list():
    async def _value(request):
        return 0

    widget = ColumnWidget(children=[StatWidget(title="A", value_callback=_value)])
    result = widget.additional_css_links(MagicMock())
    assert isinstance(result, list)


def test_grid_widget_additional_css_links_returns_list():
    async def _value(request):
        return 0

    widget = GridWidget(children=[StatWidget(title="A", value_callback=_value)])
    result = widget.additional_css_links(MagicMock())
    assert isinstance(result, list)


def test_panel_widget_additional_css_links_includes_panel_css():
    async def _value(request):
        return 0

    widget = PanelWidget(
        title="P", children=[StatWidget(title="A", value_callback=_value)]
    )
    request = MagicMock()
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.side_effect = _make_url_for()

    links = widget.additional_css_links(request)

    assert any("panel_widget.css" in link for link in links)


def test_tabs_widget_additional_css_links_returns_list():
    async def _value(_request):
        return 0

    widget = TabsWidget(tabs=[("Tab", StatWidget(title="A", value_callback=_value))])
    result = widget.additional_css_links(MagicMock())
    assert isinstance(result, list)


# ── normalize_widget: shorthand lives on the widget, not on form_layout ───────
#
# These tests build widgets directly, with no BaseModelView/form_layout in
# sight, to prove the str/tuple/list shorthand is expanded by each widget's
# own __post_init__ rather than by a form_layout-specific preprocessing pass.


def test_normalize_widget_str_becomes_field_ref():
    node = normalize_widget("email")
    assert isinstance(node, FieldRef)
    assert node.name == "email"


def test_normalize_widget_tuple_becomes_row_with_auto_md_and_col_12():
    a, b = StatWidget(title="A", value_callback=AsyncMock()), TextWidget(content="B")
    node = normalize_widget((a, b))

    assert isinstance(node, RowWidget)
    assert [col.widget for col in node.children] == [a, b]
    for col in node.children:
        assert col.breakpoints == Breakpoints(default=12, md="auto")


def test_normalize_widget_list_becomes_column():
    a, b = StatWidget(title="A", value_callback=AsyncMock()), TextWidget(content="B")
    node = normalize_widget([a, b])

    assert isinstance(node, ColumnWidget)
    assert node.children == [a, b]


def test_normalize_widget_passes_through_existing_widget():
    widget = TextWidget(content="already built")
    assert normalize_widget(widget) is widget


def test_panel_widget_expands_tuple_shorthand_without_form_layout():
    """PanelWidget normalizes shorthand children on its own; no form_layout
    or BaseModelView is involved anywhere in this test.
    """
    widget = PanelWidget(
        title="P",
        children=[
            TextWidget(content="solo"),
            (TextWidget(content="left"), TextWidget(content="right")),
        ],
    )

    solo, row = widget.children
    assert isinstance(solo, TextWidget)
    assert isinstance(row, RowWidget)
    assert row.children[0].breakpoints == Breakpoints(default=12, md="auto")
    assert row.children[1].breakpoints == Breakpoints(default=12, md="auto")


@pytest.mark.asyncio
async def test_column_widget_expands_list_and_tuple_shorthand_when_rendered(widget_env):
    """A bare list nested inside a ColumnWidget's children stacks its own
    items vertically (normalized to a nested ColumnWidget), and a bare tuple
    renders its items side by side, matching form_layout's shorthand exactly
    but with no form_layout involved.
    """
    widget = ColumnWidget(
        children=[
            [TextWidget(content="stacked-one"), TextWidget(content="stacked-two")],
            (TextWidget(content="left"), TextWidget(content="right")),
        ]
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "stacked-one" in html
    assert "stacked-two" in html
    assert "left" in html
    assert "right" in html
    assert 'class="col-12 col-md"' in html


@pytest.mark.asyncio
async def test_tabs_widget_expands_list_shorthand_tab_without_form_layout(widget_env):
    widget = TabsWidget(
        tabs=[("Details", [TextWidget(content="first"), TextWidget(content="second")])]
    )
    request = MagicMock(spec=Request)
    html = await widget.render(request, widget_env)

    assert "first" in html
    assert "second" in html
