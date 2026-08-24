---
title: Пользовательские представления и виджеты
description: Создавайте пользовательские виджеты дашборда, статические страницы и
  автономные представления внутри панели администрирования starlette-admin.
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# Пользовательские представления

Не каждая страница панели администрирования соответствует модели базы данных. `CustomView` создаёт автономную страницу в боковой панели, которую вы собираете сами из встроенных виджетов, пользовательских шаблонов или пользовательских маршрутов.

В большинстве случаев ничего наследовать не нужно. Создайте экземпляр `CustomView`, передайте ему виджет и зарегистрируйте его:

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

* **`menu_label`**, **`icon`** и **`path`**: управляют пунктом в боковой панели и URL.
* **`widget`**: определяет, что отображает страница. Передайте один экземпляр `BaseWidget` либо вызываемый объект (`(request) -> BaseWidget | None`), который строит дерево для каждого запроса. Используйте вызываемую форму, когда страница зависит от актуальных данных, текущего пользователя или флагов функций.

Чтобы показать несколько виджетов, передайте [виджет компоновки](#layout-widgets), который содержит дочерние элементы.

Наследуйте класс `CustomView` только тогда, когда нужны пользовательские эндпоинты, управление доступом или полный контроль над HTTP-ответом.

---

## Виджеты содержимого

Виджеты содержимого отображают сами данные. Их параметры `*_callback` принимают асинхронные вызываемые объекты, которые получают текущий `Request`, поэтому каждый виджет может получать актуальные данные.

Полные сигнатуры конструкторов всех описанных ниже виджетов см. в [справочнике API виджетов](../api/widgets.md).

### StatWidget

Карточка KPI, которая показывает одну метрику, необязательное описание и спарклайн.

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

**Основные параметры:**

* `title` и `value_callback`: метка и асинхронный вызываемый объект, возвращающий метрику.
* `description` и `color`: дополнительный текст под значением. Параметр `color` принимает цветовые токены Tabler, например `"success"` и `"danger"`.
* `link`: оборачивает всю карточку в ссылку.
* `chart_callback`: возвращает список `series` для ApexCharts, например `[{"name": "Views", "data": [10, 20, 30]}]`, чтобы отрисовать спарклайн внизу карточки.
* `countup`: анимирует значение метрики при загрузке с помощью countup.js.

### ChartWidget

Диаграмма ApexCharts внутри карточки.

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

**Основные параметры:**

* `chart_type`: любая допустимая строка ApexCharts, например `"line"`, `"bar"`, `"pie"`, `"donut"` или `"heatmap"`.
* `series_callback`: для большинства диаграмм возвращает список словарей (`[{"name": "...", "data": [...]}]`). Для `"pie"`, `"donut"` и `"radialBar"` возвращает плоский список чисел.
* `options`: словарь, который объединяется с конфигурацией ApexCharts по умолчанию. Используйте его для настроек конкретных типов диаграмм, например `xaxis.categories` или `labels`.

### TableWidget

Компактная сводная таблица только для чтения.

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

### TextWidget и HtmlWidget

Используйте `TextWidget` для обычного текста или Markdown, а `HtmlWidget` — для готовых HTML-блоков.

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

!!! warning "Риск безопасности"
    `HtmlWidget` выводит строки точно так, как вы их передаёте, без экранирования. Никогда не пропускайте через него пользовательский контент: это открывает вашу панель администрирования для XSS-инъекций.

### DividerWidget

Отображает горизонтальную линию (`<hr>`) для разделения секций. Не принимает параметров.

## Виджеты компоновки {#layout-widgets}

Виджеты компоновки — это структурный каркас ваших пользовательских представлений. Вместо отображения данных они организуют, выравнивают и позиционируют виджеты содержимого.

!!! note
    Эти же виджеты компоновки используются атрибутом `form_layout` у `ModelView`, поэтому с их помощью можно также располагать поля форм создания и редактирования по колонкам, панелям и вкладкам. См. [Компоновку формы](../advanced/form-layout.md).

### Строки, колонки и карточки

Чтобы построить адаптивную сетку, комбинируйте эти базовые элементы компоновки:

* **`ColumnWidget`**: вертикальная основа. Он складывает дочерние виджеты сверху вниз и обычно служит корневым контейнером дерева дашборда.
* **`RowWidget`**: горизонтальный контейнер. Он располагает дочерние элементы рядом во flexbox-строке. Оберните дочерний элемент в объект `Col`, чтобы задать его адаптивную ширину через `Breakpoints` на стандартной сетке из 1–12 колонок. Дочерние элементы без обёртки делят доступную ширину поровну.
* **`CardRowWidget`**: аккуратная строка. Он наследует все механики `RowWidget` и задаёт всем дочерним элементам одинаковую высоту. Используйте его, когда выстраиваете строку карточек — например, KPI-статистику, диаграммы или таблицы данных.

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

Адаптивная сетка на основе системы `row-cols-*` из Bootstrap. В отличие от `Col`, здесь `Breakpoints` задаёт **количество элементов в строке**, а не ширину колонки.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget и TabsWidget

* **`PanelWidget`**: оборачивает дочерние элементы в карточку с заголовком, которую можно сделать сворачиваемой.
* **`TabsWidget`**: отображает один виджет на вкладке. Параметр `tabs` принимает список кортежей `(label, widget)`.

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


## Сборка домашнего дашборда

Представление `CustomView` обслуживает корневую страницу панели администрирования по умолчанию (`/admin/`). Если вы его не задали, `Admin` создаёт `DefaultIndexView`, который показывает количество записей и ссылки на зарегистрированные модели.

Чтобы собрать собственный дашборд, напишите функцию, которая собирает дерево виджетов, и передайте её в параметр `index_view` вашего экземпляра `Admin`.

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

Поскольку `build_dashboard` выполняется при каждом запросе, компоновка может меняться во время работы. Например, можно скрывать панели от пользователей без прав администратора или подменять диаграммы.


## Пользовательские шаблоны

Когда возможностей системы виджетов недостаточно, создайте подкласс `CustomView` и заново декорируйте метод `index` с помощью `@route("")`, чтобы вместо стандартного рендеринга виджетов отдавать собственный шаблон Jinja:

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

`self.templates` — это экземпляр `Jinja2Templates`, который разрешается относительно вашей [директории шаблонов](../advanced/templates.md). Он доступен только после монтирования представления, поэтому не обращайтесь к нему из `__init__`. Пользовательский шаблон обычно расширяет базовый макет панели администрирования:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Чтобы показать виджеты внутри пользовательского шаблона, разрешите и отрисуйте их самостоятельно, а затем передайте результат через собственный контекст:

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
    Опускать блоки CSS и JS можно только если ваш шаблон не отображает виджеты. Без них виджеты диаграмм и статистики не смогут загрузить свои зависимости, такие как ApexCharts.


## Добавление маршрутов с помощью `@route`

Когда пользовательской странице нужны собственные эндпоинты — например, JSON-маршрут для клиентской диаграммы или обработчик POST для формы, — создайте подкласс `CustomView` и добавьте методы с помощью `@route`:

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

* **`path`**: добавляется к корневому пути представления. В примере выше `@route("/data")` регистрируется по адресу `/admin/reports/data`.
* **Защита CSRF**: каждый изменяющий данные маршрут (POST, PUT, DELETE) проходит через CSRF middleware, поэтому формы в ваших шаблонах должны включать `{{ csrf_input(request) }}`.
* `CustomView` берёт значения из аргументов конструктора, а при их отсутствии — из атрибутов класса, как это делает `ModelView`, поэтому `ReportsView()` выше работает без аргументов. Передавайте переопределения, например `ReportsView(menu_label="...")`, когда нужна настройка для отдельного экземпляра.


## Управление доступом

Чтобы ограничить доступ ко всему `CustomView`, переопределите метод `is_accessible(request)`. Когда он возвращает `False`, панель администрирования убирает представление из боковой панели, а каждый эндпоинт `@route` возвращает `403 Forbidden`.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Для детальных прав доступа — например, когда страницу могут просматривать все, а отправлять POST-запросы только администраторы, — разместите такую логику в конкретном обработчике `@route`, а не в `is_accessible`.


> Запускаемое приложение, использующее все описанные на этой странице виджеты — `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget` и `GridWidget`, — см. в [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard).

---

**Что дальше**

* **[Шаблоны](../advanced/templates.md):** настройте базовый макет, который расширяют шаблоны ваших пользовательских представлений.
* **[Флеш-сообщения](flash-messages.md):** показывайте обратную связь из обработчиков `@route`.
* **[Действия](actions.md):** добавьте групповые действия и действия над строками в ваши представления моделей.
