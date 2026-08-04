from __future__ import annotations

import uuid
from abc import ABC
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias, cast

from jinja2 import Environment
from markupsafe import Markup
from starlette.requests import Request
from starlette_admin.helpers import static_url

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField

try:
    import markdown as _markdown
except ImportError:  # pragma: no cover
    _markdown = None  # ty: ignore[invalid-assignment]


@dataclass
class BaseWidget(ABC):
    """Base class for all dashboard widgets.

    Subclasses set `template` to a path under the theme's `widgets/` directory
    and override `get_context` to supply template variables. Layout widgets
    should also override `render` to recursively render their children before
    rendering their own template.
    """

    template: ClassVar[str]

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {}

    def additional_css_links(self, request: Request) -> list[str]:
        """CSS URLs to inject into the page <head> when this widget is rendered."""
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        """JS URLs to inject into the page before </body> when this widget is rendered."""
        return []

    async def render(self, request: Request, env: Environment) -> Markup:
        """Render the widget to HTML using `env`."""
        ctx = await self.get_context(request)
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class StatWidget(BaseWidget):
    """Renders a KPI stat card.

    Args:
        title: Label shown as the card subheader.
        value_callback: Async callable returning the primary metric value.
        link: Optional URL; makes the entire card a clickable anchor.
        description: Secondary text shown below the value.
        description_icon: Icon class for the description badge
            (e.g. ``"fa-solid fa-arrow-trend-up"``).
        color: Tabler color token applied to the description area
            (e.g. ``"success"``, ``"danger"``).
        description_icon_position: ``"before"`` or ``"after"`` the description text.
        chart_callback: Optional async callable returning an ApexCharts ``series``
            list (e.g. ``[{"name": "Views", "data": [10, 20, 30]}]``).
            When provided, a sparkline is rendered at the bottom of the card.
        chart_type: ApexCharts chart type for the sparkline (default ``"line"``).
        chart_height: Height passed to ApexCharts (default ``"40px"``).
        chart_options: Extra ApexCharts options merged over the sparkline defaults.
        countup: When ``True``, adds ``data-countup`` to the value element so a
            countup.js animation can target it.
    """

    template: ClassVar[str] = "widgets/stat_widget.html"

    title: str
    value_callback: Callable[[Request], Awaitable[int | float | str]]
    link: str | None = None
    description: str = ""
    description_icon: str = ""
    color: str = ""
    description_icon_position: Literal["before", "after"] = "after"
    chart_callback: Callable[[Request], Awaitable[dict[str, Any]]] | None = None
    chart_type: str = "line"
    chart_height: str = "40px"
    chart_options: dict[str, Any] = field(default_factory=dict)
    countup: bool = False

    def additional_js_links(self, request: Request) -> list[str]:
        links = []
        if self.countup:
            links.append(static_url(request, "js/vendor/countUp.umd.js", v="2.10.0"))
        if self.chart_callback is not None:
            links.append(
                static_url(request, "js/vendor/apexcharts.min.js", v="v5.15.2")
            )
        links.append(static_url(request, "js/stat_widget.js", v=1))
        return links

    async def get_context(self, request: Request) -> dict[str, Any]:
        value = await self.value_callback(request)
        chart_data = await self.chart_callback(request) if self.chart_callback else None
        chart_id = (
            f"stat-chart-{uuid.uuid4().hex[:8]}" if chart_data is not None else ""
        )
        value_id = f"stat-value-{uuid.uuid4().hex[:8]}" if self.countup else ""
        return {
            "widget": self,
            "title": self.title,
            "value": value,
            "link": self.link,
            "description": self.description,
            "description_icon": self.description_icon,
            "color": self.color,
            "description_icon_position": self.description_icon_position,
            "chart_data": chart_data,
            "chart_id": chart_id,
            "chart_type": self.chart_type,
            "chart_height": self.chart_height,
            "chart_options": self.chart_options,
            "countup": self.countup,
            "value_id": value_id,
        }


