---
title: Custom Views & Widgets
description: Build custom dashboard widgets, static pages, and standalone views inside your starlette-admin panel.
---

# Custom Views

Not every admin page maps to a database model. A `CustomView` creates a standalone page in the sidebar that you compose yourself from built-in widgets, custom templates, or custom routes.

In most cases, you don't need to subclass anything. Instantiate `CustomView`, pass it a widget, and register it:

```python
from starlette.requests import Request
from starlette_admin import CustomView, StatWidget
from starlette_admin.contrib.sqla import Admin


async def count_pending_jobs(request: Request) -> int:
    return 3


admin = Admin(engine, title="My Admin", secret_key="change-me")
admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(
            title="Pending background jobs", value_callback=count_pending_jobs
        ),
    )
)
```

* **`menu_label`**, **`icon`**, and **`path`**: Control the sidebar entry and the URL.
* **`widget`**: Determines what the page renders. Pass a single `BaseWidget` instance, or a callable (`(request) -> BaseWidget | None`) that builds the tree per request. Use the callable form when the page depends on live data, the current user, or feature flags.

To show more than one widget, pass a [layout widget](#layout-widgets) that contains children.

Subclass `CustomView` only when you need custom endpoints, access control, or full control over the HTTP response.

---

## Content widgets

Content widgets render the data itself. Their `*_callback` parameters accept async callables that receive the current `Request`, so every widget can fetch live data.

For the complete constructor signature of every widget below, see the [Widgets API reference](../api/widgets.md).

### StatWidget

A KPI card that shows a single metric, an optional description, and a sparkline.

```python
from starlette.requests import Request
from starlette_admin import StatWidget


async def count_orders(request: Request) -> int:
    session = request.state.session
    return await session.scalar(select(func.count(Order.id)))


orders_stat = StatWidget(
    title="Total Orders",
    value_callback=count_orders,
    description="This month",
    color="success",
)
```

**Key parameters:**

* `title` and `value_callback`: The label and the async callable that returns the metric.
* `description` and `color`: The secondary text below the value. `color` accepts Tabler color tokens, such as `"success"` and `"danger"`.
* `link`: Wraps the whole card in an anchor.
* `chart_callback`: Returns an ApexCharts `series` list, such as `[{"name": "Views", "data": [10, 20, 30]}]`, to render a sparkline at the bottom of the card.
* `countup`: Animates the metric value on load with countup.js.

### ChartWidget

An ApexCharts chart inside a card.

```python
from starlette.requests import Request
from starlette_admin import ChartWidget


async def revenue_series(request: Request) -> list[dict]:
    return [{"name": "Revenue", "data": [1200, 1450, 1100, 1800]}]


revenue_chart = ChartWidget(
    title="Revenue over time",
    chart_type="line",
    series_callback=revenue_series,
    height=300,
)
```

**Key parameters:**

* `chart_type`: Any valid ApexCharts string, such as `"line"`, `"bar"`, `"pie"`, `"donut"`, or `"heatmap"`.
* `series_callback`: Returns a list of dictionaries for most charts (`[{"name": "...", "data": [...]}]`). For `"pie"`, `"donut"`, and `"radialBar"`, it returns a flat list of numbers.
* `options`: A dictionary that merges over the default ApexCharts config. Use it for per-type settings such as `xaxis.categories` or `labels`.

### TableWidget

A compact, read-only summary table.

```python
from starlette.requests import Request
from starlette_admin import TableWidget


async def recent_orders(request: Request) -> list[list]:
    return [["#1042", "Ada Lovelace", 129.00], ["#1041", "Alan Turing", 89.50]]


latest_orders = TableWidget(
    title="Latest Orders",
    columns=["Order", "Customer", "Total"],
    rows_callback=recent_orders,
)
```

### TextWidget & HtmlWidget

Use `TextWidget` for plain text or Markdown, and `HtmlWidget` for pre-rendered HTML blocks.

```python
from starlette_admin import TextWidget, HtmlWidget

notes = TextWidget(
    content="## Release notes\n\n- Filters now support date ranges",
    markdown=True,  # Requires `pip install markdown`
    card=True,  # Set to False to render without the surrounding card
)

banner = HtmlWidget(
    html='<div class="alert alert-info">Maintenance window at 22:00 UTC</div>'
)
```

!!! warning "Security risk"
    `HtmlWidget` renders strings exactly as you provide them, without escaping. Never pass user-supplied content through it, because doing so exposes your admin to XSS injection.

### DividerWidget

Renders a horizontal rule (`<hr>`) to separate sections. It takes no parameters.

## Layout widgets

Layout widgets are the structural scaffolding of your custom views. Instead of rendering data, they organize, align, and position your content widgets.

!!! note
    These same layout widgets power the `form_layout` attribute on `ModelView`, so you can also use them to arrange create and edit form fields into columns, panels, and tabs. See [Form Layouts](../advanced/form-layout.md).

### Rows, columns, and cards

To build a responsive grid, combine these layout primitives:

* **`ColumnWidget`**: The vertical foundation. It stacks child widgets from top to bottom and usually serves as the root container for your dashboard tree.
* **`RowWidget`**: The horizontal container. It aligns children side by side in a flexbox row. Wrap a child in a `Col` object to set its responsive width through `Breakpoints`, on a standard 1–12 grid. Unwrapped children split the available width equally.
* **`CardRowWidget`**: The polished row. It inherits every `RowWidget` mechanic and gives all children equal heights. Use it when you arrange a row of cards, such as KPI statistics, charts, or data tables.

```python
from starlette_admin import Breakpoints, CardRowWidget, Col, ColumnWidget

# Group statistics side-by-side in equal-height cards
kpi_row = CardRowWidget(
    children=[
        Col(orders_stat, breakpoints=Breakpoints(default=12, md=6)),
        Col(revenue_stat, breakpoints=Breakpoints(default=12, md=6)),
    ]
)

# Stack the KPI row above the charts and tables
page = ColumnWidget(children=[kpi_row, revenue_chart, latest_orders])
```

### GridWidget

A responsive grid built on Bootstrap's `row-cols-*` system. Unlike `Col`, `Breakpoints` here sets the **number of items per row**, not the column span.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**: Wraps children in a titled card that you can make collapsible.
* **`TabsWidget`**: Renders one widget per tab. `tabs` accepts a list of `(label, widget)` tuples.

```python
from starlette_admin import PanelWidget, TabsWidget

orders_panel = PanelWidget(
    title="Recent Orders",
    icon="fa-solid fa-clock",
    children=[latest_orders, notes],
    collapsible=True,
)

reports = TabsWidget(tabs=[("Revenue", revenue_chart), ("Orders", latest_orders)])
```


## Composing the home dashboard

A `CustomView` powers the default admin root (`/admin/`). When you don't supply one, `Admin` builds a `DefaultIndexView` that shows record counts and links for your registered models.

To build your own dashboard, write a function that assembles the widget tree and pass it to the `index_view` parameter of your `Admin` instance.

```python
async def build_dashboard(request: Request) -> ColumnWidget:
    return ColumnWidget(
        children=[
            RowWidget(...),
            ChartWidget(...),
            PanelWidget(...),
        ]
    )


admin = Admin(
    engine,
    title="My Admin",
    secret_key="change-me",
    index_view=CustomView(
        menu_label="Dashboard",
        icon="fa fa-home",
        widget=build_dashboard,
    ),
)
```

Because `build_dashboard` runs on every request, your layout can adapt at runtime. For example, you can hide panels from non-admins or swap out charts.


## Custom templates

When the widget system isn't flexible enough, subclass `CustomView` and redecorate `index` with `@route("")` to render your own Jinja template instead of the default widget rendering:

```python
from starlette_admin import CustomView, route


class StatusView(CustomView):
    menu_label = "System Status"
    path = "/status"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(
            request=request,
            name="status.html",
            context={"title": self.title(request)},
        )


admin.add_view(StatusView())
```

`self.templates` is a `Jinja2Templates` instance resolved against your [templates directory](../advanced/templates.md). It's available only after the view is mounted, so don't call it from `__init__`. A custom template usually extends the base admin layout:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

To show widgets inside your custom template, resolve and render them yourself, then pass the result through your own context:

```python
from starlette_admin.widgets import render_widget


class StatusView(CustomView):
    menu_label = "System Status"
    path = "/status"
    widget = StatWidget(title="Pending jobs", value_callback=count_pending_jobs)

    @route("")
    async def index(self, request: Request) -> Response:
        widget = await self._resolve_widget(request)
        return self.templates.TemplateResponse(
            request=request,
            name="status.html",
            context={
                "title": self.title(request),
                "widget_html": await render_widget(widget, request, self.templates.env),
                "widget_additional_css": widget.additional_css_links(request),
                "widget_additional_js": widget.additional_js_links(request),
            },
        )
```

```html
{% extends "layout.html" %}

{% block head_css %}
    {{ super() }}
    {% for link in widget_additional_css %}<link rel="stylesheet" href="{{ link }}">{% endfor %}
{% endblock %}

{% block content %}
    <h1>System status</h1>
    {{ widget_html }}
{% endblock %}

{% block script %}
    {{ super() }}
    {% for link in widget_additional_js %}<script src="{{ link }}"></script>{% endfor %}
{% endblock %}

```

!!! important
    Leave out the CSS and JS blocks only when your template renders no widgets. Without them, chart and stat widgets can't load their dependencies, such as ApexCharts.


## Adding routes with `@route`

When a custom page needs its own endpoints, such as a JSON route that feeds a client-side chart or a POST handler for a form, subclass `CustomView` and attach methods with `@route`:

```python
from starlette.responses import JSONResponse
from starlette_admin import CustomView, route


class ReportsView(CustomView):
    menu_label = "Reports"
    icon = "fa fa-file-lines"
    path = "/reports"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(
            request=request,
            name="reports/index.html",
            context={"title": self.title(request)},
        )

    @route("/data", methods=["GET"])
    async def report_list(self, request: Request):
        return JSONResponse([{"id": "001", "status": "ready"}])

    @route("/generate", methods=["POST"])
    async def generate(self, request: Request):
        form = await request.form()
        return JSONResponse({"status": "queued"})


admin.add_view(ReportsView())
```

* **`path`**: Appended to the view's root path. In the example above, `@route("/data")` registers at `/admin/reports/data`.
* **CSRF protection**: Every mutating route (POST, PUT, DELETE) passes through CSRF middleware, so forms in your templates must include `{{ csrf_input(request) }}`.
* `CustomView` falls back from constructor arguments to class attributes, the way `ModelView` does, so `ReportsView()` above works with no arguments. Pass overrides, as in `ReportsView(menu_label="...")`, when you need per-instance configuration.


## Access control

To gate an entire `CustomView`, override the `is_accessible(request)` method. When it returns `False`, the admin removes the view from the sidebar and every `@route` endpoint returns `403 Forbidden`.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

For granular permissions, such as letting anyone view the page but only admins POST to it, put that logic in the specific `@route` handler instead of in `is_accessible`.


> See [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard) for a runnable app that uses every widget described on this page: `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget`, and `GridWidget`.

---

**What's next**

* **[Templates](../advanced/templates.md):** Customize the base layout your custom-view templates extend.
* **[Flash Messages](flash-messages.md):** Surface feedback from your `@route` handlers.
* **[Actions](actions.md):** Add bulk and row actions to your model views.
