---
title: 自定义视图与部件
description: 在 starlette-admin 面板中构建自定义仪表盘部件、静态页面和独立视图。
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# 自定义视图

并非每个管理页面都对应某个数据库模型。`CustomView` 会在侧边栏中创建一个独立页面，你可以完全使用内置部件、自定义模板或自定义路由来自行组装。

在大多数情况下，你无需继承任何类。只需实例化 `CustomView`，传入一个部件，然后注册即可：

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

* **`menu_label`**、**`icon`** 和 **`path`**：控制侧边栏条目和 URL。
* **`widget`**：决定页面渲染的内容。可以传入单个 `BaseWidget` 实例，或传入一个可调用对象（`(request) -> BaseWidget | None`），按请求构建部件树。当页面依赖实时数据、当前用户或功能开关时，请使用可调用对象形式。

要显示多个部件，请传入一个包含子部件的[布局部件](#layout-widgets)。

仅当你需要自定义端点、访问控制或完全掌控 HTTP 响应时，才需要继承 `CustomView`。

---

## 内容部件

内容部件负责渲染数据本身。它们的 `*_callback` 参数接受异步可调用对象，这些对象会接收当前的 `Request`，因此每个部件都能获取实时数据。

下方每个部件的完整构造函数签名，请参阅[部件 API 参考](../api/widgets.md)。

### StatWidget

一种 KPI 卡片，显示单个指标、可选的描述文本和一个迷你图。

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

**关键参数：**

* `title` 和 `value_callback`：标签以及返回指标的异步可调用对象。
* `description` 和 `color`：数值下方的辅助文本。`color` 接受 Tabler 颜色令牌，例如 `"success"` 和 `"danger"`。
* `link`：将整张卡片包裹在锚点链接中。
* `chart_callback`：返回 ApexCharts `series` 列表，例如 `[{"name": "Views", "data": [10, 20, 30]}]`，以便在卡片底部渲染迷你图。
* `countup`：加载时使用 countup.js 为指标值添加动画效果。

### ChartWidget

卡片中的 ApexCharts 图表。

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

**关键参数：**

* `chart_type`：任意有效的 ApexCharts 字符串，例如 `"line"`、`"bar"`、`"pie"`、`"donut"` 或 `"heatmap"`。
* `series_callback`：对于大多数图表返回字典列表（`[{"name": "...", "data": [...]}]`）。对于 `"pie"`、`"donut"` 和 `"radialBar"`，则返回一个扁平的数字列表。
* `options`：一个字典，会合并覆盖默认的 ApexCharts 配置。可用于各类图表专属的设置，例如 `xaxis.categories` 或 `labels`。

### TableWidget

一个紧凑的只读汇总表格。

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

使用 `TextWidget` 显示纯文本或 Markdown，使用 `HtmlWidget` 显示预渲染的 HTML 块。

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

!!! warning "安全风险"
    `HtmlWidget` 会完全按照你提供的方式渲染字符串，不做任何转义。切勿将用户提供的内容传递给它，否则会使你的管理后台暴露于 XSS 注入风险之中。

### DividerWidget

渲染一条水平分隔线（`<hr>`）来分隔各个区块。它不接受任何参数。

## 布局部件 {#layout-widgets}

布局部件是自定义视图的结构骨架。它们不渲染数据，而是负责组织、对齐和排列你的内容部件。

!!! note
    同样的布局部件也为 `ModelView` 上的 `form_layout` 属性提供支持，因此你还可以用它们将新建和编辑表单字段排列成多列、面板和选项卡。参见[表单布局](../advanced/form-layout.md)。

### 行、列与卡片

要构建响应式网格，请组合以下布局原语：

* **`ColumnWidget`**：垂直基础容器。它自上而下堆叠子部件，通常作为仪表盘树的根容器。
* **`RowWidget`**：水平容器。它在 flexbox 行中并排对齐子项。将子项包裹在 `Col` 对象中，可以通过 `Breakpoints` 在标准的 1–12 网格上设置其响应式宽度。未包裹的子项会平均分配可用宽度。
* **`CardRowWidget`**：精致的一行。它继承了 `RowWidget` 的全部机制，并使所有子项高度一致。适合在排列一排卡片时使用，例如 KPI 统计、图表或数据表格。

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

基于 Bootstrap `row-cols-*` 系统构建的响应式网格。与 `Col` 不同，这里的 `Breakpoints` 设置的是**每行的项目数**，而不是列跨度。

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**：将子部件包裹在带标题的卡片中，并可将其设为可折叠。
* **`TabsWidget`**：每个选项卡渲染一个部件。`tabs` 接受 `(label, widget)` 元组组成的列表。

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


## 组装首页仪表盘

默认的管理根路径（`/admin/`）由一个 `CustomView` 驱动。如果你不提供自定义视图，`Admin` 会构建一个 `DefaultIndexView`，显示已注册模型的记录计数和链接。

要构建自己的仪表盘，请编写一个组装部件树的函数，并将其传递给 `Admin` 实例的 `index_view` 参数。

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

由于 `build_dashboard` 在每次请求时都会运行，布局可以在运行时动态调整。例如，你可以向非管理员隐藏某些面板，或者更换图表。


## 自定义模板

当部件系统不够灵活时，请继承 `CustomView` 并使用 `@route("")` 重新装饰 `index` 方法，以渲染你自己的 Jinja 模板，而不是默认的部件渲染：

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

`self.templates` 是一个 `Jinja2Templates` 实例，根据你的[模板目录](../advanced/templates.md)解析而来。它仅在视图挂载后才可用，因此不要在 `__init__` 中调用它。自定义模板通常继承基础管理布局：

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

要在自定义模板内显示部件，请自行解析并渲染它们，然后将结果通过你自己的上下文传递：

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
    仅当你的模板不渲染任何部件时，才可以省略 CSS 和 JS 块。缺少这些块时，图表部件和统计部件将无法加载其依赖项（例如 ApexCharts）。


## 使用 `@route` 添加路由

当自定义页面需要自己的端点时——例如为前端图表提供数据的 JSON 路由，或处理表单的 POST 处理器——请继承 `CustomView` 并使用 `@route` 附加方法：

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

* **`path`**：追加到视图的根路径之后。在上面的示例中，`@route("/data")` 注册在 `/admin/reports/data`。
* **CSRF 保护**：每个变更型路由（POST、PUT、DELETE）都会经过 CSRF 中间件，因此模板中的表单必须包含 `{{ csrf_input(request) }}`。
* `CustomView` 会在构造函数参数缺省时回退到类属性，与 `ModelView` 的做法相同，因此上面的 `ReportsView()` 无需参数即可正常工作。当你需要针对实例的配置时，可传入覆盖值，例如 `ReportsView(menu_label="...")`。


## 访问控制

要控制整个 `CustomView` 的访问权限，请重写 `is_accessible(request)` 方法。当该方法返回 `False` 时，管理后台会从侧边栏中移除该视图，并且每个 `@route` 端点都会返回 `403 Forbidden`。

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

对于更细粒度的权限，例如允许任何人查看页面但仅允许管理员 POST，请将该逻辑放在具体的 `@route` 处理器中，而不是 `is_accessible` 中。


> 请参阅 [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard)，这是一个可运行的应用，用到了本页介绍的每一个部件：`StatWidget`、`ChartWidget`、`TableWidget`、`TabsWidget`、`PanelWidget` 和 `GridWidget`。

---

**下一步**

* **[模板](../advanced/templates.md)：** 定制你的自定义视图模板所继承的基础布局。
* **[Flash 消息](flash-messages.md)：** 在 `@route` 处理器中呈现反馈信息。
* **[动作](actions.md)：** 为模型视图添加批量动作和行级动作。
