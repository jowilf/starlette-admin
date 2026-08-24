---
title: Von Flask-Admin kommend
description: Ein direkter Migrationsleitfaden von Flask-Admin zu starlette-admin,
  der zeigt, wie Sie Ihre ModelView-Konfigurationen ins ASGI-Ökosystem überführen.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Von Flask-Admin kommend

starlette-admin entstand als Portierung der Konzepte von Flask-Admin ins ASGI-Ökosystem, daher ist die Migration unkompliziert. Sie leiten weiterhin eine Klasse von `ModelView` ab, konfigurieren sie über Klassenattribute und registrieren sie auf einer `Admin`-Instanz. Der Großteil der Arbeit besteht darin, Attribute umzubenennen und vom impliziten Request-Kontext von Flask zum expliziten `request`-Objekt von Starlette zu wechseln.

Dieser Leitfaden ordnet die Flask-Admin-API Attribut für Attribut ihrem starlette-admin-Pendant zu.

## Mentales Modell

| Flask-Admin-Konzept | starlette-admin-Pendant |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, anschließend `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; die `Admin`-Instanz verwaltet Engine und Datenbank-Sessions |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee-/pymongo-Backends | Beanie, Tortoise ORM, SQLModel oder ein [eigenes Backend](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Flask-Request-Kontext (`flask.request`) | Expliziter Parameter `request: Request` in jedem Hook |
| Synchrone Methoden | `async`-Methoden; synchron funktioniert weiterhin dort, wo Callables akzeptiert werden |

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

Einen `template_mode`-Schalter gibt es nicht. Die Benutzeroberfläche verwendet [Tabler](https://tabler.io) (Bootstrap 5) und bietet einen Dark Mode. Um das Erscheinungsbild anzupassen, schreiben Sie ein eigenes [`BaseTheme`](../advanced/custom-themes.md) oder [überschreiben Sie die Templates](../advanced/templates.md).

## Attribute der Listenseite

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `column_list` | `fields` | Steuert auch die Detail- und Formularseiten. Verwenden Sie die Attribute `exclude_fields_from_*` für seitenspezifische Abweichungen. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Zum Beispiel `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Gilt für die Felddefinition. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Zum Beispiel `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / Export-Formatter | Dieselbe `formatter=`-Zuordnung, geschlüsselt nach `RequestAction` | Eine Zuordnung deckt Listen-, Detail- und Exportformatierung ab. Aktionen ohne Eintrag behalten den Rohwert. |
| `column_type_formatters` | Pro Feld `formatter=` oder eine eigene Feldsubclass | Eine Registry pro Typ gibt es nicht. Hängen Sie den Formatter an jedes Feld an oder [leiten Sie eine eigene Feldklasse ab](../advanced/custom-fields.md) und verwenden Sie diese wieder. |
| Model-Properties oder Callables in `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) oder `getter=` an jedem Feld | Fügt virtuelle Spalten hinzu oder lenkt den Wertabruf eines bestehenden Felds um – ganz ohne Subklasse. |
| Eigene WTForms-Felder (Wertumwandlung) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Ersetzt das Standard-Parsing des Felds für Formular bzw. Import je nach `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` kombiniert mit pro Feld gesetztem `filters=` | Ersetzt die flache Filterliste durch einen [visuellen Builder](../user-guide/filters.md), der verschachtelte `AND`-/`OR`-Gruppen unterstützt. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Zum Beispiel sortiert `[("created_at", True)]` in absteigender Reihenfolge. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Benutzer wählen eine Zelle aus und bearbeiten sie direkt an Ort und Stelle. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Standardmäßig `[10, 25, 50, 100]`. Benutzer wählen aus diesen Optionen. |
| `column_display_pk` | Den Primärschlüssel in `fields` aufnehmen |  |
| `column_details_list` | `fields` minus `exclude_fields_from_detail` | Die Detailseite ist eingebaut. Es gibt kein Opt-in über `can_view_details`. |

