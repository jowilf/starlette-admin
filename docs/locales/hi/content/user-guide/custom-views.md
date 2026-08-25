---
title: कस्टम व्यूज़ और विजेट
description: अपने starlette-admin पैनल के भीतर कस्टम dashboard widgets, static pages,
  और standalone views बनाएँ।
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# Custom Views

हर admin page को database model से map होना ज़रूरी नहीं। `CustomView` sidebar में एक standalone page बनाता है जिसे आप built-in widgets, custom templates, या custom routes से स्वयं compose करते हैं।

ज़्यादातर cases में आपको कुछ subclass करने की ज़रूरत नहीं। `CustomView` instantiate करें, उसे widget pass करें, और register करें:

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

* **`menu_label`**, **`icon`**, और **`path`**: Sidebar entry और URL को नियंत्रित करते हैं।
* **`widget`**: तय करता है कि page क्या render करे। Single `BaseWidget` instance pass करें, या callable (`(request) -> BaseWidget | None`) जो प्रति request tree बनाए। Page live data, current user, या feature flags पर निर्भर हो तो callable form का उपयोग करें।

एक से अधिक widget दिखाने के लिए [layout widget](#layout-widgets) pass करें जिसमें children हों।

`CustomView` subclass तभी करें जब आपको custom endpoints, access control, या HTTP response पर पूरा नियंत्रण चाहिए।

---

## Content widgets

Content widgets data को स्वयं render करते हैं। उनके `*_callback` parameters async callables accept करते हैं जो current `Request` पाते हैं, इसलिए हर widget live data fetch कर सकता है।

नीचे हर widget के complete constructor signature के लिए [Widgets API reference](../api/widgets.md) देखें।

### StatWidget

एक KPI card जो single metric, optional description, और sparkline दिखाता है।

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

**मुख्य parameters:**

* `title` और `value_callback`: Label और metric return करने वाला async callable.
* `description` और `color`: Value के नीचे secondary text। `color` Tabler color tokens accept करता है, जैसे `"success"` और `"danger"`.
* `link`: पूरे card को anchor में wrap करता है।
* `chart_callback`: Card के नीचे sparkline render करने के लिए ApexCharts `series` list return करता है, जैसे `[{"name": "Views", "data": [10, 20, 30]}]`.
* `countup`: Load पर metric value को countup.js से animate करता है।

### ChartWidget

Card के अंदर ApexCharts chart.

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

**मुख्य parameters:**

* `chart_type`: कोई भी valid ApexCharts string — जैसे `"line"`, `"bar"`, `"pie"`, `"donut"`, या `"heatmap"`.
* `series_callback`: ज़्यादातर charts के लिए dictionaries की list return करता है (`[{"name": "...", "data": [...]}]`). `"pie"`, `"donut"`, और `"radialBar"` के लिए numbers की flat list return करता है।
* `options`: Default ApexCharts config के ऊपर merge होने वाला dictionary। Per-type settings के लिए उपयोग करें, जैसे `xaxis.categories` या `labels`.

### TableWidget

एक compact, read-only summary table.

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

Plain text या Markdown के लिए `TextWidget`, और pre-rendered HTML blocks के लिए `HtmlWidget` उपयोग करें।

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

!!! warning "सुरक्षा जोखिम"
    `HtmlWidget` strings को ठीक वैसे ही render करता है जैसे आप provide करते हैं — escaping के बिना। User-supplied content कभी इससे pass न करें, अन्यथा आपका admin XSS injection के संपर्क में आ जाता है।

### DividerWidget

Sections अलग करने के लिए horizontal rule (`<hr>`) render करता है। कोई parameter नहीं लेता।

## लेआउट widgets {#layout-widgets}

Layout widgets आपके custom views की structural scaffolding हैं। Data render करने के बजाय, वे आपके content widgets को organize, align, और position करते हैं।

!!! note
    वही layout widgets `ModelView` के `form_layout` attribute को भी power देते हैं, इसलिए create/edit form fields को columns, panels, और tabs में arrange करने के लिए भी उन्हीं का उपयोग कर सकते हैं। [Form Layouts](../advanced/form-layout.md) देखें।

### Rows, columns, और cards {#rows-columns-and-cards}

Responsive grid बनाने के लिए इन layout primitives को जोड़ें:

* **`ColumnWidget`**: Vertical foundation। Child widgets को ऊपर से नीचे stack करता है, और आमतौर पर dashboard tree का root container होता है।
* **`RowWidget`**: Horizontal container। Children को flexbox row में side by side align करता है। Child को `Col` object में wrap करके `Breakpoints` के माध्यम से standard 1–12 grid पर responsive width सेट करें। Unwrapped children available width को समान बाँटते हैं।
* **`CardRowWidget`**: Polished row। यह हर `RowWidget` mechanism inherit करता है और सभी children को equal heights देता है। Cards की row arrange करते समय उपयोग करें — KPI statistics, charts, या data tables.

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

Bootstrap के `row-cols-*` system पर बना responsive grid। `Col` के विपरीत, यहाँ `Breakpoints` **row पर items की संख्या** सेट करता है, column span नहीं।

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**: Children को titled card में wrap करता है जिसे collapsible बनाया जा सकता है।
* **`TabsWidget`**: प्रति tab एक widget render करता है। `tabs` `(label, widget)` tuples की list accept करता है।

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


## Home dashboard compose करना {#composing-the-home-dashboard}

एक `CustomView` default admin root (`/admin/`) को power देता है। जब आप कोई supply नहीं करते, `Admin` एक `DefaultIndexView` बनाता है जो record counts और registered models के links दिखाता है।

अपना dashboard बनाने के लिए ऐसा function लिखें जो widget tree assemble करे, और उसे अपने `Admin` instance के `index_view` parameter को pass करें।

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

चूँकि `build_dashboard` हर request पर चलता है, आपका layout runtime पर adapt कर सकता है — उदाहरण के लिए non-admins से panels छिपाना या charts swap करना।


## Custom templates

जब widget system पर्याप्त flexible न हो, `CustomView` subclass करें और `index` को `@route("")` से redecorate करें ताकि default widget rendering के बजाय अपना Jinja template render हो:

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

`self.templates` एक `Jinja2Templates` instance है जो आपकी [templates directory](../advanced/templates.md) के विरुद्ध resolve होता है। यह view mount होने के बाद ही उपलब्ध है, इसलिए `__init__` से इसे कॉल न करें। Custom template आमतौर पर base admin layout extend करता है:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Custom template के अंदर widgets दिखाने के लिए उन्हें स्वयं resolve/render करें और result को अपने context से pass करें:

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
    CSS और JS blocks तभी छोड़ें जब आपका template कोई widget render न करे। इनके बिना chart और stat widgets अपनी dependencies — जैसे ApexCharts — load नहीं कर पाते।


## `@route` से routes जोड़ना {#adding-routes-with-route}

जब custom page को अपने endpoints चाहिए — client-side chart feed करने वाला JSON route या form के लिए POST handler — तब `CustomView` subclass करें और methods को `@route` से attach करें:

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

* **`path`**: View के root path से append होता है। ऊपर के उदाहरण में `@route("/data")`, `/admin/reports/data` पर register होता है।
* **CSRF protection**: हर mutating route (POST, PUT, DELETE) CSRF middleware से गुज़रता है, इसलिए templates के forms में `{{ csrf_input(request) }}` include करना ज़रूरी है।
* `CustomView` constructor arguments से class attributes पर fallback करता है — वैसे ही जैसे `ModelView` — इसलिए ऊपर का `ReportsView()` बिना arguments के काम करता है। Per-instance configuration के लिए overrides pass करें, जैसे `ReportsView(menu_label="...")`.


## Access control

पूरे `CustomView` को gate करने के लिए `is_accessible(request)` method override करें। `False` return करने पर admin view को sidebar से हटा देता है और हर `@route` endpoint `403 Forbidden` return करता है।

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Granular permissions — जैसे page कोई भी देख सके पर POST केवल admins करें — के लिए वह logic specific `@route` handler में रखें, `is_accessible` में नहीं।


> इस पेज पर वर्णित हर widget — `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget`, और `GridWidget` — उपयोग करने वाले runnable app के लिए [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard) देखें।

---

**आगे क्या**

* **[Templates](../advanced/templates.md):** Base layout customize करें जिसे आपके custom-view templates extend करते हैं।
* **[Flash Messages](flash-messages.md):** अपने `@route` handlers से feedback surface करें।
* **[एक्शन](actions.md):** Model views में bulk और row actions जोड़ें।
