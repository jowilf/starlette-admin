---
title: Пользовательские представления и виджеты
description: Создавайте пользовательские виджеты для дашборда, статические страницы
  и отдельные представления внутри панели starlette-admin.
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

Далеко не каждая страница админ-панели соответствует модели базы данных. `CustomView` создаёт отдельную страницу в боковом меню, которую вы собираете самостоятельно из встроенных виджетов, собственных шаблонов или собственных маршрутов.

В большинстве случаев вам не нужно ничего наследовать. Достаточно создать экземпляр `CustomView`, передать ему виджет и зарегистрировать:

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

* **`menu_label`**, **`icon`** и **`path`**: управляют пунктом в боковом меню и URL-адресом.
* **`widget`**: определяет содержимое страницы. Передайте один экземпляр `BaseWidget` либо callable-функцию (`(request) -> BaseWidget | None`), которая строит дерево виджетов для каждого запроса. Используйте вариант с функцией, когда страница зависит от актуальных данных, текущего пользователя или флагов функций.

Чтобы показать несколько виджетов, передайте [layout-виджет](#layout-widgets), содержащий дочерние элементы.

Наследуйте `CustomView` только тогда, когда нужны собственные endpoint'ы, контроль доступа или полный контроль над HTTP-ответом.

---

## Контентные виджеты

Контентные виджеты отображают сами данные. Их параметры `*_callback` принимают асинхронные callable-объекты, которые получают текущий `Request`, поэтому каждый виджет может получать данные в реальном времени.

Полную сигнатуру конструктора каждого из приведённых ниже виджетов см. в [справочнике API виджетов](../api/widgets.md).

### StatWidget

Карточка KPI, показывающая одну метрику, необязательное описание и спарклайн.

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

**Ключевые параметры:**

* `title` и `value_callback`: подпись и асинхронная функция, возвращающая метрику.
* `description` и `color`: вспомогательный текст под значением. `color` принимает цветовые токены Tabler, например `"success"` и `"danger"`.
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

**Ключевые параметры:**

* `chart_type`: любая допустимая строка ApexCharts, например `"line"`, `"bar"`, `"pie"`, `"donut"` или `"heatmap"`.
* `series_callback`: для большинства диаграмм возвращает список словарей (`[{"name": "...", "data": [...]}]`). Для `"pie"`, `"donut"` и `"radialBar"` он возвращает плоский список чисел.
* `options`: словарь, который объединяется с конфигурацией ApexCharts по умолчанию. Используйте его для настроек конкретного типа, например `xaxis.categories` или `labels`.

### TableWidget

Компактная таблица сводки только для чтения.

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

Используйте `TextWidget` для обычного текста или Markdown, а `HtmlWidget` — для готовых блоков HTML.

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

!!! warning "Риск для безопасности"
    `HtmlWidget` отображает строки ровно в том виде, в каком вы их передаёте, без экранирования. Никогда не пропускайте через него пользовательский контент, иначе панель администрирования становится уязвимой к XSS-инъекциям.

### DividerWidget

Отображает горизонтальную разделительную линию (`<hr>`), чтобы отделить секции друг от друга. Не принимает параметров.

## Layout-виджеты {#layout-widgets}

Layout-виджеты — это структурный каркас ваших пользовательских представлений. Вместо отображения данных они организуют, выравнивают и позиционируют ваши контентные виджеты.

!!! note
    Эти же layout-виджеты используются атрибутом `form_layout` у `ModelView`, поэтому с их помощью можно располагать поля форм создания и редактирования по колонкам, панелям и вкладкам. См. [Form Layouts](../advanced/form-layout.md).

### Строки, колонки и карточки

Чтобы построить адаптивную сетку, комбинируйте следующие базовые элементы:

* **`ColumnWidget`**: вертикальная основа. Он складывает дочерние виджеты сверху вниз и обычно служит корневым контейнером дерева вашего дашборда.
* **`RowWidget`**: горизонтальный контейнер. Он размещает дочерние элементы рядом во flexbox-строке. Оберните дочерний элемент в объект `Col`, чтобы задать его адаптивную ширину через `Breakpoints` на стандартной сетке от 1 до 12 колонок. Необёрнутые дочерние элементы делят доступную ширину поровну.
* **`CardRowWidget`**: аккуратная строка. Он наследует все механики `RowWidget` и делает высоту всех дочерних элементов одинаковой. Используйте его, когда выстраиваете строку карточек, например KPI-статистику, диаграммы или таблицы данных.

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

Адаптивная сетка, построенная на системе `row-cols-*` Bootstrap. В отличие от `Col`, здесь `Breakpoints` задаёт **количество элементов в строке**, а не ширину колонок.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**: помещает дочерние элементы в карточку с заголовком, которую можно сделать сворачиваемой.
* **`TabsWidget`**: отображает один виджет на вкладку. `tabs` принимает список кортежей `(label, widget)`.

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


## Сборка главного дашборда

`CustomView` обслуживает корневую страницу панели по умолчанию (`/admin/`). Если вы его не предоставите, `Admin` создаёт `DefaultIndexView`, который показывает количество записей и ссылки на зарегистрированные модели.

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

Поскольку `build_dashboard` выполняется при каждом запросе, ваша раскладка может адаптироваться во время выполнения. Например, можно скрывать панели от пользователей без прав администратора или подменять диаграммы.


## Пользовательские шаблоны

Когда системы виджетов недостаточно, наследуйте `CustomView` и переопределите метод `index` декоратором `@route("")`, чтобы вместо стандартного рендеринга виджетов отрисовать ваш собственный Jinja-шаблон:

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

`self.templates` — это экземпляр `Jinja2Templates`, привязанный к вашему [каталогу шаблонов](../advanced/templates.md). Он доступен только после монтирования представления, поэтому не вызывайте его из `__init__`. Пользовательский шаблон обычно наследует базовую раскладку панели администрирования:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Чтобы показать виджеты внутри вашего шаблона, самостоятельно разрешите и отрендерите их, а затем передайте результат через собственный контекст:

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
    Опускайте блоки CSS и JS только в том случае, если ваш шаблон не отображает ни одного виджета. Без них виджеты диаграмм и статистики не смогут загрузить свои зависимости, например ApexCharts.


## Добавление маршрутов с помощью `@route`

Когда странице требуются собственные endpoint'ы, например JSON-маршрут для клиентской диаграммы или обработчик POST для формы, наследуйте `CustomView` и добавляйте методы с помощью `@route`:

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
* **Защита CSRF**: каждый изменяющий маршрут (POST, PUT, DELETE) проходит через CSRF-middleware, поэтому формы в ваших шаблонах должны включать `{{ csrf_input(request) }}`.
* `CustomView` использует аргументы конструктора как переопределение атрибутов класса — так же, как это делает `ModelView`, поэтому `ReportsView()` выше работает без аргументов. Передавайте переопределения, как в `ReportsView(menu_label="...")`, если нужна конфигурация для конкретного экземпляра.


## Контроль доступа

Чтобы ограничить доступ к целому `CustomView`, переопределите метод `is_accessible(request)`. Когда он возвращает `False`, панель убирает представление из бокового меню, а все endpoint'ы `@route` возвращают `403 Forbidden`.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Для детализированных разрешений, например когда страницу могут просматривать все, но POST отправлять могут только администраторы, разместите эту логику в конкретном обработчике `@route`, а не в `is_accessible`.


> Пример работающего приложения со всеми описанными на этой странице виджетами — `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget` и `GridWidget` — смотрите в [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard).

---

**Что дальше**

* **[Шаблоны](../advanced/templates.md):** настройка базовой раскладки, которую наследуют шаблоны ваших пользовательских представлений.
* **[Flash Messages](flash-messages.md):** вывод обратной связи из обработчиков `@route`.
* **[Actions](actions.md):** добавление массовых и строчных действий к вашим model views.
