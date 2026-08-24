---
title: Von Flask-Admin zu starlette-admin wechseln
description: Ein direkter Migrationsleitfaden von Flask-Admin zu starlette-admin,
  der zeigt, wie Sie Ihre ModelView-Konfigurationen zum ASGI-Ökosystem übertragen.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Von Flask-Admin zu starlette-admin wechseln

starlette-admin begann als Portierung der Konzepte von Flask-Admin ins ASGI-Ökosystem, daher ist die Migration direkt. Sie leiten weiterhin eine `ModelView` ab, konfigurieren sie mit Klassenattributen und registrieren sie auf einer `Admin`-Instanz. Der Großteil der Arbeit besteht darin, Attribute umzubenennen und von Flasks implizitem Request-Kontext zum expliziten `request`-Objekt von Starlette zu wechseln.

Dieser Leitfaden bildet die Flask-Admin-API Attribut für Attribut auf ihr starlette-admin-Äquivalent ab.

## Mentales Modell

| Flask-Admin-Konzept | starlette-admin-Äquivalent |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, dann `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; die `Admin`-Instanz besitzt Engine und Datenbank-Sessions |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee-/pymongo-Backends | Beanie, Tortoise ORM, SQLModel oder ein [benutzerdefiniertes Backend](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Flask-Request-Kontext (`flask.request`) | Expliziter `request: Request`-Parameter an jedem Hook |
| Synchrone Methoden | `async`-Methoden; synchrone Methoden funktionieren weiterhin, wo Callables akzeptiert werden |

## Einrichtung

=== "Flask-Admin"

    ```python
    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    admin = Admin(app, name="My Admin", template_mode="bootstrap4")
    admin.add_view(ModelView(Post, db.session))
    ```

=== "starlette-admin"

    ```python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    app = Starlette()  # or FastAPI()
    admin = Admin(engine, title="My Admin", secret_key="change-me")
    admin.add_view(ModelView(Post))
    admin.mount_to(app)
    ```

Einen `template_mode`-Schalter gibt es nicht. Das UI verwendet [Tabler](https://tabler.io) (Bootstrap 5) und enthält einen Dark Mode. Um das Aussehen zu ändern, schreiben Sie ein benutzerdefiniertes [`BaseTheme`](../advanced/custom-themes.md) oder [überschreiben die Templates](../advanced/templates.md).

## Attribute der Listenseite

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `column_list` | `fields` | Steuert auch die Detailseite und die Formulare. Verwenden Sie die Attribute `exclude_fields_from_*` für seitenspezifische Abweichungen. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Zum Beispiel `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Gilt für die Felddefinition. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Zum Beispiel `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / Export-Formatter | Dasselbe `formatter=`-Dict, keyed nach `RequestAction` | Ein Mapping deckt Listenseite, Detailseite und Export ab. Aktionen ohne Eintrag behalten den Rohwert. |
| `column_type_formatters` | Pro Feld `formatter=`, oder eine benutzerdefinierte Feldunterklasse | Es gibt keine Registry pro Typ. Hängen Sie den Formatter an jedes Feld an oder [erstellen Sie eine Unterklasse des Feldes](../advanced/custom-fields.md), um ihn wiederzuverwenden. |
| Model-Properties oder Callables in `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) oder `getter=` an einem beliebigen Feld | Fügt virtuelle Spalten hinzu oder leitet die Wertsuche eines bestehenden Felds um, ganz ohne Unterklasse. |
| Benutzerdefinierte WTForms-Felder (Wertumwandlung) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Ersetzt das Standard-Parsing des Felds für Formular oder Import je nach `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` kombiniert mit pro Feld gesetztem `filters=` | Ersetzt die flache Filterliste durch einen [visuellen Builder](../user-guide/filters.md), der verschachtelte `AND`-/`OR`-Gruppen unterstützt. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Zum Beispiel sortiert `[("created_at", True)]` in absteigender Reihenfolge. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Benutzer wählen eine Zelle aus und bearbeiten sie direkt an Ort und Stelle. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Der Defaultwert ist `[10, 25, 50, 100]`. Benutzer wählen aus diesen Optionen. |
| `column_display_pk` | Nehmen Sie den Primärschlüssel in `fields` auf |  |
| `column_details_list` | `fields` minus `exclude_fields_from_detail` | Die Detailseite ist eingebaut. Es gibt kein `can_view_details`-Opt-in. |

