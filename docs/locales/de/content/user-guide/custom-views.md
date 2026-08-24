---
title: Benutzerdefinierte Views & Widgets
description: Erstellen Sie benutzerdefinierte Dashboard-Widgets, statische Seiten
  und eigenständige Views innerhalb Ihres starlette-admin Panels.
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# Benutzerdefinierte Views

Nicht jede Admin-Seite lässt sich auf ein Datenbankmodell abbilden. Eine `CustomView` erstellt eine eigenständige Seite in der Sidebar, die Sie selbst aus integrierten Widgets, benutzerdefinierten Templates oder benutzerdefinierten Routen zusammenstellen.

In den meisten Fällen müssen Sie nichts subclassen. Instanziieren Sie `CustomView`, übergeben Sie ein Widget und registrieren Sie es:

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

* **`menu_label`**, **`icon`** und **`path`**: Steuern den Sidebar-Eintrag und die URL.
* **`widget`**: Bestimmt, was die Seite rendert. Übergeben Sie eine einzelne `BaseWidget`-Instanz oder ein Callable (`(request) -> BaseWidget | None`), das den Baum pro Request aufbaut. Verwenden Sie die Callable-Form, wenn die Seite von Live-Daten, dem aktuellen Benutzer oder Feature-Flags abhängt.

