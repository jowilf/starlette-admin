---
title: Coming from Django Admin
description: A comprehensive migration guide mapping Django Admin concepts to starlette-admin equivalents for building declarative administrative interfaces.
---

# Coming from Django Admin

If you know Django Admin, starlette-admin will feel familiar. Both generate an admin interface from declarative, per-model configuration, and both support inline editing, batch actions, and per-request permissions.

The differences are structural. starlette-admin runs on any ASGI application instead of requiring Django, works with several ORMs, and lets you plug in your own authentication rather than imposing a built-in user model.

This guide maps every major `ModelAdmin` concept to its starlette-admin equivalent, with side-by-side code.

## Mental model

| Django Admin concept | starlette-admin equivalent |
| --- | --- |
| `AdminSite` | [`Admin`](../api/admin.md) instance mounted on your application |
| `ModelAdmin` | [`ModelView`](../user-guide/views.md) subclass |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` in `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie, or Tortoise ORM through `starlette_admin.contrib.*` |
| `__str__` on the model | `__admin_repr__(self, request)`, which is async and request-aware |
| Form fields inferred from model fields | [Fields](../user-guide/fields.md) inferred by the backend converter, customizable per field |

## Registering a model

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

Two structural differences stand out:

1. **One field list drives every page.** `fields` is the single source of truth. You then use [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create`, and `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) for per-page variations.
2. **The `Admin` instance owns the database engine.** You don't pass a session to each view.

## List page options

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `list_display` | `fields` minus [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | A single field list drives every page. |
| `list_display` with a callable or `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield), or `getter=` on any field | For example, `ComputedField("full_name", getter=lambda request, obj: ...)`. Use `getter=` on a typed field, such as a date or image field, to keep that type's rendering. |
| Reformatting a real column for display | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | A `dict[RequestAction, callable]`, so list, detail, and export can format differently. Django needs a callable plus `admin_order_field` to keep sorting; here the column stays sortable. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Powers both full-text search and the filter builder. |
| `list_filter` | `searchable_fields` combined with per-field `filters=` | Users get a visual builder with nested `AND`/`OR` groups instead of a fixed sidebar. See [Filters](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | For example, `fields_default_sort = [("created_at", True)]` sorts in descending order. |
| `admin_order_field` / sortability | [`sortable_fields`](../user-guide/views.md#search-and-sort) | Every field is sortable by default. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Users select a cell and edit it in place. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Controls pagination limits. |
| `date_hierarchy` | Date filters, such as `between` and `in the past` | There's no dedicated drill-down bar; the filter builder covers this case. |
| `empty_value_display` | A `formatter=` entry, or `null_template` | Formatters receive `None` values, so they can substitute a placeholder. `null_template` swaps the rendered markup instead. |

## Forms

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Controls form field visibility. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Compose freely with `FieldsetWidget`, `TabsWidget`, `GridWidget`, and `RowWidget`. |
| `readonly_fields` | `read_only=True` on the field | You can also exclude the field from the create and edit views. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | Same live slugification behavior. |
| `autocomplete_fields`, `raw_id_fields` | Default behavior of [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) | Relation widgets are Select2 inputs with server-side search out of the box. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Rendered as a searchable multi-select component. |
| `formfield_overrides` | Explicit entries in the `fields` list | Replace the auto-detected field directly: `fields = ["id", TextAreaField("bio")]` |
| Custom form validation | Field `validators=` or `FormValidationError` in hooks | See [Validators](../api/validators.md). |
| Form field `to_python()` / custom coercion | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | Replaces the field's default form or import parsing per `RequestAction`. |
| Model form help text | `help_text=` | Available on any field definition. |

### Fieldsets example

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

`form_layout` goes further than fieldsets: you can build tabs, responsive grids, and nested layouts. See [Form Layout](../advanced/form-layout.md).

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

starlette-admin detects the foreign key when it's unambiguous, and it supports composite foreign keys. See [Inline Forms](../user-guide/inline-forms.md) for advanced configurations.

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

Where Django Admin passes a `QuerySet`, the starlette-admin handler receives an [`ActionSelection`](../user-guide/actions.md) object. It resolves rows, primary keys, and active filters lazily, and it behaves the same way when a user selects all matching records.

Actions can also render a custom HTML form inside the confirmation dialog, which in Django Admin means building an intermediate page. For per-row operations, use [`@row_action` and `@link_row_action`](../user-guide/actions.md#row-actions), which have no Django Admin equivalent.

## Permissions and authentication

Django Admin delegates to `django.contrib.auth`. starlette-admin splits the problem in two: an [`AuthProvider`](../user-guide/auth.md) answers "who is this user", and [per-view methods](../user-guide/views.md#security-and-authorization) answer "what can they do".

| Django Admin | starlette-admin |
| --- | --- |
| `django.contrib.auth` login | `AuthProvider` (built-in sign-in page) or `OAuthProvider` (OIDC redirect flow) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` on the view |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` per user | `can_access_field(request, field)` |
| No equivalent | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

The following view restricts deletion to users with the `admin` role:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Every `can_*` method receives the request, so your authorization decisions can read the current user, HTTP headers, or anything else on the request.

## Save hooks and signals

| Django Admin | starlette-admin | Notes |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) on the view | Async-native, and receives the parsed form data with the model instance. |
| `delete_model` | `before_delete` | Handles pre-deletion logic. |
| `post_save` and other signals | [Events](../advanced/events.md) | For example, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` broadcasts to all views. |
| `LogEntry` change history | Build it with the event system | Subscribe to `AFTER_CREATE`, `AFTER_EDIT`, and `AFTER_DELETE` to fill your own audit table. |
| `messages.success(request, ...)` | `flash(request, ...)` | See [Flash Messages](../user-guide/flash-messages.md). |

## Site-wide configuration

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Custom logo through a template override | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` with [widgets](../user-guide/custom-views.md) for a rich dashboard |
| Template overrides in `templates/admin/` | `Admin(templates_dir="...")`, see [Templates](../advanced/templates.md) |
| Multiple `AdminSite` instances | Multiple `Admin` instances mounted at different application paths |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query`, or `get_detail_query` for the SQLAlchemy backend |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, see [i18n and Timezones](../user-guide/i18n.md) |

## What you gain by switching

* **End-to-end async:** Handlers, lifecycle hooks, and widget callbacks can all be coroutines that run on your existing event loop, next to your FastAPI endpoints.
* **Database flexibility:** The same admin configuration applies whether you use SQLAlchemy, SQLModel, MongoDB through MongoEngine or Beanie, or Tortoise ORM.
* **Export and import built in:** CSV, JSON, and PDF, plus Excel and other formats through `tablib`. Export records directly, or import bulk data through a preview-first wizard that enforces row-level validation and supports optional primary key upserts. See [Export and Import](../user-guide/export-import.md).
* **Dashboard widgets:** Stat cards, ApexCharts, and layout grids compose into index pages and custom views, so you don't need an external theme package to build a dashboard. See [Custom Views and Widgets](../user-guide/custom-views.md).
* **Modern user interface:** Tabler (Bootstrap 5) gives you dark mode, column visibility toggles, and search highlighting by default.

## What you must bring yourself

* **Authentication:** There's no bundled user model or permission database. Implement `AuthProvider.authenticate()` against the data store your application already uses.
* **Audit logging:** starlette-admin doesn't generate a `LogEntry` table. Wire the [event system](../advanced/events.md) to your own audit table.
* **Model-level UI configuration:** Django conveniences such as model-level `choices`, `verbose_name`, and validators don't transfer. Declare them on the starlette-admin field instead, with `EnumField`, `label=`, and `validators=`.