@dataclass
class ChartWidget(BaseWidget):
    """Renders an ApexCharts chart inside a Tabler card.

    Args:
        title: Card heading.
        chart_type: ApexCharts chart type, e.g. ``"line"``, ``"area"``,
            ``"bar"``, ``"pie"``, ``"donut"``, ``"radar"``, ``"scatter"``,
            ``"heatmap"``, ``"radialBar"``, ``"treemap"``.
        series_callback: Async callable returning the ApexCharts ``series``
            value.  For most types this is a list of
            ``{"name": …, "data": […]}`` dicts; for pie/donut/radialBar it is
            a flat list of numbers.
        height: Chart height in pixels (default ``300``).
        options: Extra ApexCharts config merged over the ``chart.type`` /
            ``chart.height`` defaults.  Use this for per-type options such as
            ``labels`` (pie/donut), ``xaxis.categories`` (bar/radar), or
            ``plotOptions``.
    """

    template: ClassVar[str] = "widgets/chart_widget.html"

    title: str
    chart_type: str
    series_callback: Callable[[Request], Awaitable[Any]]
    height: int = 300
    options: dict[str, Any] = field(default_factory=dict)

    def additional_js_links(self, request: Request) -> list[str]:
        return [
            static_url(request, "js/vendor/apexcharts.min.js", v="v5.15.2"),
            static_url(request, "js/chart_widget.js", v=1),
        ]

    async def get_context(self, request: Request) -> dict[str, Any]:
        series = await self.series_callback(request)
        chart_id = f"chart-{uuid.uuid4().hex[:8]}"
        return {
            "widget": self,
            "title": self.title,
            "chart_id": chart_id,
            "chart_type": self.chart_type,
            "series": series,
            "height": self.height,
            "options": self.options,
        }


@dataclass
class TableWidget(BaseWidget):
    """Renders a compact summary table from a data callback.

    Args:
        title: Card heading displayed above the table.
        columns: List of column header labels.
        rows_callback: Async callable returning rows as a list of lists.
    """

    template: ClassVar[str] = "widgets/table_widget.html"

    title: str
    columns: list[str]
    rows_callback: Callable[[Request], Awaitable[list[list[Any]]]]

    async def get_context(self, request: Request) -> dict[str, Any]:
        rows = await self.rows_callback(request)
        return {
            "widget": self,
            "title": self.title,
            "columns": self.columns,
            "rows": rows,
        }


@dataclass
class TextWidget(BaseWidget):
    """Renders a block of text, optionally as Markdown.

    Args:
        content: Static markdown or plain text.
        markdown: Whether to render `content` as Markdown. If the `markdown`
            package is not installed, plain-text rendering is used as a fallback.
    """

    template: ClassVar[str] = "widgets/text_widget.html"

    content: str
    markdown: bool = False
    card: bool = False

    async def get_context(self, request: Request) -> dict[str, Any]:
        rendered: str | Markup
        if self.markdown:
            if _markdown is None:  # pragma: no cover
                raise ImportError(
                    "The 'markdown' package is required when TextWidget.markdown=True. "
                    "Install it with: pip install markdown"
                )
            rendered = Markup(_markdown.markdown(self.content))
        else:
            rendered = self.content
        return {
            "widget": self,
            "content": rendered,
            "markdown": self.markdown,
            "card": self.card,
        }


@dataclass
class HtmlWidget(BaseWidget):
    """Renders an arbitrary block of pre-rendered HTML.

    Args:
        html: Raw HTML string. It is marked safe and rendered without escaping.
    """

    template: ClassVar[str] = "widgets/html_widget.html"

    html: str

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "widget": self,
            "html": Markup(self.html),
        }


@dataclass
class DividerWidget(BaseWidget):
    """A horizontal rule / visual separator between other widgets."""

    template: ClassVar[str] = "widgets/divider_widget.html"

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {"widget": self}


@dataclass
class Breakpoints:
    """Bootstrap breakpoint column sizes for ``Col`` and ``GridWidget``.

    Each field maps to a Bootstrap responsive infix. ``None`` (the default)
    means the breakpoint is omitted from the generated class string.

    For ``Col``, the values are Bootstrap column spans (1-12), or the literal
    ``"auto"`` for an equal-width flexible column (``"col-md"`` rather than
    ``"col-md-6"``):
      ``Breakpoints(default=12, md=6)`` -> ``"col-12 col-md-6"``
      ``Breakpoints(default=12, md="auto")`` -> ``"col-12 col-md"``

    For ``GridWidget``, the values are items-per-row counts (``"auto"`` does
    not apply there):
      ``Breakpoints(default=1, md=2, lg=3)`` -> ``"row-cols-1 row-cols-md-2 row-cols-lg-3"``
    """

    default: int | Literal["auto"] | None = None
    sm: int | Literal["auto"] | None = None
    md: int | Literal["auto"] | None = None
    lg: int | Literal["auto"] | None = None
    xl: int | Literal["auto"] | None = None
    xxl: int | Literal["auto"] | None = None


