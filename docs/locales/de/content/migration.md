---
title: Migrationsanleitung
description: Upgrade-Anleitung für die Migration von älteren Versionen von starlette-admin
  zur neuesten Version, einschließlich Breaking Changes und neuer Features.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Migrationsanleitung

Diese Seite sammelt die Upgrade-Anleitungen zwischen den `starlette-admin`-Releases. Springen Sie zu dem Abschnitt, der zu der Version passt, von der aus Sie ein Upgrade durchführen.

---

## Von 0.17.x zu 1.0.0

Dieses Release refaktoriert die Interna von `starlette-admin` und führt eine große Menge an neuen Features ein. Während die High-Level-API weitgehend unverändert bleibt, ist das bedeutendste Update die Neuentwicklung des Renderings der Listenseite. Wir haben DataTables zugunsten einer serverseitig gerenderten Tabelle aufgegeben. Die meisten anderen Updates bestehen aus Umbenennungen oder kleinen Signaturänderungen.

Diese Anleitung deckt jeden Breaking Change in der Reihenfolge ab, in der Sie ihm am wahrscheinlichsten begegnen werden. Jeder Abschnitt vergleicht die alte API mit ihrem Ersatz. Wenn Ihre Implementierung auf den Grundlagen oder leichten Anpassungen basiert (wie einer `Admin`-Instanz, einigen `ModelView`-Subklassen, `fields` und `searchable_fields`), wird Ihre Migration wahrscheinlich auf die Abschnitte [Anforderungen](#anforderungen) und [Admin-Konstruktor](#der-admin-konstruktor) sowie einige Umbenennungen beschränkt sein.

Anpassungen der alten Listenseite erfordern die meiste Aufmerksamkeit. DataTables-Optionen und JavaScript-Renderfunktionen haben kein direktes Äquivalent und müssen auf serverseitige Templates portiert werden (siehe [Entfernung von DataTables](#entfernung-von-datatables)).

!!! tip
    Führen Sie das Upgrade Ihrer Abhängigkeiten in einem Schritt durch und starten Sie Ihre Anwendung. Die meisten entfernten oder umbenannten Attribute werfen klare Fehler beim Start, statt still zur Laufzeit zu versagen.

### Was ist neu

Über die unten beschriebenen Breaking Changes hinaus umfasst dieses Release:

* **Native Listentabellen:** DataTables wurde entfernt zugunsten einer integrierten, serverseitig gerenderten Implementierung. Der Tabellenzustand wird jetzt vollständig über die URL gesteuert, was bedeutet, dass alle Seiten-, Filter- und Sortierkonfigurationen sofort teilbar und als Lesezeichen speicherbar sind.
* **[Filter](user-guide/filters.md):** Ein verschachtelter `AND`/`OR`-Filterbuilder ersetzt den DataTables SearchBuilder. Filter werden aus den Feldtypen abgeleitet und sind vollständig in reinem Python erweiterbar. Sie können eine Filterklasse schreiben, ohne JavaScript zu benötigen.
* **[Import und serverseitiger Export](user-guide/export-import.md):** Importieren Sie Daten aus CSV, JSON, Excel und mehr mit Fehlerberichterstattung pro Zeile, zusammen mit serverseitigen Exportern (CSV, JSON, Excel, PDF usw.), die die clientseitigen DataTables-Buttons ersetzen.
* **[Events](advanced/events.md):** Abonnieren Sie Lifecycle-Hooks wie `before_create`, `after_edit_committed`, `after_login` und verschiedene Action-Events.
* **[Themes](https://jowilf.github.io/starlette-admin/advanced/custom-themes/) und [Plugins](advanced/plugins.md):** Paketieren und wiederverwenden Sie benutzerdefinierte Ästhetiken und Verhaltensweisen. Cookiecutter-Templates sind verfügbar, um Ihnen einen schnellen Einstieg zu ermöglichen.
* **[Widgets und Dashboards](user-guide/custom-views.md):** Erstellen Sie Indexseiten und benutzerdefinierte Views mit `StatWidget`, `ChartWidget`, `TableWidget` und mehr.
* **[Formularlayout](advanced/form-layout.md):** Ordnen Sie Create-/Edit-Formulare logisch an, mit Zeilen, Spalten, Fieldsets und Tabs.
* **[Inline-Bearbeitung](user-guide/inline-edit.md):** Bearbeiten Sie ein einzelnes Feld direkt von der Listenseite aus.
* **[Inline-Formulare](user-guide/inline-forms.md):** Bearbeiten Sie verwandte Modelle innerhalb eines Elternformulars mit `InlineModelView`.
* **Weitere Verbesserungen:** [Flash-Nachrichten](user-guide/flash-messages.md), [OAuth-Login](user-guide/auth.md), ein [Tortoise-ORM-Backend](integrations/tortoise.md), neue Felder (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), Validatoren auf Feldebene und Copy-to-Clipboard-Funktionalität für jedes Feld.
* **[Logging](user-guide/admin.md#debugging):** Das Package loggt jetzt intern unter dem `starlette_admin`-Namespace, standardmäßig stummgeschaltet. Übergeben Sie `Admin(debug=True)` oder rufen Sie `starlette_admin.logging.configure_logging()` auf, um Request-Routing-, Middleware- und Berechtigungsentscheidungen in der Konsole zu sehen, was besonders praktisch während der Migration ist.
* **Erweiterte Testabdeckung:** Die Test-Suite ist jetzt deutlich größer und enthält Playwright-End-to-End-Tests, die kritische Workflows im Admin-Interface validieren.
* **Schlankeres Package**: Die Größe des veröffentlichten Packages auf PyPI wurde um ca. 50 % reduziert

### Anforderungen

* **Python-Support:** Python 3.11 oder neuer wird benötigt. Der Support für Python 3.9 und 3.10 wurde eingestellt.
* **Kernabhängigkeiten:** `itsdangerous` ist jetzt eine Kernabhängigkeit, die verwendet wird, um Admin-Cookies zu signieren (CSRF-Token und Flash-Nachrichten).
* **Neue optionale Extras:**

    | Extra | Aktiviert |
    | --- | --- |
    | `starlette-admin[email]` | Serverseitige Validierung von `EmailField` via `email-validator` |
    | `starlette-admin[pdf]` | PDF-Export via `reportlab` |
    | `starlette-admin[s3]` | S3-Dateispeicher via `aiobotocore` |
    | `starlette-admin[tinymce]` | HTML-Sanitisierung von `TinyMCEEditorField` via `nh3` |
    | `starlette-admin[i18n]` | Übersetzungen via `babel` (unverändert) |

* **Beanie-Backend:** Beanie 2.0+ wird benötigt.
* **Odmantic-Backend:** Entfernt. Wenn Sie davon abhängig sind, bleiben Sie bei `starlette-admin<=0.17.1` und zeigen Sie Ihr Interesse, indem Sie [ein Issue eröffnen](https://github.com/jowilf/starlette-admin/issues); der Support kann wieder hinzugefügt werden, wenn genügend Nachfrage besteht.

### Der Admin-Konstruktor

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` wurde zu `static_dir` umbenannt.
* **Setzen Sie einen `secret_key`.** Dieser Schlüssel signiert die CSRF- und Flash-Nachricht-Cookies. Wird er weggelassen, wird ein zufälliger Schlüssel beim Start generiert (was für die Entwicklung in Ordnung ist). Allerdings werden signierte Werte bei jedem Neustart und über mehrere Worker hinweg ungültig. Übergeben Sie in der Produktion immer einen stabilen Schlüssel.
* `logo_url`, `login_logo_url` und `favicon_url` akzeptieren jetzt eine aufrufbare Funktion `(request) -> str | None`. Dies ersetzt das Branding pro Request, das zuvor von `AdminConfig` bereitgestellt wurde.
* **Neue optionale Parameter:** `theme`, `plugins`, `additional_loaders`, `import_config` und `export_config`.
* **SQLAlchemy-Besonderheiten:** Das erste Argument ist jetzt `session_provider`. Es akzeptiert eine `Engine` oder `AsyncEngine` und akzeptiert jetzt auch einen `sessionmaker` oder `async_sessionmaker`. Bestehende `Admin(engine)`-Aufrufe funktionieren weiterhin.
* `timezone_config` hat als Defaultwert `TimezoneConfig()` statt `None`. Datetimes werden jetzt standardmäßig in der lokalen Zeitzone des Betrachters angezeigt. Übergeben Sie `timezone_config=None`, um die Rohwerte beizubehalten.

### Umbenannte View-Bezeichner

Die Namenskonvention für Views ist jetzt vereinheitlicht. Aktualisieren Sie Ihre `ModelView`-Konstruktoren und Klassenattribute entsprechend:

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

Beachten Sie, dass `Link` und `DropDown` ebenfalls `menu_label` statt `label` verwenden.

### Entfernung von DataTables

Die Listenseite verwendet nicht mehr DataTables. Die Attribute, die es zuvor konfigurierten, wurden vollständig entfernt:

| Entfernt | Ersatz |
| --- | --- |
| `datatables_options` | Keiner. Die Tabelle wird serverseitig gerendert. Passen Sie sie über Templates an. |
| `search_builder` | Der neue [Filterbuilder](user-guide/filters.md), aktiviert durch `searchable_fields`. |
| `responsive_table` | Keiner. Die Tabelle behandelt Overflow nativ. |
| `save_state` | Immer aktiv. Der Listenzustand (Seite, Sortierung, Filter, Suche, sichtbare Spalten) liegt jetzt in der URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (eine Liste von Filterklassen). |
| `BaseField.render_function_key` | `BaseField.list_template` (serverseitiges Jinja-Template). |

Wenn Sie zuvor eigene JavaScript-Renderfunktionen oder DataTables-Plugins geschrieben haben, portieren Sie diese zu `list_template`-Overrides. Jedes Feld rendert seine Listenzelle jetzt direkt aus `templates/fields/list/*.html`.

### Actions

Handler für Massenaktionen erhalten jetzt ein `ActionSelection`-Objekt statt einer Liste von Primärschlüsseln. Dies unterstützt das neue Banner „alle passenden auswählen“, das jede Zeile anspricht, die zum aktuellen Filter passt, ohne sie clientseitig zu materialisieren.

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

* Methoden wie `selection.rows()`, `selection.pks()` und `selection.count()` lösen die Zielzeilen lazy auf. Dies gilt unabhängig davon, ob der Benutzer Zeilen einzeln angehakt oder alle passenden Zeilen ausgewählt hat.
* Properties wie `selection.is_select_all`, `selection.filters` und `selection.q` ermöglichen es Ihnen, die Operation als einzelne Bulk-Query nach unten zu pushen.
* Das Zurückgeben eines Erfolgsnachrichten-Strings wird durch [Flash-Nachrichten](user-guide/flash-messages.md) ersetzt.
* Handler für Zeilenaktionen behalten ihre ursprüngliche `(request, pk)`-Signatur.
* **Neue `@action`-Optionen:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` und pro-Request-`form`-Callables.

### Authentifizierung

Das Modul `starlette_admin/auth.py` ist jetzt das Package `starlette_admin.auth`. Bestehende Imports aus `starlette_admin.auth` funktionieren weiterhin, aber der Provider-Contract hat sich geändert.

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

* Die Methoden `is_authenticated`, `get_admin_user` und `get_admin_config` sind zu einer einzelnen Methode `authenticate(request) -> AdminUser | None` zusammengeführt worden. Die Rückgabe von `None` zeigt einen nicht authentifizierten Zustand an.
* Die Methoden `login` und `logout` empfangen und geben die vorbereitete `Response` nicht mehr zurück. Geben Sie `None` für den Standard-Redirect zurück oder geben Sie eine eigene `Response` zurück, um dieses Verhalten zu überschreiben.
* `AdminConfig` wurde entfernt. Behandeln Sie Titel und Logos pro Request über die aufrufbare Form von `logo_url` und `login_logo_url` auf der `Admin`-Instanz.
* Ein integrierter [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) behandelt OAuth2/OIDC-Login-Flows out of the box.
* Der Decorator `login_not_required` bleibt unverändert.

### Export und Import

Exports sind von den clientseitigen DataTables-Buttons zu serverseitigen Streaming-Endpoints umgezogen. Die Import-Funktionalität ist völlig neu, und `ExportType` existiert nicht mehr.

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

* `export_types` heißt jetzt `exporters`. Dies akzeptiert eine Liste von Formatnamen oder `BaseExporter`-Instanzen. Unterstützte Built-ins sind `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` und `pdf`. Andere Formate als `csv` oder `json` benötigen `tablib`, und PDF benötigt das `pdf`-Extra.
* `importers` akzeptiert eine Liste von Formatnamen oder `BaseImporter`-Instanzen. Unterstützte Built-ins sind `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` und `html`. Andere Formate als `csv`, `tsv` oder `json` benötigen `tablib`.
* `export_fields` (eine Include-Liste) wird durch `exclude_fields_from_export` (eine Exclude-Liste) ersetzt. Dies entspricht der Namenskonvention der anderen `exclude_fields_from_*`-Attribute.
* Felder akzeptieren außerdem individuell `exclude_from_export` und `exclude_from_import`.
* Konfigurieren Sie globale Limits mit `ExportConfig` und `ImportConfig` auf der `Admin`-Instanz. Details finden Sie in der Dokumentation zu [Export & Import](user-guide/export-import.md).

### Benutzerdefinierte Felder und Template-Overrides

Feld-Templates sind jetzt neu organisiert. Aktualisieren Sie Ihre Pfade, wenn Sie integrierte Templates überschreiben oder benutzerdefinierte Felder ausliefern:

| Vorher | Nachher |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (clientseitige Renderfunktion) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (Pfad) | Gleicher Attributname, neues Pfadpräfix `fields/form/` |

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

Neue Fähigkeiten pro Feld, die es zu erkunden gilt, sind unter anderem `validators`, `filters`, `default`, Hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard` und ein `extra`-Dictionary für beliebige Metadaten. Weitere Informationen finden Sie in der Dokumentation zu [Benutzerdefinierten Feldern](advanced/custom-fields.md).

### CustomView

Die Klasse `CustomView` akzeptiert nicht mehr `template_path` und `methods`. Erstellen Sie einfache Seiten mit [Widgets](user-guide/custom-views.md). Für Seiten, die volle Kontrolle erfordern, subclassen Sie `CustomView` und deklarieren Sie Ihre Routen direkt.

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

Der Decorator `@route` ermöglicht es zudem jeder View, zusätzliche Endpoints für Anforderungen wie JSON-Chart-Daten oder Webhooks bereitzustellen.

### Benutzerdefinierte Backends

Wenn Sie `BaseModelView` gegen eine eigene Datenquelle implementiert haben, beachten Sie den aktualisierten Datenzugriffs-Contract:

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

* Der String-typisierte `where`-Parameter ist aufgeteilt worden in `q` (für Volltextsuchbegriffe) und `filters` (ein typisierter `FilterGroup`-Baum, der vom Filterbuilder bereitgestellt wird).
* Der `order_by`-Parameter (zuvor eine Liste von `"field direction"`-Strings) heißt jetzt `sorts` und nimmt eine Liste von `(field_name, direction)`-Tupeln entgegen.
* Jedes Backend wird jetzt mit einer Filter-Registry ausgeliefert, die Feldtypen auf Filterimplementierungen abbildet. Den vollständigen Contract und ein funktionierendes Beispiel finden Sie in der Dokumentation zu [Benutzerdefinierten Backends](integrations/custom-backend.md).

### Verhaltensänderungen, die Sie prüfen sollten

* **Zeitzonen:** Datetimes werden standardmäßig in der lokalen Zeitzone des Betrachters gerendert (siehe den Hinweis zu `timezone_config` im Abschnitt Admin-Konstruktor).
* **URL-Zustand:** Der Listenzustand liegt jetzt in der URL. Als Lesezeichen gespeicherte Admin-URLs aus früheren Versionen landen auf Standard-Listenzuständen, da gespeicherte DataTables-Zustände nicht migriert werden.
* **E-Mail-Validierung:** `EmailField` validiert jetzt serverseitig, wenn `email-validator` installiert ist.
* **CSRF-Schutz:** CSRF-Schutz ist integriert und cookie-basiert. Wenn Sie das Admin-Panel zuvor mit eigener CSRF-Middleware gewrappt haben, können Sie diese sicher entfernen. Stellen Sie sicher, dass Ihr `secret_key` gesetzt ist, damit Token Server-Neustarts überleben.
* **Upload-Größe von FileField:** `FileField.max_size` hat jetzt als Defaultwert 50 MB statt unbegrenzt. Übergeben Sie `max_size=None`, um das alte unbegrenzte Verhalten wiederherzustellen, oder setzen Sie einen expliziten Wert, um das Limit zu ändern.

### Ohne Ersatz entfernt

* `AdminConfig` (siehe [Authentifizierung](#authentifizierung)).
* `datatables_options`, `responsive_table` und `save_state` (siehe [Entfernung von DataTables](#entfernung-von-datatables)).
* Das Odmantic-Backend (siehe [Anforderungen](#anforderungen)).

## Hilfe bekommen

Wenn Sie auf ein Migrationsproblem stoßen, das in dieser Anleitung nicht abgedeckt ist, [eröffnen Sie bitte ein Issue](https://github.com/jowilf/starlette-admin/issues). Fügen Sie eine minimale Reproduktion des Problems hinzu und geben Sie die Version an, von der aus Sie ein Upgrade durchführen. Der Betrieb mit [`Admin(debug=True)`](user-guide/admin.md#debugging) offenbart die Ursache oft direkt, und die resultierenden Logs sind eine großartige Ergänzung für Ihren Bericht.
