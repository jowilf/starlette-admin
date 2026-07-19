# Coming from Django Admin

If you are coming from Django Admin, you will feel at home in starlette-admin. Both frameworks generate administrative interfaces using declarative, per-model configurations. Both support inline editing, batch actions, and per-request permissions.

The differences are primarily structural. Instead of requiring Django, starlette-admin runs on any ASGI application, supports multiple ORMs, and allows you to plug in your own authentication system rather than imposing a built-in user model.

This guide maps every major `ModelAdmin` concept to its starlette-admin equivalent alongside direct code comparisons.

## Mental Model

| Django Admin Concept | starlette-admin Equivalent |
| --- | --- |
| `AdminSite` | [`Admin`](../api/admin.md) instance mounted on your application |
| `ModelAdmin` | [`ModelView`](../user-guide/views.md) subclass |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` in `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie, or Tortoise ORM via `starlette_admin.contrib.*` |
| `__str__` on the model | `__admin_repr__(self, request)` (async and request-aware) |
| Form fields inferred from model fields | [Fields](../user-guide/fields.md) inferred by the backend converter, customizable per field |

## Registering a Model

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

There are two key structural differences to notice here:

1. **Unified field declaration:** The `fields` attribute acts as the single source of truth for all pages. You then use [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create`, and `exclude_fields_from_edit`](../user-guide/views.md#field-selection-customization) to define per-page variations.
2. **Database lifecycle ownership:** The `Admin` instance owns the database engine, meaning views do not need a session explicitly passed to them.

## List Page Options

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `list_display` | `fields` minus [`exclude_fields_from_list`](../user-guide/views.md#field-selection-customization) | A single field list drives every page. |
| `list_display` with a callable | [`ComputedField`](../user-guide/fields.md#computedfield) | Example: `ComputedField("full_name", fn=lambda obj: ...)` |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-sort) | Powers both full-text search and the filter builder. |
| `list_filter` | `searchable_fields` combined with per-field `filters=` | Users get a visual builder with nested `AND`/`OR` groups instead of a fixed sidebar. See [Filters](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-sort) | Example: `fields_default_sort = [("created_at", True)]` for descending order. |
| `admin_order_field` / sortability | [`sortable_fields`](../user-guide/views.md#search-sort) | Defaults to all fields being sortable. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Allows clicking a cell to edit in place. |
| `list_per_page` | [`page_size`, `page_size_options](../user-guide/views.md#pagination-ui-controls)` | Controls pagination limits. |
| `date_hierarchy` | Date filters (`between`, `in the past`, etc.) | There is no dedicated drill-down bar; the filter builder covers this use case. |
| `empty_value_display` | Field-level rendering | Override [`serialize_value`](../advanced/custom-fields.md) or use a `ComputedField`. |

## Forms

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Controls form field visibility. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Compose freely with `FieldsetWidget`, `TabsWidget`, `GridWidget`, and `RowWidget`. |
| `readonly_fields` | `read_only=True` on the field | Alternatively, exclude the field from the create/edit views. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | Provides the same live slugification behavior. |
| `autocomplete_fields`, `raw_id_fields` | Default behavior of [`HasOne` / `HasMany](../user-guide/fields.md#hasone-hasmany)` | Relation widgets are Select2 inputs with server-side search out of the box. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Rendered as a multi-select component with search capability. |
| `formfield_overrides` | Explicit entries in the `fields` list | Replace the auto-detected field directly: `fields = ["id", TextAreaField("bio")]` |
| Custom form validation | Field `validators=` or `FormValidationError` in hooks | See [Validators](../api/validators.md). |
| Model form help text | `help_text=` | Available on any field definition. |

### Fieldsets Example

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

The `form_layout` attribute offers significantly more flexibility than traditional fieldsets. You can easily build out tabs, responsive grids, and nested layouts. For more details, see [Form Layout](../advanced/form-layout.md).

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

Foreign keys are auto-detected when unambiguous, and composite foreign keys are fully supported. See [Inline Forms](../user-guide/inline-forms.md) for advanced configurations.

## Actions

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

Unlike Django Admin, which passes a `QuerySet`, the starlette-admin handler receives an [`ActionSelection`](../user-guide/actions.md) object. This object evaluates rows, primary keys, and active filters lazily. It also behaves consistently when a user chooses to "select all matching" records.

Furthermore, actions support custom HTML forms directly in the confirmation dialog, a feature that requires building an intermediate page in Django Admin. For per-row operations, starlette-admin provides [`@row_action` and `@link_row_action](../user-guide/actions.md#row-actions)`, which have no direct equivalent in Django Admin.

## Permissions and Authentication

While Django Admin delegates heavily to `django.contrib.auth`, starlette-admin splits the problem into two distinct parts: an [`AuthProvider`](../user-guide/auth.md) answers "who is this user," and [per-view methods](../user-guide/views.md#security-authorization) answer "what can they do."

| Django Admin | starlette-admin |
| --- | --- |
| `django.contrib.auth` login | `AuthProvider` (built-in login page) or `OAuthProvider` (OIDC redirect flow) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` on the view |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` per user | `can_access_field(request, field)` |
| N/A | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

Example of restricting deletion based on user roles:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Because every `can_*` method receives the request object, authorization decisions can dynamically evaluate the current user, HTTP headers, or any other request-specific data.

## Save Hooks and Signals

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit](../user-guide/views.md#lifecycle-hooks)` on the view | Async-native; receives the parsed form data and the model instance. |
| `delete_model` | `before_delete` | Handles pre-deletion logic. |
| `post_save` and other signals | [Events](../advanced/events.md) | Example: `admin.events.on(AdminEvent.AFTER_CREATE, handler)` broadcasts to all views. |
| `LogEntry` change history | Build using the event system | Subscribe to `AFTER_CREATE`, `AFTER_EDIT`, and `AFTER_DELETE` to populate your own audit table. |
| `messages.success(request, ...)` | `flash(request, ...)` | See [Flash Messages](../user-guide/flash-messages.md). |

## Site-Wide Configuration

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Custom logo via template override | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` utilizing [widgets](../user-guide/custom-views.md) for a rich dashboard |
| Template overrides in `templates/admin/` | `Admin(templates_dir="...")`, see [Templates](../advanced/templates.md) |
| Multiple `AdminSite` instances | Multiple `Admin` instances mounted at different application paths |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query`, or `get_detail_query` (for the SQLAlchemy backend) |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, see [i18n and Timezones](../user-guide/i18n.md) |

## What You Gain by Switching

* **End-to-end async architecture:** Handlers, lifecycle hooks, and widget callbacks can all be asynchronous coroutines running on your existing event loop, side-by-side with your FastAPI endpoints.
* **Database flexibility:** The exact same admin skills and configurations apply whether you use SQLAlchemy, SQLModel, MongoDB (via MongoEngine or Beanie), or Tortoise ORM.
* **Native import and export capabilities:** Out-of-the-box support for CSV, JSON, and Excel imports with dry-run validation. You also get export support for CSV, JSON, Excel, and PDF formats without requiring third-party plugins. See [Export and Import](../user-guide/export-import.md).
* **Integrated dashboard widgets:** Stat cards, ApexCharts, and layout grids compose easily into index pages and custom views. You do not need to hunt for an external theme package to build complex dashboards. See [Custom Views and Widgets](../user-guide/custom-views.md).
* **Modern user interface:** Uses Tabler (Bootstrap 5) to provide a polished UI that includes dark mode, column visibility toggles, and search highlighting by default.

## What You Must Bring Yourself

* **Custom user authentication:** There is no bundled user model or predefined permission database. You must implement `AuthProvider.authenticate()` to read from whichever datastore your application already utilizes.
* **Audit logging:** starlette-admin does not generate an automatic `LogEntry` table. You will need to wire the [event system](../advanced/events.md) to your own custom audit table.
* **Model-level UI configurations:** Django conveniences like model-level `choices`, `verbose_name`, and validators do not automatically transfer. You will need to declare these explicitly on the starlette-admin field definition (e.g., using `EnumField`, `label=`, and `validators=`).
