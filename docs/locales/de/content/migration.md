---
title: Migrationsleitfaden
description: Upgrade-Leitfaden für die Migration von älteren Versionen von starlette-admin
  zur neuesten Version, einschließlich Breaking Changes und neuer Funktionen.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Migrationsleitfaden

Diese Seite sammelt die Upgrade-Anleitungen zwischen den `starlette-admin`-Versionen. Springen Sie zu dem Abschnitt, der der Version entspricht, von der aus Sie ein Upgrade durchführen.

---

## Von 0.17.x zu 1.0.0

Diese Version refaktoriert die Interna von `starlette-admin` und führt eine große Anzahl neuer Features ein. Während die High-Level-API weitgehend unverändert bleibt, ist das bedeutendste Update die Neuentwicklung des Renderings der Listenseite. Wir haben DataTables zugunsten einer serverseitig gerenderten Tabelle aufgegeben. Die meisten anderen Updates bestehen aus Umbenennungen oder kleineren Signaturänderungen.

Dieser Leitfaden behandelt alle Breaking Changes in der Reihenfolge, in der Sie ihnen höchstwahrscheinlich begegnen. Jeder Abschnitt vergleicht die alte API mit ihrem Ersatz. Wenn Ihre Implementierung auf den Grundlagen oder leichten Anpassungen beruht (wie einer `Admin`-Instanz, einigen `ModelView`-Unterklassen, `fields` und `searchable_fields`), wird Ihre Migration wahrscheinlich auf die Abschnitte [Voraussetzungen](#requirements) und [Admin-Konstruktor](#the-admin-constructor) sowie einige Umbenennungen beschränkt sein.

Anpassungen der alten Listenseite erfordern die meiste Aufmerksamkeit. DataTables-Optionen und JavaScript-Renderfunktionen haben kein direktes Äquivalent und müssen auf serverseitige Templates portiert werden (siehe [Entfernung von DataTables](#datatables-removal)).

!!! tip
    Aktualisieren Sie Ihre Abhängigkeiten in einem Schritt und starten Sie Ihre Anwendung. Die meisten entfernten oder umbenannten Attribute lösen klare Fehler beim Start aus, statt zur Laufzeit still zu versagen.

### Was ist neu

Über die unten beschriebenen Breaking Changes hinaus umfasst diese Version:

* **Native Listentabellen:** DataTables wurde entfernt und durch eine integrierte, serverseitig gerenderte Implementierung ersetzt. Der Tabellenzustand wird nun vollständig über die URL gesteuert, was bedeutet, dass alle Seiten-, Filter- und Sortierkonfigurationen sofort teilbar und als Lesezeichen speicherbar sind.
* **[Filter](user-guide/filters.md):** Ein verschachtelter `AND`/`OR`-Filterbuilder ersetzt den DataTables SearchBuilder. Filter werden aus den Feldtypen abgeleitet und sind vollständig in reinem Python erweiterbar. Sie können eine Filterklasse schreiben, ohne JavaScript zu benötigen.
* **[Import und serverseitiger Export](user-guide/export-import.md):** Importieren Sie Daten aus CSV, JSON, Excel und mehr mit Fehlerberichterstattung pro Zeile, zusammen mit serverseitigen Exportern (CSV, JSON, Excel, PDF usw.), die die clientseitigen DataTables-Buttons ersetzen.
* **[Events](advanced/events.md):** Abonnieren Sie Lifecycle-Hooks wie `before_create`, `after_edit_committed`, `after_login` und verschiedene Action-Events.
* **[Themes](advanced/custom-themes.md) und [Plugins](advanced/plugins.md):** Paketieren und wiederverwenden Sie eigene Optiken und Verhaltensweisen. Cookiecutter-Templates stehen zur Verfügung, um Ihnen einen schnellen Einstieg zu ermöglichen.
* **[Widgets und Dashboards](user-guide/custom-views.md):** Erstellen Sie Indexseiten und Custom Views mit `StatWidget`, `ChartWidget`, `TableWidget` und mehr.
* **[Formularlayout](advanced/form-layout.md):** Ordnen Sie Create-/Edit-Formulare logisch anhand von Zeilen, Spalten, Fieldsets und Tabs an.
* **[Inline-Bearbeitung](user-guide/inline-edit.md):** Bearbeiten Sie ein einzelnes Feld direkt über die Listenseite.
* **[Inline-Formulare](user-guide/inline-forms.md):** Bearbeiten Sie verwandte Modelle innerhalb eines übergeordneten Formulars mit `InlineModelView`.
* **Weitere Verbesserungen:** [Flash-Nachrichten](user-guide/flash-messages.md), [OAuth-Login](user-guide/auth.md), ein [Tortoise-ORM-Backend](integrations/tortoise.md), neue Felder (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), Feld-Validatoren (`validators`) sowie Copy-to-Clipboard-Funktionalität für jedes Feld.
* **[Logging](user-guide/admin.md#debugging):** Das Paket protokolliert nun intern unter dem Namespace `starlette_admin`, standardmäßig stummgeschaltet. Übergeben Sie `Admin(debug=True)` oder rufen Sie `starlette_admin.logging.configure_logging()` auf, um Request-Routing-, Middleware- und Berechtigungsentscheidungen in der Konsole zu sehen – besonders praktisch während der Migration.
* **Erweiterte Testabdeckung:** Die Testsuite ist nun deutlich größer und enthält Playwright-End-to-End-Tests, die kritische Workflows über das Admin-Interface hinweg validieren.
* **Schlankeres Paket:** Die Größe des veröffentlichten Pakets auf PyPI wurde um ca. 50 % reduziert.

### Voraussetzungen {#requirements}

* **Python-Unterstützung:** Python 3.11 oder neuer wird benötigt. Die Unterstützung für Python 3.9 und 3.10 wurde eingestellt.
* **Kernabhängigkeiten:** `itsdangerous` ist nun eine Kernabhängigkeit, die zum Signieren der Admin-Cookies verwendet wird (CSRF-Token und Flash-Nachrichten).
* **Neue optionale Extras:**

    | Extra | Aktiviert |
    | --- | --- |
    | `starlette-admin[email]` | Serverseitige Validierung von `EmailField` via `email-validator` |
    | `starlette-admin[pdf]` | PDF-Export via `reportlab` |
    | `starlette-admin[s3]` | S3-Dateispeicherung via `aiobotocore` |
    | `starlette-admin[tinymce]` | HTML-Sanitisierung von `TinyMCEEditorField` via `nh3` |
    | `starlette-admin[i18n]` | Übersetzungen via `babel` (unverändert) |

* **Beanie-Backend:** Beanie 2.0+ wird benötigt.
* **Odmantic-Backend:** Entfernt. Wenn Sie darauf angewiesen sind, bleiben Sie bei `starlette-admin<=0.17.1` und zeigen Sie Ihr Interesse, indem Sie [ein Issue eröffnen](https://github.com/jowilf/starlette-admin/issues); die Unterstützung kann wieder hinzugefügt werden, wenn ausreichend Nachfrage besteht.

### Der Admin-Konstruktor {#the-admin-constructor}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` wurde in `static_dir` umbenannt.
* **Setzen Sie einen `secret_key`.** Dieser Schlüssel signiert die CSRF- und Flash-Nachrichten-Cookies. Wird er weggelassen, wird beim Start ein zufälliger Schlüssel generiert (was für die Entwicklung unproblematisch ist). Signierte Werte werden jedoch bei jedem Neustart und über mehrere Worker hinweg ungültig. Übergeben Sie in der Produktion immer einen stabilen Secret.
* `logo_url`, `login_logo_url` und `favicon_url` akzeptieren nun ein Callable `(request) -> str | None`. Dies ersetzt das zuvor von `AdminConfig` bereitgestellte Branding pro Request.
* **Neue optionale Parameter:** `theme`, `plugins`, `additional_loaders`, `import_config` und `export_config`.
* **SQLAlchemy-Besonderheiten:** Das erste Argument ist nun `session_provider`. Es akzeptiert ein `Engine` oder `AsyncEngine` und akzeptiert nun auch einen `sessionmaker` oder `async_sessionmaker`. Bestehende `Admin(engine)`-Aufrufe funktionieren weiterhin.
* `timezone_config` hat standardmäßig den Wert `TimezoneConfig()` statt `None`. Datums- und Zeitangaben werden standardmäßig in der lokalen Zeitzone des Betrachters angezeigt. Übergeben Sie `timezone_config=None`, um Rohwerte beizubehalten.

### Umbenannte View-Bezeichner

Die Namenskonvention für Views ist nun vereinheitlicht. Passen Sie Ihre `ModelView`-Konstruktoren und Klassenattribute entsprechend an:

| Vorher | Nachher |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

Beachten Sie, dass auch `Link` und `DropDown` `menu_label` statt `label` verwenden.

### Entfernung von DataTables {#datatables-removal}

Die Listenseite verwendet keine DataTables mehr. Die Attribute, die diese zuvor konfiguriert haben, wurden vollständig entfernt:

| Entfernt | Ersatz |
| --- | --- |
| `datatables_options` | Keiner. Die Tabelle wird serverseitig gerendert. Anpassung über Templates. |
| `search_builder` | Der neue [Filterbuilder](user-guide/filters.md), aktiviert durch `searchable_fields`. |
| `responsive_table` | Keiner. Die Tabelle behandelt Overflow nativ. |
| `save_state` | Immer aktiv. Der Listenstatus (Seite, Sortierung, Filter, Suche, sichtbare Spalten) liegt nun in der URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (eine Liste von Filterklassen). |
| `BaseField.render_function_key` | `BaseField.list_template` (serverseitiges Jinja-Template). |

Wenn Sie bisher eigene JavaScript-Renderfunktionen oder DataTables-Plugins geschrieben haben, portieren Sie diese auf `list_template`-Overrides. Jedes Feld rendert seine Listenzelle nun direkt aus `templates/fields/list/*.html`.

### Actions

Batch-Action-Handler erhalten nun ein `ActionSelection`-Objekt statt einer Liste von Primärschlüsseln. Dies unterstützt das neue Banner „alle passenden auswählen“, das jede Zeile anspricht, die dem aktuellen Filter entspricht, ohne sie clientseitig zu materialisieren.

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* Methoden wie `selection.rows()`, `selection.pks()` und `selection.count()` lösen die Zielzeilen träge (lazy) auf. Dies gilt unabhängig davon, ob der Benutzer Zeilen einzeln angekreuzt oder alle passenden Zeilen ausgewählt hat.
* Eigenschaften wie `selection.is_select_all`, `selection.filters` und `selection.q` ermöglichen es Ihnen, die Operation als einzelne Bulk-Abfrage nach unten durchzureichen.
* Die Rückgabe eines Erfolgsnachrichten-Strings wird durch [Flash-Nachrichten](user-guide/flash-messages.md) ersetzt.
* Row-Action-Handler behalten ihre ursprüngliche `(request, pk)`-Signatur bei.
* **Neue `@action`-Optionen:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` sowie pro-Request-`form`-Callables.

### Authentifizierung {#authentication}

Das Modul `starlette_admin/auth.py` ist nun das Paket `starlette_admin.auth`. Bestehende Imports aus `starlette_admin.auth` funktionieren weiterhin, aber der Provider-Vertrag hat sich geändert.

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* Die Methoden `is_authenticated`, `get_admin_user` und `get_admin_config` sind in einer einzigen Methode `authenticate(request) -> AdminUser | None` zusammengefasst. Die Rückgabe von `None` signalisiert einen nicht authentifizierten Zustand.
* Die Methoden `login` und `logout` empfangen und geben die vorbereitete `response` nicht mehr zurück. Geben Sie `None` für die Standard-Weiterleitung zurück oder geben Sie ein eigenes `Response` zurück, um dieses Verhalten zu überschreiben.
* `AdminConfig` wurde entfernt. Behandeln Sie Titel und Logos pro Request über die Callable-Form von `logo_url` und `login_logo_url` auf der `Admin`-Instanz.
* Ein integrierter [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) verarbeitet OAuth2/OIDC-Login-Flows out of the box.
* Der Decorator `login_not_required` bleibt unverändert.

### Export und Import

Exporte wurden von clientseitigen DataTables-Buttons zu serverseitigen Streaming-Endpoints verlagert. Die Importfunktionalität ist vollständig neu, und `ExportType` existiert nicht mehr.

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` heißt nun `exporters`. Es akzeptiert eine Liste von Formatnamen oder `BaseExporter`-Instanzen. Zu den unterstützten Built-ins gehören `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` und `pdf`. Andere Formate als `csv` oder `json` benötigen `tablib`, PDF benötigt das Extra `pdf`.
* `importers` akzeptiert eine Liste von Formatnamen oder `BaseImporter`-Instanzen. Zu den unterstützten Built-ins gehören `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` und `html`. Andere Formate als `csv`, `tsv` oder `json` benötigen `tablib`.
* `export_fields` (eine Include-Liste) wird durch `exclude_fields_from_export` (eine Exclude-Liste) ersetzt. Dies entspricht der Namenskonvention der anderen `exclude_fields_from_*`-Attribute.
* Felder akzeptieren zudem einzeln `exclude_from_export` und `exclude_from_import`.
* Konfigurieren Sie globale Limits mit `ExportConfig` und `ImportConfig` auf der `Admin`-Instanz. Details finden Sie in der Dokumentation zu [Export & Import](user-guide/export-import.md).

### Benutzerdefinierte Felder und Template-Overrides

Feld-Templates wurden neu organisiert. Passen Sie Ihre Pfade an, wenn Sie eingebaute Templates überschreiben oder eigene Felder mitliefern:

| Vorher | Nachher |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (clientseitige Renderfunktion) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (Pfad) | Gleiches Attribut, neues Pfadpräfix `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

Neue Fähigkeiten pro Feld, die es zu entdecken gilt, umfassen `validators`, `filters`, `default`, Hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard` sowie ein `extra`-Dictionary für beliebige Metadaten. Weitere Informationen finden Sie in der Dokumentation zu [Custom Fields](advanced/custom-fields.md).

### CustomView

Die Klasse `CustomView` akzeptiert `template_path` und `methods` nicht mehr. Erstellen Sie einfache Seiten mit [Widgets](user-guide/custom-views.md). Für Seiten, die volle Kontrolle erfordern, subclassen Sie `CustomView` und deklarieren Sie Ihre Routen direkt.

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

Der Decorator `@route` ermöglicht außerdem jeder View, zusätzliche Endpoints bereitzustellen – etwa für JSON-Chart-Daten oder Webhooks.

### Benutzerdefinierte Backends

Wenn Sie `BaseModelView` gegen eine eigene Datenquelle implementiert haben, beachten Sie den aktualisierten Datenzugriffsvertrag:

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* Der String-typisierte Parameter `where` wurde aufgeteilt in `q` (für Volltext-Suchbegriffe) und `filters` (ein typisierter `FilterGroup`-Baum, der vom Filterbuilder bereitgestellt wird).
* Der Parameter `order_by` (zuvor eine Liste von `"field direction"`-Strings) heißt nun `sorts` und nimmt eine Liste von `(field_name, direction)`-Tupeln entgegen.
* Jedes Backend liefert nun eine Filter-Registry mit, die Feldtypen auf Filterimplementierungen abbildet. Den vollständigen Vertrag und ein funktionierendes Beispiel finden Sie in der Dokumentation zum [Custom Backend](integrations/custom-backend.md).

### Zu prüfende Verhaltensänderungen

* **Zeitzonen:** Datums- und Zeitangaben werden standardmäßig in der lokalen Zeitzone des Betrachters gerendert (siehe den Hinweis zu `timezone_config` im Abschnitt Admin-Konstruktor).
* **URL-Zustand:** Der Listenstatus liegt nun in der URL. Als Lesezeichen gespeicherte Admin-URLs aus früheren Versionen landen auf Standard-Listenzuständen, da gespeicherte DataTables-Zustände nicht migriert werden.
* **E-Mail-Validierung:** `EmailField` validiert nun serverseitig, wenn `email-validator` installiert ist.
* **CSRF-Schutz:** CSRF-Schutz ist eingebaut und cookie-basiert. Wenn Sie das Admin zuvor mit eigener CSRF-Middleware umschlossen haben, können Sie diese gefahrlos entfernen. Stellen Sie sicher, dass Ihr `secret_key` gesetzt ist, damit Token Server-Neustarts überleben.
* **Upload-Größe von FileField:** `FileField.max_size` hat nun standardmäßig 50 MB statt unbegrenzt. Übergeben Sie `max_size=None`, um das alte unbegrenzte Verhalten wiederherzustellen, oder setzen Sie einen expliziten Wert, um das Limit zu ändern.

### Ohne Ersatz entfernt

* `AdminConfig` (siehe [Authentifizierung](#authentication)).
* `datatables_options`, `responsive_table` und `save_state` (siehe [Entfernung von DataTables](#datatables-removal)).
* Das Odmantic-Backend (siehe [Voraussetzungen](#requirements)).

## Hilfe erhalten

Sollten Sie auf ein Migrationsproblem stoßen, das in diesem Leitfaden nicht behandelt wird, öffnen Sie bitte [ein Issue](https://github.com/jowilf/starlette-admin/issues). Fügen Sie eine minimale Reproduktion des Problems bei und geben Sie die Version an, von der aus Sie ein Upgrade durchführen. Der Betrieb mit [`Admin(debug=True)`](user-guide/admin.md#debugging) offenbart die Ursache oft direkt, und die resultierenden Logs sind eine wertvolle Ergänzung für Ihren Bericht.
