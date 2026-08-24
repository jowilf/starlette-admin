---
title: Vues et widgets personnalisés
description: Créez des widgets de tableau de bord personnalisés, des pages statiques
  et des vues autonomes dans votre panneau starlette-admin.
source_hash: 6f5147acf421066ce3c314b76d6a43207b99786736811af1cec56d47d1faf51e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/custom-views/)
<!-- translation-notice:end -->

# Vues personnalisées

Toutes les pages d'administration ne correspondent pas à un modèle de base de données. Une `CustomView` crée une page autonome dans la barre latérale que vous composez vous-même à partir de widgets intégrés, de templates personnalisés ou de routes personnalisées.

Dans la plupart des cas, vous n'avez pas besoin de créer une sous-classe. Instanciez `CustomView`, passez-lui un widget et enregistrez-le :

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

* **`menu_label`**, **`icon`** et **`path`** : contrôlent l'entrée dans la barre latérale et l'URL.
* **`widget`** : détermine ce que la page affiche. Passez une seule instance de `BaseWidget`, ou un callable (`(request) -> BaseWidget | None`) qui construit l'arborescence à chaque requête. Utilisez la forme callable lorsque la page dépend de données en temps réel, de l'utilisateur courant ou de feature flags.

Pour afficher plusieurs widgets, passez un [widget de mise en page](#widgets-de-mise-en-page) qui contient des enfants.

Ne créez une sous-classe de `CustomView` que si vous avez besoin d'endpoints personnalisés, d'un contrôle d'accès ou d'un contrôle total sur la réponse HTTP.

---

## Widgets de contenu

Les widgets de contenu affichent les données elles-mêmes. Leurs paramètres `*_callback` acceptent des callables asynchrones qui reçoivent le `Request` courant, ce qui permet à chaque widget de récupérer des données en temps réel.

Pour la signature complète du constructeur de chaque widget ci-dessous, consultez la [référence de l'API Widgets](../api/widgets.md).

### StatWidget

Une carte KPI qui affiche une métrique unique, une description facultative et un sparkline.

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

**Paramètres principaux :**

* `title` et `value_callback` : le libellé et le callable asynchrone qui renvoie la métrique.
* `description` et `color` : le texte secondaire sous la valeur. `color` accepte les tokens de couleur Tabler, tels que `"success"` et `"danger"`.
* `link` : enveloppe toute la carte dans une ancre.
* `chart_callback` : renvoie une liste `series` ApexCharts, telle que `[{"name": "Views", "data": [10, 20, 30]}]`, pour afficher un sparkline en bas de la carte.
* `countup` : anime la valeur de la métrique au chargement avec countup.js.

### ChartWidget

Un graphique ApexCharts intégré dans une carte.

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

**Paramètres principaux :**

* `chart_type` : toute chaîne valide ApexCharts, telle que `"line"`, `"bar"`, `"pie"`, `"donut"` ou `"heatmap"`.
* `series_callback` : renvoie une liste de dictionnaires pour la plupart des graphiques (`[{"name": "...", "data": [...]}]`). Pour `"pie"`, `"donut"` et `"radialBar"`, elle renvoie une liste plate de nombres.
* `options` : un dictionnaire fusionné par-dessus la configuration par défaut d'ApexCharts. Utilisez-le pour les réglages propres à chaque type, tels que `xaxis.categories` ou `labels`.

### TableWidget

Un tableau récapitulatif compact, en lecture seule.

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

Utilisez `TextWidget` pour du texte brut ou du Markdown, et `HtmlWidget` pour des blocs HTML pré-rendus.

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

!!! warning "Risque de sécurité"
    `HtmlWidget` affiche les chaînes exactement telles que vous les fournissez, sans échappement. Ne passez jamais de contenu fourni par l'utilisateur à travers lui, car cela exposerait votre administration à des injections XSS.

### DividerWidget

Affiche une règle horizontale (`<hr>`) pour séparer des sections. Il ne prend aucun paramètre.

## Widgets de mise en page

Les widgets de mise en page constituent l'ossature structurelle de vos vues personnalisées. Au lieu d'afficher des données, ils organisent, alignent et positionnent vos widgets de contenu.

!!! note
    Ces mêmes widgets de mise en page alimentent l'attribut `form_layout` de `ModelView`, ce qui vous permet également de les utiliser pour organiser les champs des formulaires de création et d'édition en colonnes, panneaux et onglets. Voir [Mises en page de formulaire](../advanced/form-layout.md).

### Lignes, colonnes et cartes

Pour construire une grille responsive, combinez ces primitives de mise en page :

* **`ColumnWidget`** : la fondation verticale. Elle empile les widgets enfants de haut en bas et sert généralement de conteneur racine pour l'arborescence de votre tableau de bord.
* **`RowWidget`** : le conteneur horizontal. Il aligne les enfants côte à côte dans une ligne flexbox. Enveloppez un enfant dans un objet `Col` pour définir sa largeur responsive via `Breakpoints`, sur une grille standard de 1 à 12. Les enfants non enveloppés se partagent équitablement la largeur disponible.
* **`CardRowWidget`** : la ligne soignée. Elle hérite de toutes les mécaniques de `RowWidget` et donne à tous les enfants des hauteurs égales. Utilisez-la lorsque vous disposez une rangée de cartes, telles que des statistiques KPI, des graphiques ou des tableaux de données.

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

Une grille responsive construite sur le système `row-cols-*` de Bootstrap. Contrairement à `Col`, `Breakpoints` définit ici le **nombre d'éléments par ligne**, et non l'étendue en colonnes.

```python
from starlette_admin import Breakpoints, GridWidget

stats_grid = GridWidget(
    children=[orders_stat, revenue_stat, users_stat],
    breakpoints=Breakpoints(default=1, md=2, lg=3),
    gutter=3,  # Bootstrap gutter scale (0-5)
)
```

### PanelWidget & TabsWidget

* **`PanelWidget`** : enveloppe les enfants dans une carte titrée que vous pouvez rendre repliable.
* **`TabsWidget`** : affiche un widget par onglet. `tabs` accepte une liste de tuples `(label, widget)`.

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


## Composer le tableau de bord d'accueil

Une `CustomView` alimente la racine par défaut de l'administration (`/admin/`). Lorsque vous n'en fournissez pas, `Admin` construit une `DefaultIndexView` qui affiche le nombre d'enregistrements et des liens vers vos modèles enregistrés.

Pour construire votre propre tableau de bord, écrivez une fonction qui assemble l'arborescence de widgets et passez-la au paramètre `index_view` de votre instance `Admin`.

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

Comme `build_dashboard` s'exécute à chaque requête, votre mise en page peut s'adapter à l'exécution. Par exemple, vous pouvez masquer des panneaux aux non-administrateurs ou remplacer des graphiques.


## Templates personnalisés

Lorsque le système de widgets n'est pas assez flexible, créez une sous-classe de `CustomView` et redécorez `index` avec `@route("")` pour afficher votre propre template Jinja au lieu du rendu par défaut des widgets :

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

`self.templates` est une instance de `Jinja2Templates` résolue par rapport à votre [répertoire de templates](../advanced/templates.md). Elle n'est disponible qu'une fois la vue montée ; ne l'appelez donc pas depuis `__init__`. Un template personnalisé étend généralement la mise en page de base de l'administration :

```html
{% extends "layout.html" %}

{% block content %}
    <h1>System status</h1>
    <p>All services operational.</p>
{% endblock %}

```

Pour afficher des widgets dans votre template personnalisé, résolvez-les et rendez-les vous-même, puis transmettez le résultat via votre propre contexte :

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
    Omettez les blocs CSS et JS uniquement si votre template n'affiche aucun widget. Sans eux, les widgets de graphique et de statistiques ne peuvent pas charger leurs dépendances, telles qu'ApexCharts.


## Ajouter des routes avec `@route`

Lorsqu'une page personnalisée a besoin de ses propres endpoints, tels qu'une route JSON qui alimente un graphique côté client ou un gestionnaire POST pour un formulaire, créez une sous-classe de `CustomView` et attachez des méthodes avec `@route` :

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

* **`path`** : ajouté au chemin racine de la vue. Dans l'exemple ci-dessus, `@route("/data")` est enregistré sur `/admin/reports/data`.
* **Protection CSRF** : chaque route modifiante (POST, PUT, DELETE) passe par le middleware CSRF ; vos formulaires doivent donc inclure `{{ csrf_input(request) }}`.
* `CustomView` retombe des arguments du constructeur sur les attributs de classe, comme le fait `ModelView` ; ainsi, `ReportsView()` ci-dessus fonctionne sans argument. Passez des valeurs de remplacement, comme dans `ReportsView(menu_label="...")`, lorsque vous avez besoin d'une configuration par instance.


## Contrôle d'accès

Pour restreindre l'accès à une `CustomView` entière, redéfinissez la méthode `is_accessible(request)`. Lorsqu'elle renvoie `False`, l'administration retire la vue de la barre latérale et chaque endpoint `@route` renvoie `403 Forbidden`.

```python
class ReportsView(CustomView):
    menu_label = "Reports"
    path = "/reports"

    def is_accessible(self, request: Request) -> bool:
        return request.state.admin_user is not None
```

Pour des permissions plus fines, par exemple permettre à tout le monde de consulter la page mais réserver le POST aux administrateurs, placez cette logique dans le gestionnaire `@route` concerné plutôt que dans `is_accessible`.


> Consultez [examples/07-dashboard](https://github.com/jowilf/starlette-admin/tree/main/examples/07-dashboard) pour une application exécutable qui utilise tous les widgets décrits sur cette page : `StatWidget`, `ChartWidget`, `TableWidget`, `TabsWidget`, `PanelWidget` et `GridWidget`.

---

**Et ensuite**

* **[Templates](../advanced/templates.md) :** personnalisez la mise en page de base que vos templates de vue personnalisée étendent.
* **[Messages flash](flash-messages.md) :** affichez les retours de vos gestionnaires `@route`.
* **[Actions](actions.md) :** ajoutez des actions groupées et des actions par ligne à vos vues de modèles.
