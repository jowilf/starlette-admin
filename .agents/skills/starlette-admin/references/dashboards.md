# Custom views, dashboards, and widgets

`CustomView` creates a standalone sidebar page. Instantiate it directly for widget-based pages; subclass only for custom routes, templates, or access control.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

`widget` accepts a `BaseWidget` instance or a callable `(request) -> BaseWidget | None`; use the callable form when content depends on live data, the user, or feature flags.

## Content widgets

All `*_callback` parameters take async callables receiving the current `Request`.

- `StatWidget(title=, value_callback=, description=, color=, link=, chart_callback=, countup=)`: KPI card. `color` takes Tabler tokens (`"success"`, `"danger"`); `chart_callback` returns an ApexCharts series list for a sparkline.
- `ChartWidget(title=, chart_type=, series_callback=, height=, options=)`: ApexCharts chart. `chart_type` is any ApexCharts string (`"line"`, `"bar"`, `"pie"`, `"donut"`, `"heatmap"`, ...). `series_callback` returns `[{"name": ..., "data": [...]}]`, or a flat number list for pie/donut/radialBar. `options` merges over the default config (use it for `xaxis.categories` or `labels`).
- `TableWidget(title=, columns=, rows_callback=)`: compact read-only table; `rows_callback` returns a list of row lists.
- `TextWidget(content=, markdown=, card=)`: plain text or Markdown (`markdown=True` requires the `markdown` package).
- `HtmlWidget(html=)`: raw HTML, rendered UNESCAPED. Never pass user-supplied content.
- `DividerWidget()`: horizontal rule.

## Layout widgets

- `ColumnWidget(children=)`: vertical stack, typical root container.
- `RowWidget(children=)`: flexbox row. Wrap children in `Col(widget, breakpoints=Breakpoints(default=12, md=6))` for responsive 1-12 spans; unwrapped children split evenly.
- `CardRowWidget(children=)`: like `RowWidget` but equal-height cards; use for KPI/chart rows.
- `GridWidget(children=, breakpoints=, gutter=)`: `Breakpoints` here means items per row, not span.
- `PanelWidget(title=, icon=, children=, collapsible=, collapsed=)` and `TabsWidget(tabs=[(label, widget), ...])`.

These same widgets power `ModelView.form_layout` (see [views.md](views.md)). Container widgets expand the tuple/list shorthand everywhere.

## Home dashboard

The admin root renders a `DefaultIndexView` (record counts per model) unless you pass `index_view`:

```python
async def build_dashboard(request: Request) -> ColumnWidget:
    return ColumnWidget(children=[kpi_row, revenue_chart, latest_orders])


admin = Admin(
    engine,
    title="My Admin",
    secret_key="change-me",
    index_view=CustomView(menu_label="Dashboard", icon="fa fa-home", widget=build_dashboard),
)
```

The builder runs on every request, so the layout can adapt per user.

## Custom templates and routes

Subclass `CustomView` and re-decorate `index` with `@route("")` to render your own Jinja template; add more endpoints with `@route`:

```python
from starlette.responses import JSONResponse
from starlette_admin import CustomView, route


class ReportsView(CustomView):
    menu_label = "Reports"
    icon = "fa fa-file-lines"
    path = "/reports"

    @route("")
    async def index(self, request):
        return self.templates.TemplateResponse(
            request=request, name="reports/index.html",
            context={"title": self.title(request)},
        )

    @route("/data", methods=["GET"])
    async def report_list(self, request):
        return JSONResponse([{"id": "001", "status": "ready"}])

    @route("/generate", methods=["POST"])
    async def generate(self, request):
        form = await request.form()
        return JSONResponse({"status": "queued"})


admin.add_view(ReportsView())
```

- Route paths append to the view's `path` (`/admin/reports/data` above).
- Mutating routes go through CSRF middleware: custom form templates must include `{{ csrf_input(request) }}`.
- `self.templates` resolves against `Admin(templates_dir=...)`, falling back to the built-ins; it is only available after mounting, so never touch it in `__init__`. Templates typically start with `{% extends "layout.html" %}` and fill `{% block content %}`.
- To render widgets inside a custom template, resolve with `await self._resolve_widget(request)`, render with `starlette_admin.widgets.render_widget(widget, request, self.templates.env)`, and include the widget's `additional_css_links`/`additional_js_links` in the head/script blocks, otherwise charts fail to load their assets.
- Constructor arguments fall back to class attributes, so `ReportsView()` needs no arguments.

## Access control

Override `is_accessible(request)`: returning `False` removes the sidebar entry and makes every `@route` return 403. For granular rules (public GET, admin-only POST), check inside the specific handler instead.

Runnable example: `examples/07-dashboard` uses every widget above.
