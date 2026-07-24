# Coming from Flask-Admin

Because starlette-admin began as a port of Flask-Admin's concepts to the ASGI ecosystem, the migration process is highly direct. You still subclass a `ModelView`, configure it using class attributes, and register it on an `Admin` instance. Most of the transition involves renaming attributes and shifting from Flask's implicit request context to Starlette's explicit `request` object.

This guide maps the Flask-Admin API, attribute by attribute, to its starlette-admin equivalent.

## Mental Model

| Flask-Admin Concept | starlette-admin Equivalent |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")` then `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; the `Admin` instance owns the engine and database sessions |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee / pymongo backends | Beanie, Tortoise ORM, SQLModel, or a [custom backend](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Flask request context (`flask.request`) | Explicit `request: Request` parameter on every hook |
| Sync methods | `async` methods (sync still works where callables are accepted) |

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

There is no `template_mode` switch. The UI uses [Tabler](https://tabler.io) (Bootstrap 5) with built-in dark mode support. You customize the appearance using a custom [`BaseTheme`](../advanced/custom-themes.md) and [template overrides](../advanced/templates.md).

## List Page Attributes

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `column_list` | `fields` | Also drives detail and form pages. Use the `exclude_fields_from_*` attributes to define per-page variations. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Example: `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Applies to the specific field definition. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | Example: `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / export formatters | The same `formatter=` dict, keyed by `RequestAction` | One mapping covers list, detail, and export formatting; actions without an entry keep the raw value. |
| `column_type_formatters` | Per-field `formatter=`, or a custom field subclass | There is no per-type registry; attach the formatter to each field, or [subclass the field](../advanced/custom-fields.md) and reuse it. |
| Model properties or callables in `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) or `getter=` on any field | Adds virtual columns, or redirects an existing field's value lookup, without a subclass. |
| Custom WTForms fields (value coercion) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) on the field | Replaces the field's default form or import parsing per `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-sort) |  |
| `column_filters` | `searchable_fields` combined with per-field `filters=` | Replaces the flat filter list with a [visual builder](../user-guide/filters.md) supporting nested `AND`/`OR` groups. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-sort) | Example: `[("created_at", True)]` for descending order. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Allows clicking a cell to edit in place. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-ui-controls) | Defaults to `[10, 25, 50, 100]`. Users select from these options. |
| `column_display_pk` | Include the primary key in `fields` |  |
| `column_details_list` | `fields` minus `exclude_fields_from_detail` | The detail page is built in. No `can_view_details` opt-in is required. |