## Formularattribute

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `form_columns` | `fields` minus `exclude_fields_from_create` und `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Getrennte Sichtbarkeitssteuerung pro Formular. |
| `form_overrides` | Explizite Feldinstanzen in `fields` | Zum Beispiel `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Konstruktorargumente am Feld | Zum Beispiel `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Zum Beispiel `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Zusätzliche Einträge in `fields` | Unterstützt jedes Feld ohne zugrunde liegende Datenbankspalte, etwa ein [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Feldattribute | Setzen Sie `read_only`, `disabled` oder `placeholder` direkt am Feld. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Ersetzt flache Regeln durch Fieldsets, Tabs und responsive Grids. |
| `create_modal` / `edit_modal` | Nicht verfügbar | Die Views zum Erstellen und Bearbeiten werden als vollständige Seiten gerendert. |
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

Der Export als CSV und JSON ist standardmäßig aktiviert. Zeilenbegrenzungen greifen automatisch, und das Escaping von Tabellenkalkulationsformeln ist eine optionale Exporter-Einstellung. Der Import, den Flask-Admin nicht bietet, umfasst einen Vorschauschritt mit Validierung jeder einzelnen Zeile sowie optionalen Aktualisierungen bestehender Datensätze über den Primärschlüssel. Siehe [Export und Import](../user-guide/export-import.md).

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

Der Handler erhält ein [`ActionSelection`](../user-guide/actions.md)-Objekt statt roher IDs. Es löst die Zeilen lazy auf, stellt die aktiven Filter bereit und funktioniert gleichermaßen, wenn ein Benutzer alle passenden Datensätze seitenübergreifend auswählt. Aktionen können zudem ein eigenes HTML-Formular im Bestätigungsdialog rendern. Für Operationen pro Zeile ersetzen [`@row_action` und `@link_row_action`](../user-guide/actions.md#row-actions) benutzerdefinierte Spalten-Formatter.

## Berechtigungen und Zugriffskontrolle

Die `can_*`-Klassenflags von Flask-Admin werden in starlette-admin zu [Methoden pro Request](../user-guide/views.md#security-and-authorization), sodass Autorisierungsentscheidungen vom angemeldeten Benutzer abhängen können.

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Blendet den View im Menü aus und blockiert den direkten Zugriff. |
| `inaccessible_callback()` | Wird vom Authentifizierungsablauf behandelt | Nicht authentifizierte Requests werden zur Anmeldeseite weitergeleitet. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` und `can_delete` folgen demselben Muster. |
| `can_view_details` | `can_view_detail(request)` | Die Detailseite existiert standardmäßig. |
| `can_export` | `can_export(request)`, dazu `can_import(request)` |  |
| Kein Äquivalent | `can_access_field(request, field)` | Steuert die Sichtbarkeit auf Feldebene pro Benutzer. |
| Kein Äquivalent | `is_action_allowed(request, name)` | Bietet Autorisierung pro Aktion. |

Bei Flask-Admin integrieren Sie Flask-Login selbst. starlette-admin liefert einen [`AuthProvider`](../user-guide/auth.md) mit fertiger Anmeldeseite mit; die Methoden `login`, `logout` und `authenticate` implementieren Sie gegen Ihren Benutzerspeicher. Ein `OAuthProvider` deckt OIDC-Redirect-Flows ab. Der angemeldete Benutzer ist überall als `request.state.admin_user` verfügbar.

## Lifecycle-Hooks für Modelle

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, spezifisch für das SQLAlchemy-Backend |
| `handle_view_exception` | Auslösen von `FormValidationError` oder `ActionFailed` |

Über die Hooks pro View hinaus ermöglicht das [Event-System](../advanced/events.md) einem einzigen Handler, jeden View zu beobachten. Dafür gibt es in Flask-Admin kein Äquivalent.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Eigene Views und die Indexseite

| Flask-Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Setzen Sie Seiten aus [Widgets](../user-guide/custom-views.md) zusammen, ohne rohe Templates zu schreiben. |
| Eigenes Template-Rendering | Subclass von `CustomView` | Gibt Ihnen volle Kontrolle über Routen und Responses. |
| `AdminIndexView` | `Admin(index_view=...)` | Bauen Sie Dashboards aus `StatWidget`, `ChartWidget`, `TableWidget` und Layout-Widgets. |
| `MenuLink` | [`Link`](../user-guide/views.md#link)-View | Zum Beispiel `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Kategorien im Menü | [`DropDown`](../user-guide/views.md#sidebar-organization)-View | Gruppiert Views in der Sidebar. |
| `FileAdmin` | Nicht verfügbar | Datei- und Bildfelder mit [lokalem oder S3-Speicher](../user-guide/file-storage.md) verwalten Anhänge. Einen Server-Dateibrowser gibt es nicht. |

## Inline-Modelle

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

Eine explizite Klasse stellt jedem Inline-Modell die gesamte Konfigurationsoberfläche von `ModelView` zur Verfügung: Feldauswahl, Validierung und Unterstützung zusammengesetzter Fremdschlüssel. Siehe [Inline-Formulare](../user-guide/inline-forms.md).

## Internationalisierung

Flask-Admin hängt von Flask-Babel und der umgebenden Flask-Umgebung ab. starlette-admin verwendet stattdessen ein Konfigurationsobjekt:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Zeitzonenbewusstes Rendern von Datum und Uhrzeit funktioniert auf dieselbe Weise über `TimezoneConfig`. Siehe [Internationalisierung und Zeitzonen](../user-guide/i18n.md).

## Was Sie durch den Wechsel gewinnen

* **Ein asynchroner Stack.** Läuft nativ unter FastAPI und Starlette, mit Unterstützung für async SQLAlchemy, Beanie und Tortoise ORM. Flask-Admin ist synchron.
* **Integrierte Sicherheitsfunktionen.** CSRF-Schutz, Bereinigung von Upload-Dateinamen, Prüfung des Bildinhalts und Export-Zeilenbegrenzungen sind aktiv, sobald Sie `Admin` instanziieren; das Escaping von Tabellenkalkulationsformeln lässt sich an den Exportern einschalten. Siehe [Sicherheit](../user-guide/security.md).
* **Datenimport.** Ein Vorschauschritt validiert jede Zeile, bevor etwas geschrieben wird. Flask-Admin bietet keine Importfunktion.
* **Ein Widget-System für Dashboards.** Erstellen Sie Indexseiten und eigene Views in Python, statt Templates von Hand zu schreiben.
* **Modernes Design.** Eine aktiv gepflegte Codebasis mit ausgereifter Benutzeroberfläche, integriertem Dark Mode und erstklassigen Type Hints.

## Woran Sie sich anpassen müssen

* **Explizite Request-Objekte.** Einen ambienten Request-Kontext gibt es nicht. Jeder Hook und jede Berechtigungsmethode erhält den `request` als Parameter.
* **Asynchrone Handler.** Hooks und Aktionen sind Coroutinen; halten Sie blockierende Aufrufe daraus fern oder verlagern Sie diese Arbeit in einen Thread.
* **Kein `FileAdmin`.** Wenn Ihr Workflow das Durchsuchen des Server-Dateisystems erfordert, deckt starlette-admin das nicht ab.
* **Keine Modals zum Erstellen oder Bearbeiten.** Formulare werden als vollständige Seiten statt als Popup-Modals gerendert.
