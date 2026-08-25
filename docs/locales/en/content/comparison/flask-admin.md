---
title: Coming from Flask-Admin
description: A direct migration guide from Flask-Admin to starlette-admin, showing how to transition your ModelView configurations to the ASGI ecosystem.
---

# Coming from Flask-Admin

starlette-admin began as a port of Flask-Admin's concepts to the ASGI ecosystem, so the migration is direct. You still subclass a `ModelView`, configure it with class attributes, and register it on an `Admin` instance. Most of the work is renaming attributes and moving from Flask's implicit request context to Starlette's explicit `request` object.

This guide maps the Flask-Admin API, attribute by attribute, to its starlette-admin equivalent.

## Mental model

| Flask-Admin concept | starlette-admin equivalent |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, then `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; the `Admin` instance owns the engine and database sessions |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee / pymongo backends | Beanie, Tortoise ORM, SQLModel, or a [custom backend](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Flask request context (`flask.request`) | Explicit `request: Request` parameter on every hook |
| Sync methods | `async` methods; sync still works where callables are accepted |

## Setup

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

There's no `template_mode` switch. The UI uses [Tabler](https://tabler.io) (Bootstrap 5) and includes dark mode. To change the look, write a custom [`BaseTheme`](../advanced/custom-themes.md) or [override the templates](../advanced/templates.md).

## List page attributes

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `column_list` | `fields` | Also drives the detail and form pages. Use the `exclude_fields_from_*` attributes for per-page variations. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | For example, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Applies to the field definition. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | For example, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / export formatters | The same `formatter=` dict, keyed by `RequestAction` | One mapping covers list, detail, and export formatting. Actions without an entry keep the raw value. |
| `column_type_formatters` | Per-field `formatter=`, or a custom field subclass | There's no per-type registry. Attach the formatter to each field, or [subclass the field](../advanced/custom-fields.md) and reuse it. |
| Model properties or callables in `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) or `getter=` on any field | Adds virtual columns, or redirects an existing field's value lookup, without a subclass. |
| Custom WTForms fields (value coercion) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | Replaces the field's default form or import parsing per `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` combined with per-field `filters=` | Replaces the flat filter list with a [visual builder](../user-guide/filters.md) that supports nested `AND`/`OR` groups. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | For example, `[("created_at", True)]` sorts in descending order. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Users select a cell and edit it in place. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Defaults to `[10, 25, 50, 100]`. Users pick from these options. |
| `column_display_pk` | Include the primary key in `fields` |  |
| `column_details_list` | `fields` minus `exclude_fields_from_detail` | The detail page is built in. There's no `can_view_details` opt-in. |

## Form attributes

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `form_columns` | `fields` minus `exclude_fields_from_create` and `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Separate visibility controls per form. |
| `form_overrides` | Explicit field instances in `fields` | For example, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Constructor arguments on the field | For example, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | For example, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Extra entries in `fields` | Supports any field that isn't backed by a database column, such as a [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Field attributes | Set `read_only`, `disabled`, or `placeholder` directly on the field. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Replaces flat rules with fieldsets, tabs, and responsive grids. |
| `create_modal` / `edit_modal` | Not available | Create and edit views render as full pages. |
| `on_form_prefill` | `before_edit` hook |  |

## Export and import

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

CSV and JSON export is on by default. Row caps apply automatically, and spreadsheet formula escaping is an opt-in exporter setting. Import, which Flask-Admin doesn't provide, includes a preview step with per-row validation and optional updates to existing records by primary key. See [Export and Import](../user-guide/export-import.md).

## Actions

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

The handler receives an [`ActionSelection`](../user-guide/actions.md) object instead of raw IDs. It resolves rows lazily, exposes the active filters, and works the same way when a user selects all matching records across pages. Actions can also render a custom HTML form inside the confirmation dialog. For per-row operations, [`@row_action` and `@link_row_action`](../user-guide/actions.md#row-actions) replace custom column formatters.

## Permissions and access control

Flask-Admin's `can_*` class flags become [per-request methods](../user-guide/views.md#security-and-authorization) in starlette-admin, so authorization decisions can depend on the signed-in user.

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Hides the view from the menu and blocks direct access. |
| `inaccessible_callback()` | Handled by the authentication flow | Unauthenticated requests redirect to the sign-in page. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` and `can_delete` follow the same pattern. |
| `can_view_details` | `can_view_detail(request)` | The detail page exists by default. |
| `can_export` | `can_export(request)`, plus `can_import(request)` |  |
| No equivalent | `can_access_field(request, field)` | Controls field-level visibility per user. |
| No equivalent | `is_action_allowed(request, name)` | Provides per-action authorization. |

With Flask-Admin, you integrate Flask-Login yourself. starlette-admin ships an [`AuthProvider`](../user-guide/auth.md) with a ready-made sign-in page, and you implement the `login`, `logout`, and `authenticate` methods against your user store. An `OAuthProvider` covers OIDC redirect flows. The signed-in user is available everywhere as `request.state.admin_user`.

## Model lifecycle hooks

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, specific to the SQLAlchemy backend |
| `handle_view_exception` | Raise `FormValidationError` or `ActionFailed` |

Beyond per-view hooks, the [event system](../advanced/events.md) lets a single handler observe every view. Flask-Admin has no equivalent.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Custom views and the index page

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Compose pages from [widgets](../user-guide/custom-views.md) without writing raw templates. |
| Custom template rendering | `CustomView` subclass | Gives you full control over routes and responses. |
| `AdminIndexView` | `Admin(index_view=...)` | Build dashboards from `StatWidget`, `ChartWidget`, `TableWidget`, and layout widgets. |
| `MenuLink` | [`Link`](../user-guide/views.md#link) view | For example, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Categories in the menu | [`DropDown`](../user-guide/views.md#sidebar-organization) view | Groups views together in the sidebar. |
| `FileAdmin` | Not available | File and image fields with [local or S3 storage](../user-guide/file-storage.md) handle attachments. There's no server file browser. |

## Inline models

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

An explicit class gives each inline model the full `ModelView` configuration surface: field selection, validation, and composite foreign key support. See [Inline Forms](../user-guide/inline-forms.md).

## Internationalization

Flask-Admin depends on Flask-Babel and the surrounding Flask environment. starlette-admin uses a configuration object instead:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Timezone-aware datetime rendering works the same way, through `TimezoneConfig`. See [Internationalization and Timezones](../user-guide/i18n.md).

## What you gain by switching

* **An async stack.** Runs natively on FastAPI and Starlette, with support for async SQLAlchemy, Beanie, and Tortoise ORM. Flask-Admin is synchronous.
* **Security features built in.** CSRF protection, upload filename sanitization, image content verification, and export row limits are on as soon as you instantiate `Admin`, and you can enable spreadsheet formula escaping on the exporters. See [Security](../user-guide/security.md).
* **Data import.** A preview step validates every row before anything is written. Flask-Admin has no import feature.
* **A dashboard widget system.** Build index pages and custom views in Python instead of hand-writing templates.
* **Modern design.** An actively maintained codebase with a polished UI, built-in dark mode, and first-class type hints.

## What you must adapt to

* **Explicit request objects.** There's no ambient request context. Every hook and permission method receives the `request` as a parameter.
* **Async handlers.** Hooks and actions are coroutines, so keep blocking calls out of them or move that work to a thread.
* **No `FileAdmin`.** If your workflow depends on browsing the server file system, starlette-admin doesn't cover it.
* **No create or edit modals.** Forms render as full pages rather than popup modals.