WidgetShorthand: TypeAlias = "BaseWidget | str | tuple[Any, ...] | list[Any]"
"""Anything a container widget's `children` (or `Col.widget`, or a
`TabsWidget` tab's widget) will accept in place of an already-built
`BaseWidget`. See `normalize_widget` for what each shorthand expands to.
"""


@dataclass
class Col:
    """Responsive column wrapper for children of ``RowWidget``.

    Wrap a child widget with ``Col`` to control its Bootstrap column span at
    each viewport size. Omitting ``breakpoints`` (or leaving all fields
    ``None``) yields an auto ``col`` class.

    ``widget`` accepts the same shorthand as any other widget slot (see
    `normalize_widget`), so ``Col("email", Breakpoints(md=6))`` is
    equivalent to ``Col(FieldRef("email"), Breakpoints(md=6))``.

    Example::

        Col(my_widget, breakpoints=Breakpoints(default=12, md=6))
        # -> class="col-12 col-md-6"
    """

    widget: BaseWidget
    breakpoints: Breakpoints = field(default_factory=Breakpoints)

    def __post_init__(self) -> None:
        self.widget = normalize_widget(self.widget)


def _col(infix: str, value: int | Literal["auto"]) -> str:
    base = f"col-{infix}" if infix else "col"
    return base if value == "auto" else f"{base}-{value}"


def _col_class(bp: Breakpoints) -> str:
    parts: list[str] = []
    if bp.default is not None:
        parts.append(_col("", bp.default))
    if bp.sm is not None:
        parts.append(_col("sm", bp.sm))
    if bp.md is not None:
        parts.append(_col("md", bp.md))
    if bp.lg is not None:
        parts.append(_col("lg", bp.lg))
    if bp.xl is not None:
        parts.append(_col("xl", bp.xl))
    if bp.xxl is not None:
        parts.append(_col("xxl", bp.xxl))
    return " ".join(parts) if parts else "col"


def _row_col_class(bp: Breakpoints) -> str:
    parts: list[str] = []
    if bp.default is not None:
        parts.append(f"row-cols-{bp.default}")
    if bp.sm is not None:
        parts.append(f"row-cols-sm-{bp.sm}")
    if bp.md is not None:
        parts.append(f"row-cols-md-{bp.md}")
    if bp.lg is not None:
        parts.append(f"row-cols-lg-{bp.lg}")
    if bp.xl is not None:
        parts.append(f"row-cols-xl-{bp.xl}")
    if bp.xxl is not None:
        parts.append(f"row-cols-xxl-{bp.xxl}")
    return " ".join(parts) if parts else "row-cols-1"


def normalize_widget(node: WidgetShorthand) -> BaseWidget:
    """Expand a shorthand `WidgetShorthand` into a real widget.

    A bare `str` becomes a `FieldRef` referencing the declared field of
    that name. A `tuple` becomes a `RowWidget` with each item in its own
    `Col`, full width below the `md` breakpoint and equal width at `md` and
    above (matching how a single item renders full width on its own); if
    every item resolves to a `StatWidget`, a `CardRowWidget` is used instead
    so the cards get the row-deck equal-height treatment. A `list` becomes a
    `ColumnWidget` stacking each item vertically. Anything else is assumed
    to already be a `BaseWidget` and is returned unchanged.

    Each item handed to the resulting `RowWidget`/`ColumnWidget` is itself
    shorthand-typed, so nesting (a tuple inside a list, a list inside a
    tuple, and so on) is expanded in turn by that container's own
    `__post_init__` when it is constructed below: no explicit recursion is
    needed here.
    """
    if isinstance(node, str):
        return FieldRef(node)
    if isinstance(node, tuple):
        # `Col`/`ColumnWidget` accept `WidgetShorthand` at construction and
        # normalize it in `__post_init__`, but their fields are declared as
        # the already-normalized `BaseWidget` for readers after that point.
        cols: list[BaseWidget | Col] = [
            Col(cast(BaseWidget, item), Breakpoints(default=12, md="auto"))
            for item in node
        ]
        row_cls = (
            CardRowWidget
            if cols
            and all(
                isinstance(col, Col) and isinstance(col.widget, StatWidget)
                for col in cols
            )
            else RowWidget
        )
        return row_cls(children=cols)
    if isinstance(node, list):
        return ColumnWidget(children=cast("list[BaseWidget]", node))
    return node


