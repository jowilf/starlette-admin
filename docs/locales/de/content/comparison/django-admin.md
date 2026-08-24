---
title: Migration von Django Admin
description: Ein umfassender Migrationsleitfaden, der Django-Admin-Konzepte ihren
  starlette-admin-Entsprechungen für den Aufbau deklarativer Verwaltungsoberflächen
  zuordnet.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Migration von Django Admin

Wenn Sie Django Admin kennen, wird Ihnen starlette-admin vertraut vorkommen. Beide erzeugen eine Admin-Oberfläche aus deklarativer Konfiguration pro Modell, und beide unterstützen Inline-Bearbeitung, Batch-Aktionen und Berechtigungen pro Anfrage.

Die Unterschiede sind struktureller Natur. starlette-admin läuft auf jeder ASGI-Anwendung, statt Django vorauszusetzen, arbeitet mit mehreren ORMs und erlaubt es Ihnen, Ihre eigene Authentifizierung anzubinden, statt ein eingebautes Benutzermodell vorzugeben.

Dieser Leitfaden ordnet jedes zentrale `ModelAdmin`-Konzept seiner starlette-admin-Entsprechung zu – mit Code im direkten Vergleich.

## Mentales Modell

| Django-Admin-Konzept | starlette-admin-Entsprechung |
| --- | --- |
| `AdminSite` | [`Admin`](../api/admin.md)-Instanz, die in Ihrer Anwendung gemountet ist |
| `ModelAdmin` | [`ModelView`](../user-guide/views.md)-Unterklasse |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` in `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie oder Tortoise ORM über `starlette_admin.contrib.*` |
| `__str__` am Modell | `__admin_repr__(self, request)`, das asynchron ist und die Anfrage berücksichtigt |
| Aus Modelfeldern abgeleitete Formularfelder | [Felder](../user-guide/fields.md), abgeleitet vom Backend-Converter, pro Feld anpassbar |

## Registrieren eines Modells

=== "Django Admin"

    ```python
    from django.contrib import admin
    from .models import Post


    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import Admin, ModelView


    class PostView(ModelView):
        fields = ["id", "title", "content", "published", "created_at"]
        exclude_fields_from_list = ["content"]
        searchable_fields = ["title", "content"]


    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)  # app is your FastAPI or Starlette instance
    ```

Zwei strukturelle Unterschiede fallen besonders auf:

1. **Eine Feldliste steuert jede Seite.** `fields` ist die alleinige Quelle der Wahrheit. Für Abweichungen pro Seite verwenden Sie anschließend [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` und `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization).
2. **Die `Admin`-Instanz besitzt die Datenbank-Engine.** Sie übergeben keine Session an die einzelnen Views.

## Optionen der Listenseite

