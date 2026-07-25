# Migration Guide

This page collects the upgrade instructions between `starlette-admin` releases. Jump to the section matching the version you are upgrading from.

---

## From 0.17.x to 1.0.0

This release refactors the internals of `starlette-admin` and introduces a large set of new features. While the high-level API remains largely unchanged, the most significant update is the rewrite of the list page rendering. We have dropped DataTables in favor of a server-rendered table. Most other updates consist of renames or minor signature changes.

This guide covers every breaking change in the order you are most likely to encounter them. Each section compares the old API alongside its replacement. If your implementation relies on the basics or light customizations (such as an `Admin` instance, a few `ModelView` subclasses, `fields`, and `searchable_fields`), your migration will likely be limited to the [Requirements](#requirements) and [Admin Constructor](#the-admin-constructor) sections, plus a few renames.

Customizations of the old list page require the most attention. DataTables options and JavaScript render functions have no direct equivalent and must be ported to server-side templates (see [DataTables Removal](#datatables-removal)).

!!! tip
    Upgrade your dependencies in one step and start your application. Most removed or renamed attributes raise clear errors at startup rather than failing silently at runtime.

### What's New

Beyond the breaking changes outlined below, this release includes:

* **Native list tables:** DataTables has been removed in favor of a built-in, server-rendered implementation. Table state is now entirely URL-driven, meaning all page, filter, and sort configurations are immediately shareable and bookmarkable.
* **[Filters](user-guide/filters.md):** A nested `AND`/`OR` filter builder replaces the DataTables SearchBuilder. Filters are derived from field types and are fully extensible in pure Python. You can write a filter class without needing any JavaScript.
* **[Import and Server-Side Export](user-guide/export-import.md):** Enjoy CSV/JSON import capabilities with per-row error reporting, alongside server-side exporters (CSV, JSON, Excel, PDF, etc.) that replace client-side DataTables buttons.
* **[Events](advanced/events.md):** Subscribe to lifecycle hooks like `before_create`, `after_edit_committed`, `after_login`, and various action events.
* **[Themes](advanced/custom-themes.md) and [Plugins](advanced/plugins.md):** Package and reuse custom aesthetics and behaviors. Cookiecutter templates are available to help you get started quickly.
* **[Widgets and Dashboards](user-guide/custom-views.md):** Build index pages and custom views using `StatWidget`, `ChartWidget`, `TableWidget`, and more.
* **[Form Layout](advanced/form-layout.md):** Arrange create/edit forms logically using rows, columns, fieldsets, and tabs.
* **[Inline Edit](user-guide/inline-edit.md):** Edit a single field directly from the list page.
* **[Inline Forms](user-guide/inline-forms.md):** Edit related models inside a parent form using `InlineModelView`.
* **Other Enhancements:** [Flash messages](user-guide/flash-messages.md), [OAuth login](user-guide/auth.md), a [Tortoise ORM backend](integrations/tortoise.md), new fields (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), field-level `validators`, and clipboard copy functionality on any field.
* **Expanded Test Coverage:** The test suite is now substantially larger, featuring Playwright end-to-end tests that validate critical workflows across the admin interface.

### Requirements

* **Python Support:** Python 3.11 or newer is required. Support for Python 3.9 and 3.10 has been dropped.
* **Core Dependencies:** `itsdangerous` is now a core dependency used to sign admin cookies (CSRF tokens and flash messages).
* **New Optional Extras:**

 | Extra | Enables |
    | --- | --- |
    | `starlette-admin[email]` | `EmailField` server-side validation via `email-validator` |
    | `starlette-admin[pdf]` | PDF export via `reportlab` |
    | `starlette-admin[s3]` | S3 file storage via `aiobotocore` |
    | `starlette-admin[tinymce]` | `TinyMCEEditorField` HTML sanitization via `nh3` |
    | `starlette-admin[i18n]` | Translations via `babel` (unchanged) |

* **Beanie Backend:** Beanie 2.0+ is required.
* **Odmantic Backend:** Removed. Odmantic is no longer actively maintained. If you depend on it, stay on `starlette-admin<=0.17.1` or migrate to Beanie for MongoDB support.

### The Admin Constructor

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` is renamed to `static_dir`.
* **Set a `secret_key`.** This key signs the CSRF and flash-message cookies. If omitted, a random key generates at startup (which is fine for development). However, signed values will be invalidated on every restart and across multiple workers. Always pass a stable secret in production.
* `logo_url`, `login_logo_url`, and `favicon_url` now accept a callable `(request) -> str | None`. This replaces the per-request branding previously provided by `AdminConfig`.
* **New optional parameters:** `theme`, `plugins`, `additional_loaders`, `import_config`, and `export_config`.
* **SQLAlchemy specifics:** The first argument is now `session_provider`. It accepts an `Engine` or `AsyncEngine`, and now also accepts a `sessionmaker` or `async_sessionmaker`. Existing `Admin(engine)` calls will continue to work.
* `timezone_config` defaults to `TimezoneConfig()` instead of `None`. Datetimes now display in the viewer's local timezone by default. Pass `timezone_config=None` to retain raw values.

### Renamed View Identifiers

The naming convention for views is now unified. Update your `ModelView` constructors and class attributes accordingly:

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

Note that `Link` and `DropDown` also use `menu_label` instead of `label`.

### DataTables Removal

The list page no longer uses DataTables. The attributes that previously configured it have been removed entirely:

| Removed | Replacement |
| --- | --- |
| `datatables_options` | None. The table is server-rendered. Customize via templates. |
| `search_builder` | The new [filter builder](user-guide/filters.md), enabled by `searchable_fields`. |
| `responsive_table` | None. The table handles overflow natively. |
| `save_state` | Always on. List state (page, sort, filters, search, visible columns) now lives in the URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (a list of filter classes). |
| `BaseField.render_function_key` | `BaseField.list_template` (server-side Jinja template). |

If you previously wrote custom JavaScript render functions or DataTables plugins, port them to `list_template` overrides. Each field now renders its list cell directly from `templates/fields/list/*.html`.

### Actions

Batch action handlers now receive an `ActionSelection` object instead of a list of primary keys. This supports the new "select all matching" banner, targeting every row that matches the current filter without materializing them on the client side.

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

* Methods like `selection.rows()`, `selection.pks()`, and `selection.count()` resolve target rows lazily. This applies whether the user checked rows individually or selected all matching rows.
* Properties like `selection.is_select_all`, `selection.filters`, and `selection.q` allow you to push the operation down as a single bulk query.
* Returning a success message string is replaced by [flash messages](user-guide/flash-messages.md).
* Row action handlers retain their original `(request, pk)` signature.
* **New `@action` options:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size`, and per-request `form` callables.

### Authentication

The `starlette_admin/auth.py` module is now the `starlette_admin.auth` package. Existing imports from `starlette_admin.auth` will continue to work, but the provider contract has changed.

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

* The methods `is_authenticated`, `get_admin_user`, and `get_admin_config` are merged into a single `authenticate(request) -> AdminUser | None` method. Returning `None` indicates an unauthenticated state.
* The `login` and `logout` methods no longer receive or return the prepared `response`. Return `None` for the default redirect, or return a custom `Response` to override this behavior.
* `AdminConfig` is removed. Handle per-request titles and logos using the callable form of `logo_url` and `login_logo_url` on the `Admin` instance.
* A built-in [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) handles OAuth2/OIDC login flows out of the box.
* The `login_not_required` decorator remains unchanged.

### Export and Import

Exports have moved from client-side DataTables buttons to server-side streaming endpoints. Import functionality is entirely new, and `ExportType` no longer exists.

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

* `export_types` is now `exporters`. This accepts a list of format names or `BaseExporter` instances. Supported built-ins include `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml`, and `pdf`. Formats other than `csv` or `json` require `tablib`, and PDF requires the `pdf` extra.
* `export_fields` (an include list) is replaced by `exclude_fields_from_export` (an exclude list). This matches the naming convention of other `exclude_fields_from_*` attributes.
* Fields also accept `exclude_from_export` and `exclude_from_import` on an individual basis.
* Configure global limits using `ExportConfig` and `ImportConfig` on the `Admin` instance. Refer to the [Export & Import](user-guide/export-import.md) documentation for details.

### Custom Fields and Template Overrides

Field templates are now reorganized. Update your paths if you override built-in templates or ship custom fields:

| Before | After |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (client-side render function) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (path) | Same attribute name, new path prefix `fields/form/` |

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

New per-field capabilities to explore include `validators`, `filters`, `default`, hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard`, and an `extra` dictionary for arbitrary metadata. Review the [Custom Fields](advanced/custom-fields.md) documentation for more information.

### CustomView

The `CustomView` class no longer accepts `template_path` and `methods`. Build simple pages using [widgets](user-guide/custom-views.md). For pages requiring full control, subclass `CustomView` and declare your routes directly.

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

The `@route` decorator also allows any view to expose extra endpoints for requirements like JSON chart data or webhooks.

### Custom Backends

If you implemented `BaseModelView` against a custom datasource, note the updated data-access contract:

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

* The string-typed `where` parameter is split into `q` (for full-text search terms) and `filters` (a typed `FilterGroup` tree provided by the filter builder).
* The `order_by` parameter (previously a list of `"field direction"` strings) is now `sorts`, taking a list of `(field_name, direction)` tuples.
* Each backend now ships with a filter registry mapping field types to filter implementations. Check the [Custom Backend](integrations/custom-backend.md) documentation for the full contract and a working example.

### Behavior Changes to Review

* **Timezones:** Datetimes render in the viewer's local timezone by default (see the `timezone_config` note in the Admin Constructor section).
* **URL State:** List state now lives in the URL. Bookmarked admin URLs from previous versions will land on default list states, because saved DataTables states are not migrated.
* **Email Validation:** `EmailField` now validates on the server when `email-validator` is installed.
* **CSRF Protection:** CSRF protection is built-in and cookie-based. If you previously wrapped the admin with custom CSRF middleware, you can safely remove it. Ensure your `secret_key` is set so tokens survive server restarts.
* **FileField Upload Size:** `FileField.max_size` now defaults to 50 MB instead of unlimited. Pass `max_size=None` to restore the old unbounded behavior, or set an explicit value to change the cap.

### Removed with No Replacement

* `AdminConfig` (see [Authentication](#authentication)).
* `datatables_options`, `responsive_table`, and `save_state` (see [DataTables Removal](#datatables-removal)).
* The Odmantic backend (see [Requirements](#requirements)).

## Getting Help

If you encounter a migration issue not covered in this guide, please [open an issue](https://github.com/jowilf/starlette-admin/issues). Include a minimal reproduction of the problem and specify the version you are upgrading from.