def _collect_child_links(
    children: Sequence[BaseWidget | Col], request: Request, method: str
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for child in children:
        widget = child.widget if isinstance(child, Col) else child
        for link in getattr(widget, method)(request):
            if link not in seen:
                seen.add(link)
                result.append(link)
    return result


@dataclass
class RowWidget(BaseWidget):
    """Arranges child widgets horizontally in a plain Bootstrap grid row.

    Use ``CardRowWidget`` instead when every child is itself a card (KPI
    stats, charts, tables) and should get Tabler's ``row-deck row-cards``
    equal-height-card treatment.

    Args:
        children: Widgets (or ``Col``-wrapped widgets) to render side-by-side.
            Wrap a child in ``Col`` to control its responsive column widths; unwrapped children get an auto ``col`` class.
            Also accepts `WidgetShorthand` (see `normalize_widget`) in place
            of a built widget, e.g. a bare field name.
    """

    template: ClassVar[str] = "widgets/row_widget.html"

    children: list[BaseWidget | Col] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.children = [
            child if isinstance(child, Col) else normalize_widget(child)
            for child in self.children
        ]

    def additional_css_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_css_links")

    def additional_js_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_js_links")

    async def render(self, request: Request, env: Environment) -> Markup:
        items: list[tuple[str, Markup]] = []
        for child in self.children:
            if isinstance(child, Col):
                widget, col_class = child.widget, _col_class(child.breakpoints)
            else:
                widget, col_class = child, "col"
            items.append((col_class, await widget.render(request, env)))
        template = env.get_template(self.template)
        return Markup(template.render({"items": items}, request=request))


@dataclass
class CardRowWidget(RowWidget):
    """A ``RowWidget`` for rows of cards: same layout mechanics, plus
    Tabler's ``row-deck row-cards`` classes so the cards in the row share a
    consistent, equal height. Used for dashboard rows of ``StatWidget``,
    ``ChartWidget``, ``TableWidget``, etc.
    """

    template: ClassVar[str] = "widgets/card_row_widget.html"


@dataclass
class ColumnWidget(BaseWidget):
    """Stacks child widgets vertically.

    Args:
        children: Widgets to stack. Also accepts `WidgetShorthand` (see
            `normalize_widget`) in place of a built widget, e.g. a bare
            field name or a tuple of names for a side-by-side row.
    """

    template: ClassVar[str] = "widgets/column_widget.html"

    children: list[BaseWidget] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.children = [normalize_widget(child) for child in self.children]

    def additional_css_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_css_links")

    def additional_js_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_js_links")

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "widget": self,
            "children": self.children,
        }

    async def render(self, request: Request, env: Environment) -> Markup:
        ctx = await self.get_context(request)
        ctx["children_html"] = [
            await child.render(request, env) for child in self.children
        ]
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class GridWidget(BaseWidget):
    """Arranges child widgets in a responsive Bootstrap grid.

    Uses Bootstrap's ``row-cols-*`` system: Tabler/Bootstrap handles all
    responsive behavior; no custom ``<style>`` or media queries are emitted.

    Args:
        children: Widgets to render in the grid. Also accepts
            `WidgetShorthand` (see `normalize_widget`) in place of a built
            widget.
        breakpoints: Items-per-row at each viewport size. ``default`` sets
            the base (smallest) column count; each named breakpoint overrides
            it upward. Example::

                Breakpoints(default=1, md=2, lg=3)
                # -> "row-cols-1 row-cols-md-2 row-cols-lg-3"

        gutter: Bootstrap gutter scale applied as ``g-{n}`` (values 0-5, default 3, approximately 1 rem).
    """

    template: ClassVar[str] = "widgets/grid_widget.html"

    children: list[BaseWidget] = field(default_factory=list)
    breakpoints: Breakpoints = field(default_factory=lambda: Breakpoints(default=1))
    gutter: int = 3

    def __post_init__(self) -> None:
        self.children = [normalize_widget(child) for child in self.children]

    def additional_css_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_css_links")

    def additional_js_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_js_links")

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "widget": self,
            "children": self.children,
            "row_col_class": _row_col_class(self.breakpoints),
            "gutter": self.gutter,
        }

    async def render(self, request: Request, env: Environment) -> Markup:
        ctx = await self.get_context(request)
        ctx["children_html"] = [
            await child.render(request, env) for child in self.children
        ]
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class PanelWidget(BaseWidget):
    """Wraps child widgets inside a titled card/panel.

    When used in a `form_layout` and resolved down to exactly one visible
    field, that field's label is hidden: the panel title already names it,
    so the label would be redundant. See
    [BaseModelView.resolve_form_layout][starlette_admin.views.BaseModelView.resolve_form_layout].

    Args:
        title: Panel heading.
        children: Widgets rendered inside the panel body. Also accepts
            `WidgetShorthand` (see `normalize_widget`) in place of a built
            widget, e.g. a bare field name or a tuple of names for a
            side-by-side row.
        collapsible: Whether the panel can be collapsed.
        collapsed: Initial collapsed state (only meaningful when collapsible).
        icon: Optional icon class for the panel header.
    """

    template: ClassVar[str] = "widgets/panel_widget.html"

    title: str
    children: list[BaseWidget] = field(default_factory=list)
    collapsible: bool = False
    collapsed: bool = False
    icon: str = ""

    def __post_init__(self) -> None:
        self.children = [normalize_widget(child) for child in self.children]

    def additional_css_links(self, request: Request) -> list[str]:
        own = [static_url(request, "css/panel_widget.css", v=1)]
        return own + _collect_child_links(
            self.children, request, "additional_css_links"
        )

    def additional_js_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_js_links")

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "widget": self,
            "widget_id": f"panel-{uuid.uuid4().hex[:8]}",
            "title": self.title,
            "children": self.children,
            "collapsible": self.collapsible,
            "collapsed": self.collapsed,
            # "icon" is reserved for the global icon(name) resolver, so this
            # widget's own icon is named "panel_icon" in the render context.
            "panel_icon": self.icon,
        }

    async def render(self, request: Request, env: Environment) -> Markup:
        ctx = await self.get_context(request)
        ctx["children_html"] = [
            await child.render(request, env) for child in self.children
        ]
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class FieldsetWidget(BaseWidget):
    """Wraps child widgets inside a native HTML ``<fieldset>``/``<legend>``.

    Use this instead of ``PanelWidget`` when you want the semantics and
    plain styling of a form fieldset rather than a card: no shadow, no
    header bar, just a bordered group with its ``legend`` as the caption.

    Args:
        legend: Text rendered in the ``<legend>`` element.
        children: Widgets rendered inside the fieldset. Also accepts
            `WidgetShorthand` (see `normalize_widget`) in place of a built
            widget, e.g. a bare field name or a tuple of names for a
            side-by-side row.
        disabled: Sets the HTML ``disabled`` attribute on the ``<fieldset>``,
            which disables every form control nested inside it.
    """

    template: ClassVar[str] = "widgets/fieldset_widget.html"

    legend: str
    children: list[BaseWidget] = field(default_factory=list)
    disabled: bool = False

    def __post_init__(self) -> None:
        self.children = [normalize_widget(child) for child in self.children]

    def additional_css_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_css_links")

    def additional_js_links(self, request: Request) -> list[str]:
        return _collect_child_links(self.children, request, "additional_js_links")

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "widget": self,
            "legend": self.legend,
            "children": self.children,
            "disabled": self.disabled,
        }

    async def render(self, request: Request, env: Environment) -> Markup:
        ctx = await self.get_context(request)
        ctx["children_html"] = [
            await child.render(request, env) for child in self.children
        ]
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class TabsWidget(BaseWidget):
    """Renders child widgets as Bootstrap tabs.

    Args:
        tabs: List of (tab_label, widget) tuples. A tab's `widget` accepts
            `WidgetShorthand` (see `normalize_widget`) in place of a built
            widget: a bare field name, a tuple of items for a side-by-side
            row, or a *list* of entries stacked vertically, normalized to a
            `ColumnWidget`. The list form lets a tab hold more than one row
            without an explicit `ColumnWidget` wrapper, e.g.
            `("Tab", ["aa", ("b", "c")])`.
        save_state: Remember the last active tab in the browser's
            `sessionStorage`, so it stays selected across page reloads
            within the same tab/session. The storage key is derived from the
            request path and each tab's label (a UUID5, so it's still
            uniquely identifying), not stored on the instance: a `TabsWidget`
            may be a persistent view attribute or, like in a dashboard
            `CustomView.widget` callable, rebuilt from scratch on every
            request, so nothing about the key can depend on Python object
            identity surviving between requests.
    """

    template: ClassVar[str] = "widgets/tabs_widget.html"

    tabs: list[tuple[str, BaseWidget]] = field(default_factory=list)
    save_state: bool = True

    def __post_init__(self) -> None:
        self.tabs = [(label, normalize_widget(widget)) for label, widget in self.tabs]

    def additional_css_links(self, request: Request) -> list[str]:
        return _collect_child_links(
            [w for _, w in self.tabs], request, "additional_css_links"
        )

    def additional_js_links(self, request: Request) -> list[str]:
        links = _collect_child_links(
            [w for _, w in self.tabs], request, "additional_js_links"
        )
        if self.save_state:
            links.append(static_url(request, "js/tabs_widget.js", v=1))
        return links

    def _storage_key(self, request: Request) -> str:
        seed = str(request.url.path) + "|" + "|".join(label for label, _ in self.tabs)
        return f"starlette-admin-tabs-{uuid.uuid5(uuid.NAMESPACE_URL, seed).hex}"

    async def get_context(self, request: Request) -> dict[str, Any]:
        tab_ids = [f"tab-{uuid.uuid4().hex[:8]}" for _ in self.tabs]
        return {
            "widget": self,
            "tabs": self.tabs,
            "tab_ids": tab_ids,
            "save_state": self.save_state,
            "storage_key": self._storage_key(request) if self.save_state else None,
        }

    async def render(self, request: Request, env: Environment) -> Markup:
        ctx = await self.get_context(request)
        ctx["tabs_html"] = [
            (label, await widget.render(request, env)) for label, widget in self.tabs
        ]
        template = env.get_template(self.template)
        return Markup(template.render(ctx, request=request))