## Form Attributes

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `form_columns` | `fields` minus `exclude_fields_from_create` and `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Provides separate visibility controls per form. |
| `form_overrides` | Explicit field instances in `fields` | Example: `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Constructor arguments on the field | Example: `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Example: `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Extra entries in `fields` | Supports any field not backed by a database column, such as a [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Field attributes | Use attributes like `read_only`, `disabled`, or `placeholder` directly on the field. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Replaces flat rules with robust fieldsets, tabs, and responsive grids. |
| `create_modal` / `edit_modal` | Not available | Create and edit views render as full pages. |
| `on_form_prefill` | `before_edit` hook |  |

## Export and Import

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

Exporting to CSV and JSON is enabled by default. Row caps apply automatically, and spreadsheet formula escaping is available as an opt-in exporter setting. Importing, a feature Flask-Admin lacks entirely, includes a preview step with per-row validation and optional updates of existing records by primary key. See [Export and Import](../user-guide/export-import.md).

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

The handler receives an [`ActionSelection`](../user-guide/actions.md) object instead of raw IDs. This object resolves rows lazily, exposes active filters, and works transparently with "select all matching" across multiple pages. Actions can also render a custom HTML form within the confirmation dialog. Additionally, [`@row_action` and `@link_row_action`](../user-guide/actions.md#row-actions) provide per-row operations without requiring custom column formatters.

## Permissions and Access Control

Flask-Admin's `can_*` class flags translate to [per-request methods](../user-guide/views.md#security-authorization) in starlette-admin, allowing authorization decisions to depend dynamically on the logged-in user.

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Hides the view from the menu and blocks direct access. |
| `inaccessible_callback()` | Handled by the authentication flow | Unauthenticated requests redirect to the login page automatically. |
| `can_create = False` | `def can_create(self, request): return False` | Follows the same pattern for `can_edit` and `can_delete`. |
| `can_view_details` | `can_view_detail(request)` | The detail page exists by default. |
| `can_export` | `can_export(request)`, plus `can_import(request)` |  |
| N/A | `can_access_field(request, field)` | Controls field-level visibility per user. |
| N/A | `is_action_allowed(request, name)` | Provides per-action authorization. |

Flask-Admin requires you to integrate Flask-Login manually. In contrast, starlette-admin provides an [`AuthProvider`](../user-guide/auth.md) with a ready-made login page, requiring you only to implement the `login`, `logout`, and `authenticate` methods against your user datastore. It also offers an `OAuthProvider` for OIDC redirect flows. The authenticated user is accessible globally via `request.state.admin_user`.

## Model Lifecycle Hooks

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query` (Specific to the SQLAlchemy backend) |
| `handle_view_exception` | Raise `FormValidationError` or `ActionFailed` |

Beyond per-view hooks, the [event system](../advanced/events.md) allows a single handler to observe every view. Flask-Admin has no equivalent feature.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Custom Views and the Index Page

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Compose pages from [widgets](../user-guide/custom-views.md) without writing raw templates. |
| Custom template rendering | `CustomView` subclass | Offers full control over routes and responses when needed. |
| `AdminIndexView` | `Admin(index_view=...)` | Build dashboards using `StatWidget`, `ChartWidget`, `TableWidget`, and layout widgets. |
| `MenuLink` | [`Link`](../user-guide/views.md#link) view | Example: `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Categories in the menu | [`DropDown`](../user-guide/views.md#sidebar-organization) view | Groups views together in the sidebar. |
| `FileAdmin` | Not available | Replaced by file and image fields with [local or S3 storage](../user-guide/file-storage.md) for attachments. There is no dedicated server file browser. |

## Inline Models

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

Using an explicit class gives you the full `ModelView` configuration surface for each inline model. This includes field selection, validation, and composite foreign key support. See [Inline Forms](../user-guide/inline-forms.md).

## Internationalization

Flask-Admin depends on Flask-Babel and the surrounding Flask environment. starlette-admin uses a dedicated configuration object:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

You configure timezone-aware datetime rendering similarly using `TimezoneConfig`. See [Internationalization and Timezones](../user-guide/i18n.md).

## What You Gain by Switching

* **An async stack.** Runs natively on FastAPI and Starlette, bringing full support for async SQLAlchemy, Beanie, and Tortoise ORM. Flask-Admin remains strictly synchronous.
* **Security features built in.** CSRF protection, upload filename sanitization, image content verification, and export row limits are enabled automatically when you instantiate the `Admin` class, and spreadsheet formula escaping can be enabled on the exporters. See [Security](../user-guide/security.md).
* **Robust data import.** Includes a built-in preview step that validates every row before writing, a feature Flask-Admin lacks entirely.
* **A dashboard widget system.** Construct index pages and custom views programmatically instead of relying on hand-written templates.
* **Modern design.** An actively maintained codebase utilizing a polished UI, built-in dark mode, and first-class type hinting.

## What You Must Adapt To

* **Explicit request objects.** There is no ambient request context. Every hook and permission method receives the `request` object explicitly as a parameter.
* **Async handlers.** Hooks and actions are coroutines. You must avoid blocking calls inside them or offload them to separate threads.
* **No `FileAdmin`.** If your workflow relies heavily on browsing the server file system directly, be aware that this specific feature does not exist in starlette-admin.
* **No create/edit modals.** Forms are built as complete, standalone pages rather than popup modals.
