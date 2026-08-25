---
title: Vistas y widgets personalizados
description: Cree widgets de dashboard personalizados, páginas estáticas y vistas
  independientes dentro de su panel de starlette-admin.
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# Vistas personalizadas

No todas las páginas del panel de administración corresponden a un modelo de base de datos. Una `CustomView` crea una página independiente en la barra lateral que usted compone a su gusto con widgets integrados, plantillas personalizadas o rutas personalizadas.

En la mayoría de los casos, no necesita heredar de ninguna clase. Instancie `CustomView`, pásale un widget y regístrelo:

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

* **`menu_label`**, **`icon`** y **`path`**: Controlan la entrada de la barra lateral y la URL.
* **`widget`**: Determina lo que la página renderiza. Pase una única instancia de `BaseWidget`, o un callable (`(request) -> BaseWidget | None`) que construya el árbol por cada petición. Utilice la forma callable cuando la página dependa de datos en vivo, del usuario actual o de feature flags.

Para mostrar más de un widget, pase un [widget de layout](#layout-widgets) que contenga hijos.

Herede de `CustomView` únicamente cuando necesite endpoints personalizados, control de acceso o control total sobre la respuesta HTTP.

---

## Widgets de contenido {#layout-widgets}

Los widgets de contenido renderizan los datos en sí mismos. Sus parámetros `*_callback` aceptan callables asíncronos que reciben el `Request` actual, de modo que cada widget puede obtener datos en vivo.

Para ver la firma completa del constructor de cada widget descrito a continuación, consulte la [referencia de la API de Widgets](../api/widgets.md).

### StatWidget

Una tarjeta KPI que muestra una única métrica, una descripción opcional y un sparkline.

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

**Parámetros clave:**

* `title` y `value_callback`: La etiqueta y el callable asíncrono que devuelve la métrica.
* `description` y `color`: El texto secundario debajo del valor. `color` acepta tokens de color de Tabler, como `"success"` y `"danger"`.
* `link`: Envuelve toda la tarjeta en un ancla.
* `chart_callback`: Devuelve una lista `series` de ApexCharts, como `[{"name": "Views", "data": [10, 20, 30]}]`, para renderizar un sparkline en la parte inferior de la tarjeta.
* `countup`: Anima el valor de la métrica al cargar mediante countup.js.

### ChartWidget

Un gráfico de ApexCharts dentro de una tarjeta.

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

**Parámetros clave:**

* `chart_type`: Cualquier cadena válida de ApexCharts, como `"line"`, `"bar"`, `"pie"`, `"donut"` o `"heatmap"`.
* `series_callback`: Devuelve una lista de diccionarios para la mayoría de los gráficos (`[{"name": "...", "data": [...]}]`). Para `"pie"`, `"donut"` y `"radialBar"`, devuelve una lista plana de números.
* `options`: Un diccionario que se fusiona con la configuración predeterminada de ApexCharts. Úselo para ajustes específicos de cada tipo, como `xaxis.categories` o `labels`.

### TableWidget

Una tabla resumen compacta y de solo lectura.

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

Utilice `TextWidget` para texto plano o Markdown, y `HtmlWidget` para bloques HTML prerenderizados.

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

!!! warning "Riesgo de seguridad"
    `HtmlWidget` renderiza las cadenas exactamente tal como usted las proporciona, sin escaparlas. Nunca pase contenido suministrado por el usuario a través de él, ya que hacerlo expone su panel a inyecciones XSS.

### DividerWidget

Renderiza una línea horizontal (`<hr>`) para separar secciones. No recibe parámetros.

## Widgets de layout

Los widgets de layout son la estructura básica de sus vistas personalizadas. En lugar de renderizar datos, organizan, alinean y posicionan sus widgets de contenido.

!!! note
    Estos mismos widgets de layout alimentan el atributo `form_layout` de `ModelView`, por lo que también puede usarlos para organizar los campos de los formularios de creación y edición en columnas, paneles y pestañas. Consulte [Form Layouts](../advanced/form-layout.md).

### Filas, columnas y tarjetas

Para construir una cuadrícula responsiva, combine estas primitivas de layout:

* **`ColumnWidget`**: La base vertical. Apila los widgets hijos de arriba hacia abajo y normalmente sirve como contenedor raíz del árbol de su dashboard.
* **`RowWidget`**: El contenedor horizontal. Alinea los hijos lado a lado en una fila flexbox. Envuelva un hijo en un objeto `Col` para definir su ancho responsivo mediante `Breakpoints`, en una cuadrícula estándar de 1–12. Los hijos sin envolver reparten el ancho disponible en partes iguales.
* **`CardRowWidget`**: La fila pulida. Hereda todas las mecánicas de `RowWidget` y da a todos los hijos la misma altura. Úselo cuando disponga una fila de tarjetas, como estadísticas KPI, gráficos o tablas de datos.

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

Una cuadrícula responsiva basada en el sistema `row-cols-*` de Bootstrap. A diferencia de `Col`, aquí `Breakpoints` define el **número de elementos por fila**, no la extensión de columna.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**: Envuelve a los hijos en una tarjeta con título que puede hacer colapsable.
* **`TabsWidget`**: Renderiza un widget por pestaña. `tabs` acepta una lista de tuplas `(label, widget)`.

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


## Composición del dashboard principal

Una `CustomView` alimenta la raíz predeterminada del panel (`/admin/`). Cuando usted no proporciona una, `Admin` construye una `DefaultIndexView` que muestra conteos de registros y enlaces para sus modelos registrados.

Para construir su propio dashboard, escriba una función que ensamble el árbol de widgets y pásela al parámetro `index_view` de su instancia de `Admin`.

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

Como `build_dashboard` se ejecuta en cada petición, su layout puede adaptarse en tiempo de ejecución. Por ejemplo, puede ocultar paneles a usuarios que no sean administradores o sustituir gráficos.


## Plantillas personalizadas

Cuando el sistema de widgets no sea lo bastante flexible, herede de `CustomView` y vuelva a decorar `index` con `@route("")` para renderizar su propia plantilla Jinja en lugar del renderizado predeterminado de widgets:

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

`self.templates` es una instancia de `Jinja2Templates` resuelta contra su [directorio de plantillas](../advanced/templates.md). Solo está disponible después de montar la vista, así que no la llame desde `__init__`. Una plantilla personalizada normalmente extiende el layout base del panel:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Para mostrar widgets dentro de su plantilla personalizada, resuélvalos y renderícelos usted mismo, y luego pase el resultado a través de su propio contexto:

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
    Omita los bloques CSS y JS únicamente cuando su plantilla no renderice ningún widget. Sin ellos, los widgets de gráficos y estadísticas no pueden cargar sus dependencias, como ApexCharts.


## Adición de rutas con `@route`

Cuando una página personalizada necesita sus propios endpoints, como una ruta JSON que alimenta un gráfico del lado del cliente o un manejador POST para un formulario, herede de `CustomView` y adjunte métodos con `@route`:

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

* **`path`**: Se añade a la ruta raíz de la vista. En el ejemplo anterior, `@route("/data")` se registra en `/admin/reports/data`.
* **Protección CSRF**: Toda ruta de modificación (POST, PUT, DELETE) pasa por el middleware CSRF, por lo que los formularios de sus plantillas deben incluir `{{ csrf_input(request) }}`.
* `CustomView` recurre de los argumentos del constructor a los atributos de clase, igual que hace `ModelView`, de modo que `ReportsView()` anterior funciona sin argumentos. Pase sobrescrituras, como en `ReportsView(menu_label="...")`, cuando necesite configuración por instancia.


## Control de acceso

Para restringir el acceso a una `CustomView` completa, sobrescriba el método `is_accessible(request)`. Cuando devuelve `False`, el panel elimina la vista de la barra lateral y todos los endpoints `@route` devuelven `403 Forbidden`.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Para permisos granulares, como permitir que cualquiera vea la página pero que solo los administradores hagan POST, coloque esa lógica en el manejador `@route` específico en lugar de en `is_accessible`.


> Consulte [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard) para ver una aplicación ejecutable que utiliza todos los widgets descritos en esta página: `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget` y `GridWidget`.

---

**¿Qué sigue?**

* **[Templates](../advanced/templates.md):** Personalice el layout base que extienden las plantillas de sus vistas personalizadas.
* **[Flash Messages](flash-messages.md):** Muestre retroalimentación desde sus manejadores `@route`.
* **[Actions](actions.md):** Añada acciones masivas y por fila a sus vistas de modelos.