@dataclass
class FieldRef(BaseWidget):
    """Leaf widget referencing a declared field by name, for use inside
    ``BaseModelView.form_layout``.

    ``FieldRef("email")`` placed anywhere in a `form_layout` tree — bare,
    or nested inside ``RowWidget``, ``PanelWidget``, ``TabsWidget``, etc. —
    means "render the declared ``email`` field here". It is not
    self-sufficient: the ``_field``/``_value``/``_error`` attributes are
    filled in by ``BaseModelView.resolve_form_layout`` from the current
    request's `obj`/`errors`/field permissions before rendering, so a bare
    ``FieldRef`` constructed and rendered outside that pipeline has nothing
    to show.

    Args:
        name: Name of the declared field to render.
        show_label: Whether to render the field's `<label>`. Set to `False`
            when the surrounding layout already conveys the field's purpose,
            so the label would be redundant.
        prepend: Bootstrap/Tabler input-group addon rendered before the
            input, e.g. ``"@"`` or ``'<i class="fa fa-phone"></i>'``. Plain
            text or raw HTML, rendered unescaped. Only honored by fields
            whose form template renders a native `<input>`. Other field types
            silently ignore it.
        append: Same as `prepend`, rendered after the input.
        flat: Render the input-group with Tabler's `input-group-flat` style.
            Only applies when `prepend` or `append` is set.
    """

    template: ClassVar[str] = "widgets/form_field_widget.html"

    name: str
    show_label: bool = True
    prepend: str | None = None
    append: str | None = None
    flat: bool = False
    _field: BaseField | None = field(default=None, repr=False)
    _value: Any = field(default=None, repr=False)
    _error: str | None = field(default=None, repr=False)

    async def get_context(self, request: Request) -> dict[str, Any]:
        return {
            "field": self._field,
            "value": self._value,
            "error": self._error,
            "show_label": self.show_label,
            "input_group_prepend": (
                Markup(self.prepend) if self.prepend is not None else None
            ),
            "input_group_append": (
                Markup(self.append) if self.append is not None else None
            ),
            "input_group_flat": self.flat,
        }


async def render_widget(
    widget: BaseWidget, request: Request, env: Environment
) -> Markup:
    """Render `widget` to HTML using `env`.

    This is a convenience helper for custom views that want to render widgets
    outside of the default ``CustomView.widget`` flow.
    """
    return await widget.render(request, env)
