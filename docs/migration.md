# Migration Guide

This release is a major rewrite of starlette-admin. The list page, export system, actions, authentication, filtering, and templating layers were all rebuilt. Most applications need code changes to upgrade.

This guide covers every breaking change, in the order you are most likely to hit them. Each section shows the old API next to its replacement. If you only use the basics (an `Admin`, a few `ModelView` subclasses, `fields`, and `searchable_fields`), your migration is limited to the [Requirements](#requirements) and [Admin constructor](#the-admin-constructor) sections.

!!! tip
    Upgrade in one step, then start your app: most removed or renamed attributes raise clear errors at startup rather than failing silently at runtime.

## What's new

Beyond the breaking changes below, this release adds:

* **In-house list table**: DataTables and jQuery are gone. Lists are server-rendered with URL-driven state, so every list, filter, and sort state is shareable and bookmarkable.
* **[Filters](user-guide/filters.md)**: a nested `AND`/`OR` filter builder on every list page, derived from field types.
* **[Import & server-side export](user-guide/export-import.md)**: CSV/JSON import with per-row error reporting, and server-side exporters (CSV, JSON, Excel, PDF, and more) replacing the client-side DataTables buttons.
* **[Events](advanced/events.md)**: subscribe to lifecycle hooks (`before_create`, `after_edit_committed`, `after_login`, action events, and more).
* **[Themes](advanced/custom-themes.md)** and **[plugins](advanced/plugins.md)**: package and reuse custom looks and behaviors, with cookiecutter templates to get started.
* **[Widgets and dashboards](user-guide/custom-views.md)**: build index pages and custom views from `StatWidget`, `ChartWidget`, `TableWidget`, and friends.
* **[Form layout](advanced/form-layout.md)**: arrange create/edit forms in rows, columns, fieldsets, and tabs.
* **[Inline edit](user-guide/inline-edit.md)**: edit a single field straight from the list page.
* **[Inline forms](user-guide/inline-forms.md)**: edit related models inside the parent form with `InlineModelView`.
* **[Flash messages](user-guide/flash-messages.md)**, **[OAuth login](user-guide/auth.md)**, a **Tortoise ORM backend**, new fields (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), field-level `validators`, and clipboard copy on any field.

## Requirements

* **Python 3.11 or newer** is required. Python 3.9 and 3.10 are no longer supported.
* `itsdangerous` is now a core dependency. It signs the admin's cookies (CSRF token, flash messages).
* New optional extras:

    | Extra | Enables |
    | --- | --- |
    | `starlette-admin[email]` | `EmailField` server-side validation via `email-validator` |
    | `starlette-admin[pdf]` | PDF export via `reportlab` |
    | `starlette-admin[s3]` | S3 file storage via `aiobotocore` |
    | `starlette-admin[tinymce]` | `TinyMCEEditorField` HTML sanitization via `nh3` |
    | `starlette-admin[i18n]` | Translations via `babel` (unchanged) |

* **Beanie 2.0+** is required for the Beanie backend.
* **The Odmantic backend was removed.** Odmantic is no longer actively maintained. Stay on `starlette-admin<=0.17.1` or migrate to Beanie, which covers the same MongoDB use case.

## The Admin constructor

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` was renamed to `static_dir`.
* **Set `secret_key`.** It signs the CSRF and flash-message cookies. When omitted, a random key is generated at startup (fine for development), so signed values are invalidated on every restart and across multiple workers. In production, always pass a stable secret.
* `logo_url`, `login_logo_url`, and `favicon_url` now also accept a callable `(request) -> str | None`, replacing the per-request branding that `AdminConfig` used to provide.
* New optional parameters: `theme`, `plugins`, `additional_loaders`, `import_config`, `export_config`.
* SQLAlchemy only: the first argument is now `session_provider`. It still accepts an `Engine` or `AsyncEngine`, and now also accepts a `sessionmaker` / `async_sessionmaker`, so existing `Admin(engine)` calls keep working.
* `timezone_config` now defaults to `TimezoneConfig()` instead of `None`: datetimes are displayed in the viewer's local timezone by default. Pass `timezone_config=None` to keep raw values.

## Renamed view identifiers

The naming of views was unified. In `ModelView` constructors and class attributes:

| Before | After |
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

`Link` and `DropDown` use `menu_label` instead of `label` as well.

## DataTables removal

The list page no longer uses DataTables, so the attributes that configured it are gone:

| Removed | Replacement |
| --- | --- |
| `datatables_options` | None. The table is server-rendered; customize via templates. |
| `search_builder` | The new [filter builder](user-guide/filters.md), enabled by `searchable_fields`. |
| `responsive_table` | None. The table handles overflow natively. |
| `save_state` | Always on. List state (page, sort, filters, search, visible columns) lives in the URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (a list of filter classes). |
| `BaseField.render_function_key` | `BaseField.list_template` (server-side Jinja template). |

If you wrote custom JavaScript render functions or DataTables plugins, port them to `list_template` overrides: each field now renders its list cell from `templates/fields/list/*.html`.

## Actions

Batch action handlers receive an `ActionSelection` instead of a list of primary keys. This powers the new "select all matching" banner, which targets every row matching the current filter without materializing them client-side.

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

* `selection.rows()`, `selection.pks()`, and `selection.count()` resolve the target rows lazily, whether the user checked rows individually or selected all matching rows. `selection.is_select_all`, `selection.filters`, and `selection.q` let you push the operation down as a single bulk query.
* Returning a success message string is replaced by [flash messages](user-guide/flash-messages.md).
* Row action handlers keep their `(request, pk)` signature.
* New options on `@action`: `header`, `allow_empty_selection`, `dedicated_button`, `modal_size`, and per-request `form` callables.

## Authentication

`starlette_admin/auth.py` became the `starlette_admin.auth` package. Imports from `starlette_admin.auth` keep working, but the provider contract changed:

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

* `is_authenticated`, `get_admin_user`, and `get_admin_config` were merged into a single `authenticate(request) -> AdminUser | None`. Returning `None` means unauthenticated.
* `login` and `logout` no longer receive or return the prepared `response`. Return `None` for the default redirect, or a custom `Response` to override it.
* `AdminConfig` was removed. Per-request titles and logos are covered by the callable form of `logo_url` / `login_logo_url` on `Admin`.
* A built-in [`OAuthProvider`][starlette_admin.auth.oauth.OAuthProvider] handles OAuth2/OIDC login flows.
* `login_not_required` is unchanged.

## Export and import

Exports moved from client-side DataTables buttons to server-side streaming endpoints, and imports are new. `ExportType` no longer exists.

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

* `export_types` is now `exporters`, a list of format names or `BaseExporter` instances. Built-ins: `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml`, `pdf` (formats other than `csv`/`json` need `tablib`, PDF needs the `pdf` extra).
* `export_fields` (an include list) is replaced by `exclude_fields_from_export` (an exclude list), matching the other `exclude_fields_from_*` attributes. Fields also accept `exclude_from_export` / `exclude_from_import` individually.
* Global limits are set with `ExportConfig` and `ImportConfig` on the `Admin`. See [Export & Import](user-guide/export-import.md).

## Custom fields and template overrides

Field templates were reorganized. If you override built-in templates or ship custom fields:

| Before | After |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (client-side render function) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (path) | Same attribute, new path prefix `fields/form/` |

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

New per-field capabilities worth adopting while you are here: `validators`, `filters`, `default`, `getter` / `formatter` / `parser` hooks, `copy_to_clipboard`, and an `extra` dict for arbitrary metadata. See [Custom Fields](advanced/custom-fields.md).

`starlette_admin._types` was renamed to `starlette_admin.types`. `RequestAction` and the other public enums are still importable from the `starlette_admin` root.

## CustomView

`CustomView` no longer takes `template_path` and `methods`. Simple pages are built from [widgets](user-guide/custom-views.md); pages needing full control subclass `CustomView` and declare routes:

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

The `@route` decorator also lets any view expose extra endpoints (JSON data for charts, webhooks, and so on).

## Custom backends

If you implemented `BaseModelView` against your own datasource, the data-access contract changed:

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...

# After
async def find_all(self, request, skip=0, limit=100, q=None, sorts=None, filters=None): ...
async def count(self, request, q=None, filters=None): ...
```

* The stringly-typed `where` splits into `q` (the full-text search term) and `filters` (a typed `FilterGroup` tree from the filter builder).
* `order_by` (a list of `"field direction"` strings) becomes `sorts`, a list of `(field_name, direction)` tuples.
* Each backend now ships a filter registry mapping field types to filter implementations; see [Custom Backend](integrations/custom-backend.md) for the full contract and a worked example.

## Behavior changes to review

* **Datetimes render in the viewer's local timezone by default** (see the `timezone_config` note above).
* **List state lives in the URL.** Bookmarked admin URLs from the old version will land on default list states; saved DataTables state is not migrated.
* **`EmailField` validates on the server** when `email-validator` is installed.
* **CSRF protection is built in** and cookie-based; if you had a custom CSRF middleware around the admin, you can remove it. Ensure `secret_key` is set so tokens survive restarts.

## Removed with no replacement

* `AdminConfig` (see [Authentication](#authentication)).
* `datatables_options`, `responsive_table`, `save_state` (see [DataTables removal](#datatables-removal)).
* The Odmantic backend (see [Requirements](#requirements)).

## Getting help

If you hit a migration issue not covered here, [open an issue](https://github.com/jowilf/starlette-admin/issues) with a minimal reproduction and the version you are upgrading from.