## Formularattribute

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `form_columns` | `fields` minus `exclude_fields_from_create` und `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Getrennte Sichtbarkeitssteuerung pro Formular. |
| `form_overrides` | Explizite Feldinstanzen in `fields` | Zum Beispiel `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Konstruktorargumente am Feld | Zum Beispiel `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Zum Beispiel `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Zusätzliche Einträge in `fields` | Unterstützt jedes Feld, das nicht auf einer Datenbankspalte basiert, z. B. ein [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Feldattribute | Setzen Sie `read_only`, `disabled` oder `placeholder` direkt am Feld. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Ersetzt flache Regeln durch Fieldsets, Tabs und responsive Grids. |
| `create_modal` / `edit_modal` | Nicht verfügbar | Die Create- und Edit-Views werden als vollständige Seiten gerendert. |
| `on_form_prefill` | `before_edit`-Hook |  |

## Export und Import

=== "Flask-Admin"

    ```python
    class PostView(ModelView):
        can_export = True
        export_types = ["csv", "xlsx"]
        export_max_rows = 10000
    ```

=== "starlette-admin"

    ```python
    class PostView(ModelView):
        exporters = ["csv", "xlsx", "pdf"]
        importers = ["csv", "xlsx"]
        exclude_fields_from_export = ["internal_notes"]
    ```

CSV- und JSON-Export sind standardmäßig aktiviert. Zeilenlimits greifen automatisch, und das Escapen von Tabellenkalkulationsformeln ist eine Opt-in-Einstellung des Exporters. Der Import, den Flask-Admin nicht bietet, umfasst einen Vorschauschritt mit Validierung pro Zeile sowie optionale Updates bestehender Datensätze über den Primärschlüssel. Siehe [Export und Import](../user-guide/export-import.md).

## Aktionen

=== "Flask-Admin"

    ```python
    from flask_admin.actions import action


    class PostView(ModelView):
        @action("publish", "Publish", "Publish selected posts?")
        def action_publish(self, ids):
            query = Post.query.filter(Post.id.in_(ids))
            for post in query.all():
                post.published = True
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class PostView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Publish",
            confirmation="Publish selected posts?",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            for post in await selection.rows():
                post.published = True
            flash(request, "Posts published")
    ```

Der Handler erhält ein [`ActionSelection`](../user-guide/actions.md)-Objekt statt roher IDs. Er löst die Zeilen lazy auf, stellt die aktiven Filter bereit und funktioniert genauso, wenn ein Benutzer alle passenden Datensätze über Seiten hinweg auswählt. Aktionen können außerdem ein benutzerdefiniertes HTML-Formular innerhalb des Bestätigungsdialogs rendern. Für Operationen pro Zeile ersetzen [`@row_action` und `@link_row_action`](../user-guide/actions.md#row-actions) benutzerdefinierte Spalten-Formatter.

## Berechtigungen und Zugriffskontrolle

Die `can_*`-Klassenflags von Flask-Admin werden in starlette-admin zu [Methoden pro Request](../user-guide/views.md#security-and-authorization), sodass Autorisierungsentscheidungen vom angemeldeten Benutzer abhängen können.

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Blendet die View im Menü aus und blockiert den direkten Zugriff. |
| `inaccessible_callback()` | Vom Authentifizierungsflow behandelt | Unauthentifizierte Requests leiten zur Anmeldeseite weiter. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` und `can_delete` folgen demselben Muster. |
| `can_view_details` | `can_view_detail(request)` | Die Detailseite existiert standardmäßig. |
| `can_export` | `can_export(request)`, dazu `can_import(request)` |  |
| Kein Äquivalent | `can_access_field(request, field)` | Steuert die Sichtbarkeit auf Feldebene pro Benutzer. |
| Kein Äquivalent | `is_action_allowed(request, name)` | Bietet Autorisierung pro Aktion. |

Bei Flask-Admin integrieren Sie Flask-Login selbst. starlette-admin bringt einen [`AuthProvider`](../user-guide/auth.md) mit fertiger Anmeldeseite mit, und Sie implementieren die Methoden `login`, `logout` und `authenticate` gegen Ihren Benutzerspeicher. Ein `OAuthProvider` deckt OIDC-Redirect-Flows ab. Der angemeldete Benutzer ist überall als `request.state.admin_user` verfügbar.

## Lebenszyklus-Hooks für Datenbankmodelle

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, spezifisch für das SQLAlchemy-Backend |
| `handle_view_exception` | Werfen Sie `FormValidationError` oder `ActionFailed` |

Über die Hooks pro View hinaus ermöglicht Ihnen das [Event-System](../advanced/events.md), dass ein einzelner Handler jede View beobachtet. Dafür gibt es in Flask-Admin kein Äquivalent.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Benutzerdefinierte Views und die Indexseite

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Setzen Sie Seiten aus [Widgets](../user-guide/custom-views.md) zusammen, ohne Templates von Hand zu schreiben. |
| Benutzerdefiniertes Template-Rendering | `CustomView`-Unterklasse | Gibt Ihnen volle Kontrolle über Routen und Responses. |
| `AdminIndexView` | `Admin(index_view=...)` | Bauen Sie Dashboards aus `StatWidget`, `ChartWidget`, `TableWidget` und Layout-Widgets. |
| `MenuLink` | [`Link`](../user-guide/views.md#link)-View | Zum Beispiel `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Kategorien im Menü | [`DropDown`](../user-guide/views.md#sidebar-organization)-View | Gruppiert Views zusammen in der Sidebar. |
| `FileAdmin` | Nicht verfügbar | Datei- und Bildfelder mit [lokalem oder S3-Speicher](../user-guide/file-storage.md) verwalten Anhänge. Einen Server-Dateibrowser gibt es nicht. |

## Inline-Datenbankmodelle

=== "Flask-Admin"

    ```python
    class ArticleView(ModelView):
        inline_models = [Comment]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import InlineModelView, ModelView


    class CommentInline(InlineModelView):
        model = Comment
        fields = ["author", "body"]


    class ArticleView(ModelView):
        inlines = [CommentInline]
    ```

Eine explizite Klasse gibt jedem Inline-Datenbankmodell die gesamte Konfigurationsoberfläche von `ModelView`: Feldauswahl, Validierung und Unterstützung für zusammengesetzte Fremdschlüssel. Siehe [Inline-Formulare](../user-guide/inline-forms.md).

## Internationalisierung

Flask-Admin hängt von Flask-Babel und der umgebenden Flask-Umgebung ab. starlette-admin verwendet stattdessen ein Konfigurationsobjekt:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Zeitzonenbewusstes Rendern von Datums- und Zeitwerten funktioniert auf dieselbe Weise, über `TimezoneConfig`. Siehe [Internationalisierung und Zeitzonen](../user-guide/i18n.md).

## Was Sie durch den Wechsel gewinnen

* **Ein async-Stack.** Läuft nativ auf FastAPI und Starlette, mit Unterstützung für async SQLAlchemy, Beanie und Tortoise ORM. Flask-Admin ist synchron.
* **Integrierte Sicherheitsfunktionen.** CSRF-Schutz, Bereinigung von Upload-Dateinamen, Prüfung von Bildinhalten und Export-Zeilenlimits sind aktiv, sobald Sie `Admin` instanziieren, und Sie können das Escapen von Tabellenkalkulationsformeln bei den Exportern aktivieren. Siehe [Sicherheit](../user-guide/security.md).
* **Datenimport.** Ein Vorschauschritt validiert jede Zeile, bevor etwas geschrieben wird. Flask-Admin hat keine Import-Funktion.
* **Ein Dashboard-Widget-System.** Bauen Sie Indexseiten und benutzerdefinierte Views in Python, statt Templates von Hand zu schreiben.
* **Modernes Design.** Eine aktiv gepflegte Codebasis mit ausgefeiltem UI, integriertem Dark Mode und erstklassigen Type Hints.

## Woran Sie sich anpassen müssen

* **Explizite Request-Objekte.** Es gibt keinen impliziten Request-Kontext. Jeder Hook und jede Berechtigungsmethode erhält den `request` als Parameter.
* **Async-Handler.** Hooks und Aktionen sind Coroutinen, halten Sie blockierende Aufrufe daher daraus fern oder verlagern Sie diese Arbeit in einen Thread.
* **Kein `FileAdmin`.** Wenn Ihr Workflow das Durchsuchen des Server-Dateisystems erfordert, deckt starlette-admin das nicht ab.
* **Keine Create- oder Edit-Modals.** Formulare werden als vollständige Seiten statt als Popup-Modals gerendert.