| Django Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `list_display` | `fields` minus [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | Eine einzige Feldliste steuert alle Seiten. |
| `list_display` mit einem Callable oder `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield) oder `getter=` an einem beliebigen Feld | Zum Beispiel `ComputedField("full_name", getter=lambda request, obj: ...)`. Verwenden Sie `getter=` an einem typisierten Feld, etwa einem Datums- oder Bildfeld, um dessen Rendering beizubehalten. |
| Neuformatieren einer echten Spalte zur Anzeige | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Ein `dict[RequestAction, callable]`, sodass Liste, Detailansicht und Export unterschiedlich formatieren können. Django benötigt einen Callable plus `admin_order_field`, um die Sortierbarkeit zu erhalten; hier bleibt die Spalte sortierbar. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Steuert sowohl die Volltextsuche als auch den Filter-Builder. |
| `list_filter` | `searchable_fields` kombiniert mit pro Feld gesetztem `filters=` | Benutzer erhalten einen visuellen Builder mit verschachtelten `AND`-/`OR`-Gruppen statt einer festen Sidebar. Siehe [Filter](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Zum Beispiel sortiert `fields_default_sort = [("created_at", True)]` in absteigender Reihenfolge. |
| `admin_order_field` / Sortierbarkeit | [`sortable_fields`](../user-guide/views.md#search-and-sort) | Jedes Feld ist standardmäßig sortierbar. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Benutzer wählen eine Zelle aus und bearbeiten sie direkt an Ort und Stelle. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Steuert die Grenzen der Paginierung. |
| `date_hierarchy` | Datumsfilter wie `between` und `in the past` | Eine eigene Drilldown-Leiste gibt es nicht; der Filter-Builder deckt diesen Fall ab. |
| `empty_value_display` | Ein `formatter=`-Eintrag oder `null_template` | Formatter erhalten `None`-Werte und können daher einen Platzhalter einsetzen. `null_template` ersetzt stattdessen das gerenderte Markup. |

## Formulare

| Django Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Steuert die Sichtbarkeit von Formularfeldern. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Frei kombinierbar mit `FieldsetWidget`, `TabsWidget`, `GridWidget` und `RowWidget`. |
| `readonly_fields` | `read_only=True` am Feld | Sie können das Feld auch aus den Create- und Edit-Views ausschließen. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | Identisches Verhalten der Live-Slug-Erzeugung. |
| `autocomplete_fields`, `raw_id_fields` | Standardverhalten von [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) | Relations-Widgets sind Select2-Eingabefelder mit serverseitiger Suche ab Werk. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Wird als durchsuchbare Multi-Select-Komponente gerendert. |
| `formfield_overrides` | Explizite Einträge in der `fields`-Liste | Ersetzen Sie das automatisch erkannte Feld direkt: `fields = ["id", TextAreaField("bio")]` |
| Eigene Formularvalidierung | `validators=` am Feld oder `FormValidationError` in Hooks | Siehe [Validators](../api/validators.md). |
| `to_python()` des Formularfelds / eigene Typumwandlung | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) am Feld | Ersetzt das Standard-Parsing des Felds für Formular oder Import, jeweils pro `RequestAction`. |
| Hilfetext im Modelformular | `help_text=` | Für jede Felddefinition verfügbar. |

### Fieldsets-Beispiel

=== "Django Admin"

    ```python
    class PostAdmin(admin.ModelAdmin):
        fieldsets = [
            ("Content", {"fields": ["title", "body"]}),
            ("Publication", {"fields": ["published", "created_at"]}),
        ]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import FieldsetWidget


    class PostView(ModelView):
        fields = ["id", "title", "body", "published", "created_at"]
        form_layout = [
            FieldsetWidget(legend="Content", children=["title", "body"]),
            FieldsetWidget(legend="Publication", children=["published", "created_at"]),
        ]
    ```

`form_layout` geht über Fieldsets hinaus: Sie können damit Tabs, responsive Grids und verschachtelte Layouts erstellen. Siehe [Formularlayout](../advanced/form-layout.md).

## Inlines

=== "Django Admin"

    ```python
    class CommentInline(admin.TabularInline):
        model = Comment
        extra = 1


    class ArticleAdmin(admin.ModelAdmin):
        inlines = [CommentInline]
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

starlette-admin erkennt den Fremdschlüssel, wenn dieser eindeutig ist, und unterstützt zusammengesetzte Fremdschlüssel. Fortgeschrittene Konfigurationen finden Sie unter [Inline-Formulare](../user-guide/inline-forms.md).

## Aktionen

=== "Django Admin"

    ```python
    @admin.action(description="Mark selected articles as published")
    def make_published(modeladmin, request, queryset):
        queryset.update(published=True)


    class ArticleAdmin(admin.ModelAdmin):
        actions = [make_published]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class ArticleView(ModelView):
        actions = ["make_published", "delete"]

        @action(
            name="make_published",
            text="Mark selected articles as published",
            confirmation="Publish the selected articles?",
        )
        async def make_published(
            self, request: Request, selection: ActionSelection
        ) -> None:
            for article in await selection.rows():
                article.published = True
            flash(request, "Articles published")
    ```

Wo Django Admin ein `QuerySet` übergibt, erhält der Handler in starlette-admin ein [`ActionSelection`](../user-guide/actions.md)-Objekt. Es löst Zeilen, Primärschlüssel und aktive Filter verzögert (lazy) auf und verhält sich genauso, wenn ein Benutzer alle übereinstimmenden Datensätze auswählt.

Aktionen können außerdem ein eigenes HTML-Formular innerhalb des Bestätigungsdialogs rendern – in Django Admin entspräche das dem Bau einer separaten Zwischenseite. Für Operationen auf Zeilenebene verwenden Sie [`@row_action` und `@link_row_action`](../user-guide/actions.md#row-actions); dafür existiert kein Pendant in Django Admin.

## Berechtigungen und Authentifizierung

Django Admin delegiert an `django.contrib.auth`. starlette-admin zerlegt das Problem in zwei Teile: Ein [`AuthProvider`](../user-guide/auth.md) beantwortet die Frage „Wer ist dieser Benutzer?“, und [die Methoden pro View](../user-guide/views.md#security-and-authorization) beantworten die Frage „Was darf dieser Benutzer tun?“.

| Django Admin | starlette-admin |
| --- | --- |
| `django.contrib.auth`-Login | `AuthProvider` (eingebaute Anmeldeseite) oder `OAuthProvider` (OIDC-Redirect-Flow) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` am View |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` pro Benutzer | `can_access_field(request, field)` |
| Keine Entsprechung | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

Die folgende View beschränkt das Löschen auf Benutzer mit der Rolle `admin`:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Jede `can_*`-Methode erhält die Anfrage, sodass Ihre Autorisierungsentscheidungen auf den aktuellen Benutzer, HTTP-Header oder beliebige andere Angaben der Anfrage zugreifen können.

## Save-Hooks und Signale

| Django Admin | starlette-admin | Hinweise |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) am View | Nativ asynchron; empfängt die geparsten Formulardaten zusammen mit der Modellinstanz. |
| `delete_model` | `before_delete` | Dient der Logik vor dem Löschen. |
| `post_save` und andere Signale | [Events](../advanced/events.md) | Zum Beispiel überträgt `admin.events.on(AdminEvent.AFTER_CREATE, handler)` an alle Views. |
| `LogEntry`-Änderungshistorie | Bauen Sie sie mit dem Event-System | Abonnieren Sie `AFTER_CREATE`, `AFTER_EDIT` und `AFTER_DELETE`, um Ihre eigene Audit-Tabelle zu füllen. |
| `messages.success(request, ...)` | `flash(request, ...)` | Siehe [Flash-Nachrichten](../user-guide/flash-messages.md). |

## Globale Konfiguration

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Eigenes Logo über einen Template-Override | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` mit [Widgets](../user-guide/custom-views.md) für ein umfangreiches Dashboard |
| Template-Overrides in `templates/admin/` | `Admin(templates_dir="...")`, siehe [Templates](../advanced/templates.md) |
| Mehrere `AdminSite`-Instanzen | Mehrere `Admin`-Instanzen, gemountet an unterschiedlichen Anwendungspfaden |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` oder `get_detail_query` für das SQLAlchemy-Backend |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, siehe [i18n und Zeitzonen](../user-guide/i18n.md) |

## Was Sie durch den Wechsel gewinnen

* **Durchgängig asynchron:** Handler, Lifecycle-Hooks und Widget-Callbacks können alle Coroutines sein, die auf Ihrer bestehenden Event-Loop laufen – neben Ihren FastAPI-Endpoints.
* **Datenbankflexibilität:** Dieselbe Admin-Konfiguration gilt unabhängig davon, ob Sie SQLAlchemy, SQLModel, MongoDB über MongoEngine oder Beanie oder Tortoise ORM verwenden.
* **Export und Import eingebaut:** CSV, JSON und PDF, dazu Excel und weitere Formate über `tablib`. Exportieren Sie Datensätze direkt oder importieren Sie Massendaten über einen Wizard mit vorangestellter Vorschau, der Validierung auf Zeilenebene erzwingt und optionale Upserts per Primärschlüssel unterstützt. Siehe [Export und Import](../user-guide/export-import.md).
* **Dashboard-Widgets:** Stat-Karten, ApexCharts und Layout-Grids lassen sich zu Indexseiten und Custom Views kombinieren, sodass Sie kein externes Theme-Paket benötigen, um ein Dashboard zu bauen. Siehe [Custom Views und Widgets](../user-guide/custom-views.md).
* **Moderne Benutzeroberfläche:** Tabler (Bootstrap 5) bietet Dark Mode, Umschalter für die Spaltensichtbarkeit und Suchhervorhebung ab Werk.

## Was Sie selbst bereitstellen müssen

* **Authentifizierung:** Es gibt kein gebündeltes Benutzermodell und keine Berechtigungsdatenbank. Implementieren Sie `AuthProvider.authenticate()` gegen den Datenspeicher, den Ihre Anwendung bereits verwendet.
* **Audit-Logging:** starlette-admin erzeugt keine `LogEntry`-Tabelle. Verbinden Sie das [Event-System](../advanced/events.md) mit Ihrer eigenen Audit-Tabelle.
* **UI-Konfiguration auf Modellebene:** Django-Komfortfunktionen wie `choices`, `verbose_name` und Validatoren auf Modellebene werden nicht übernommen. Deklarieren Sie sie stattdessen am starlette-admin-Feld, mit `EnumField`, `label=` und `validators=`.