Um mehr als ein Widget anzuzeigen, übergeben Sie ein [Layout-Widget](#layout-widgets), das Kinder enthält.

Subclassen Sie `CustomView` nur dann, wenn Sie benutzerdefinierte Endpoints, Zugriffskontrolle oder volle Kontrolle über die Response benötigen.

---

## Inhalts-Widgets

Inhalts-Widgets rendern die Daten selbst. Ihre `*_callback`-Parameter akzeptieren async Callables, die den aktuellen `Request` erhalten, sodass jedes Widget Live-Daten abrufen kann.

Die vollständige Konstruktorsignatur jedes Widgets unten finden Sie in der [Widgets-API-Referenz](../api/widgets.md).

### StatWidget

Eine KPI-Karte, die eine einzelne Metrik, eine optionale Beschreibung und einen Sparkline anzeigt.

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

**Wichtige Parameter:**

* `title` und `value_callback`: Das Label und das async Callable, das die Metrik zurückgibt.
* `description` und `color`: Der sekundäre Text unterhalb des Werts. `color` akzeptiert Tabler-Farb-Tokens, wie `"success"` und `"danger"`.
* `link`: Wrappt die gesamte Karte in einem Anker.
* `chart_callback`: Gibt eine ApexCharts-`series`-Liste zurück, wie `[{"name": "Views", "data": [10, 20, 30]}]`, um einen Sparkline am unteren Rand der Karte zu rendern.
* `countup`: Animiert den Metrikwert beim Laden mit countup.js.

### ChartWidget

Ein ApexCharts-Diagramm innerhalb einer Karte.

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

**Wichtige Parameter:**

* `chart_type`: Jeder gültige ApexCharts-String, wie `"line"`, `"bar"`, `"pie"`, `"donut"` oder `"heatmap"`.
* `series_callback`: Gibt für die meisten Diagramme eine Liste von Dictionaries zurück (`[{"name": "...", "data": [...]}]`). Für `"pie"`, `"donut"` und `"radialBar"` gibt sie eine flache Liste von Zahlen zurück.
* `options`: Ein Dictionary, das über die Defaultkonfiguration von ApexCharts gemerged wird. Verwenden Sie es für typspezifische Einstellungen wie `xaxis.categories` oder `labels`.

### TableWidget

Eine kompakte, schreibgeschützte Übersichtstabelle.

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

Verwenden Sie `TextWidget` für reinen Text oder Markdown und `HtmlWidget` für vorgerenderte HTML-Blöcke.

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

!!! warning "Sicherheitsrisiko"
    `HtmlWidget` rendert Strings exakt so, wie Sie sie bereitstellen, ohne Escaping. Übergeben Sie niemals vom Benutzer bereitgestellte Inhalte daran, da dies Ihr Admin-Panel XSS-Injektionen aussetzt.

### DividerWidget

Rendert eine horizontale Linie (`<hr>`), um Abschnitte zu trennen. Es nimmt keine Parameter entgegen.

## Layout-Widgets

Layout-Widgets sind das strukturelle Grundgerüst Ihrer benutzerdefinierten Views. Statt Daten zu rendern, organisieren, ausrichten und positionieren sie Ihre Inhalts-Widgets.

!!! note
    Dieselben Layout-Widgets treiben auch das Attribut `form_layout` auf `ModelView` an, sodass Sie sie auch verwenden können, um Formularfelder zum Erstellen und Bearbeiten in Spalten, Panels und Tabs anzuordnen. Siehe [Formularlayouts](../advanced/form-layout.md).

### Zeilen, Spalten und Karten

Um ein responsives Grid zu bauen, kombinieren Sie diese Layout-Primitiven:

* **`ColumnWidget`**: Das vertikale Fundament. Es stapelt Kind-Widgets von oben nach unten und dient üblicherweise als Root-Container Ihres Dashboard-Baums.
* **`RowWidget`**: Der horizontale Container. Er richtet Kinder nebeneinander in einer Flexbox-Zeile aus. Wrappen Sie ein Kind in ein `Col`-Objekt, um seine responsive Breite über `Breakpoints` auf einem Standardraster von 1–12 festzulegen. Nicht gewrappte Kinder teilen sich die verfügbare Breite gleichmäßig.
* **`CardRowWidget`**: Die polierte Zeile. Sie erbt jede `RowWidget`-Mechanik und gibt allen Kindern gleiche Höhen. Verwenden Sie sie, wenn Sie eine Reihe von Karten anordnen, wie KPI-Statistiken, Diagramme oder Datentabellen.

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

Ein responsives Grid, das auf Bootstraps `row-cols-*`-System aufbaut. Anders als bei `Col` legt `Breakpoints` hier die **Anzahl der Elemente pro Zeile** fest, nicht die Spaltenspanne.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`**: Wrappt Kinder in einer betitelten Karte, die Sie einklappbar machen können.
* **`TabsWidget`**: Rendert ein Widget pro Tab. `tabs` akzeptiert eine Liste von `(label, widget)`-Tupeln.

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


## Das Home-Dashboard zusammenstellen

Eine `CustomView` treibt das Default-Admin-Root (`/admin/`) an. Wenn Sie keine bereitstellen, baut `Admin` eine `DefaultIndexView`, die Record-Anzahlen und Links für Ihre registrierten Modelle anzeigt.

Um Ihr eigenes Dashboard zu bauen, schreiben Sie eine Funktion, die den Widget-Baum zusammensetzt, und übergeben Sie sie an den Parameter `index_view` Ihrer `Admin`-Instanz.

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

Da `build_dashboard` bei jedem Request ausgeführt wird, kann sich Ihr Layout zur Laufzeit anpassen. So können Sie beispielsweise Panels für Nicht-Admins ausblenden oder Diagramme austauschen.


## Benutzerdefinierte Templates

Wenn das Widget-System nicht flexibel genug ist, subclassen Sie `CustomView` und dekorieren Sie `index` erneut mit `@route("")`, um Ihr eigenes Jinja-Template statt des Default-Widget-Renderings zu rendern:

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

`self.templates` ist eine `Jinja2Templates`-Instanz, die gegen Ihr [Templates-Verzeichnis](../advanced/templates.md) aufgelöst wird. Sie ist erst verfügbar, nachdem die View gemountet wurde, rufen Sie sie also nicht aus `__init__` auf. Ein benutzerdefiniertes Template erweitert üblicherweise das Basis-Admin-Layout:

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Um Widgets innerhalb Ihres benutzerdefinierten Templates anzuzeigen, lösen und rendern Sie sie selbst und übergeben dann das Ergebnis durch Ihren eigenen Kontext:

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
    Lassen Sie die CSS- und JS-Blöcke nur weg, wenn Ihr Template keine Widgets rendert. Ohne diese Blöcke können Diagramm- und Stat-Widgets ihre Abhängigkeiten nicht laden, wie ApexCharts.


## Routen mit `@route` hinzufügen

Wenn eine benutzerdefinierte Seite eigene Endpoints benötigt, wie eine JSON-Route, die ein clientseitiges Diagramm speist, oder einen POST-Handler für ein Formular, subclassen Sie `CustomView` und hängen Sie Methoden mit `@route` an:

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

* **`path`**: Wird an den Root-Pfad der View angehängt. Im obigen Beispiel registriert `@route("/data")` unter `/admin/reports/data`.
* **CSRF-Schutz**: Jede mutierende Route (POST, PUT, DELETE) läuft durch die CSRF-Middleware, daher müssen Formulare in Ihren Templates `{{ csrf_input(request) }}` enthalten.
* `CustomView` fällt von Konstruktorargumenten auf Klassenattribute zurück, so wie es `ModelView` tut, daher funktioniert `ReportsView()` oben ohne Argumente. Übergeben Sie Overrides, wie in `ReportsView(menu_label="...")`, wenn Sie eine Konfiguration pro Instanz benötigen.


## Zugriffskontrolle

Um eine gesamte `CustomView` zu sperren, überschreiben Sie die Methode `is_accessible(request)`. Wenn sie `False` zurückgibt, entfernt das Admin-Panel die View aus der Sidebar, und jeder `@route`-Endpoint gibt `403 Forbidden` zurück.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Für granulare Berechtigungen, etwa wenn jeder die Seite ansehen darf, aber nur Admins POST-Anfragen senden dürfen, platzieren Sie diese Logik im jeweiligen `@route`-Handler statt in `is_accessible`.


> Sehen Sie sich [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard) für eine lauffähige App an, die jedes auf dieser Seite beschriebene Widget verwendet: `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget` und `GridWidget`.

---

**Wie geht es weiter?**

* **[Templates](../advanced/templates.md):** Passen Sie das Basislayout an, das Ihre benutzerdefinierten View-Templates erweitern.
* **[Flash-Nachrichten](flash-messages.md):** Geben Sie Feedback aus Ihren `@route`-Handlern aus.
* **[Aktionen](actions.md):** Fügen Sie Massen- und Zeilenaktionen zu Ihren Modell-Views hinzu.
