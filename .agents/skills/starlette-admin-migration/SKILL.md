---
name: starlette-admin-migration
description: Migrate an application from starlette-admin 0.17.x to 1.0.0. Use when upgrading starlette-admin, fixing breaking changes after a version bump, or when errors mention removed attributes such as statics_dir, identity, datatables_options, ExportType, search_builder, display_template, is_authenticated, or AdminConfig.
---

# Migrate starlette-admin 0.17.x to 1.0.0

Apply every breaking change from the official migration guide, published at https://jowilf.github.io/starlette-admin/migration/. For feature work after the upgrade, use the `starlette-admin` skill.

## Workflow

1. Locate all code using starlette-admin: `grep -rl "starlette_admin" --include="*.py"`. Also search template directories for overridden admin templates.
2. Run the detection greps below to build the list of impacted call sites before editing anything.
3. Apply the transformations section by section. Mechanical renames first, then behavioral changes.
4. Flag anything under "Needs human decision" to the user instead of guessing.
5. Start the app once after migrating: removed or renamed attributes raise clear errors at startup rather than failing silently at runtime.

## Step 0: Requirements

* Python 3.11+ is required. Check `pyproject.toml` / `setup.cfg` and CI matrices for 3.9 or 3.10.
* Beanie backend requires Beanie 2.0+.
* Odmantic backend is removed. If the code imports `starlette_admin.contrib.odmantic`, stop and tell the user: stay on `starlette-admin<=0.17.1` or migrate models to Beanie.
* New extras to add when the feature is used: `email` (EmailField server-side validation), `pdf` (PDF export), `s3` (S3 file storage), `tinymce` (HTML sanitization).

## Step 1: Admin constructor

Detect: `grep -rn "statics_dir\|Admin(" --include="*.py"`

* `statics_dir` becomes `static_dir`.
* Add `secret_key=...` sourced from the environment. It signs CSRF and flash cookies. Without it, signed values invalidate on restart and break across workers.
* `timezone_config` now defaults to `TimezoneConfig()`. Datetimes render in the viewer's local timezone. Pass `timezone_config=None` only if the user needs the old raw display.
* Per-request branding moved from `AdminConfig` to callable `logo_url`, `login_logo_url`, `favicon_url` parameters: `(request) -> str | None`.
* SQLAlchemy: the first argument is now `session_provider` and also accepts a `sessionmaker` or `async_sessionmaker`. Existing `Admin(engine)` calls keep working.

## Step 2: View identifier renames

Detect: `grep -rn "identity=\|label=\|form_include_pk\|identity:\|label:" --include="*.py"`

Apply in `ModelView`, `Link`, `DropDown`, and `CustomView` (constructor args and class attributes):

| Before | After |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

Careful with `name` and `label`: rename them only on view classes, not on fields or actions (`@action(name=..., text=...)` and `BaseField.label` are unchanged).

## Step 3: DataTables removal

Detect: `grep -rn "datatables_options\|search_builder\|responsive_table\|save_state\|render_function_key" --include="*.py"`

| Removed | Replacement |
| --- | --- |
| `datatables_options` | Delete. Table is server-rendered; customize via templates. |
| `search_builder` | Delete. Filter builder is enabled by `searchable_fields`. |
| `responsive_table` | Delete. |
| `save_state` | Delete. List state lives in the URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (list of filter classes). |
| `BaseField.render_function_key` | `BaseField.list_template` (Jinja template under `fields/list/`). |

Custom JavaScript render functions have no direct equivalent. Port their logic to a server-side Jinja template and set `list_template` on the field. Flag each one to the user with the original JS so they can validate the ported template.

## Step 4: Batch actions

Detect: `grep -rn "@action" --include="*.py"`

Batch handlers change from `(self, request, pks: List[Any]) -> str` to `(self, request, selection: ActionSelection) -> None`:

* Replace `await self.find_by_pks(request, pks)` with `await selection.rows()`.
* Replace `len(pks)` with `await selection.count()`; `selection.pks()` returns the keys.
* Replace the returned message string with `flash(request, message)`.
* For bulk pushdown, `selection.is_select_all`, `selection.filters`, and `selection.q` describe the selection without materializing rows.
* Row action handlers (`@row_action`) keep the `(request, pk)` signature. Do not touch them.

## Step 5: Auth providers

Detect: `grep -rn "AuthProvider\|is_authenticated\|get_admin_user\|get_admin_config\|AdminConfig" --include="*.py"`

* Merge `is_authenticated`, `get_admin_user`, and `get_admin_config` into one method: `async def authenticate(self, request) -> AdminUser | None`. Return `None` when unauthenticated.
* `login` and `logout` no longer receive or return `response`. Return `None` for the default redirect or a custom `Response` to override. Raise `LoginFailed` on bad credentials.
* `AdminConfig` is removed. Move per-request titles and logos to callable `logo_url` / `login_logo_url` on `Admin`.
* `login_not_required` is unchanged. A built-in `OAuthProvider` is available for OAuth2/OIDC flows.

## Step 6: Export and import

Detect: `grep -rn "ExportType\|export_types\|export_fields" --include="*.py"`

* `export_types = [ExportType.CSV, ...]` becomes `exporters = ["csv", ...]`. Built-ins: `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml`, `pdf`. Remove the `ExportType` import.
* `export_fields` (include list) becomes `exclude_fields_from_export` (exclude list). Invert the field list against the view's `fields`.
* New capabilities to mention, not auto-add: `importers`, `exclude_fields_from_import`, per-field `exclude_from_export` / `exclude_from_import`, `ExportConfig` / `ImportConfig` on `Admin`.

## Step 7: Custom fields and template overrides

Detect: `grep -rn "display_template\|form_template\|displays/\|forms/" --include="*.py"` and look for template dirs containing `displays/` or `forms/`.

| Before | After |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| client-side render function | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `form_template` path prefix | `fields/form/` |

Move the template files and update the attribute paths together.

## Step 8: CustomView

Detect: `grep -rn "CustomView" --include="*.py"`

`template_path` and `methods` are removed. Two replacement patterns:

* Simple page: pass a `widget=` (for example `StatWidget`, `ChartWidget`, `TableWidget`).
* Full control: subclass `CustomView`, set `menu_label` and `path`, and declare endpoints with `@route`. Render with `self.templates.TemplateResponse(request=request, name=...)`.

Pick based on what the old template did; when unclear, subclass with `@route` since it can render the existing template unchanged.

## Step 9: Custom backends

Detect: `grep -rn "BaseModelView" --include="*.py"` (subclasses implementing `find_all` / `count`).

* `where` splits into `q` (full-text search string) and `filters` (typed `FilterGroup` tree).
* `order_by` (list of `"field direction"` strings) becomes `sorts` (list of `(field_name, direction)` tuples).
* Signatures: `find_all(self, request, skip=0, limit=100, q=None, sorts=None, filters=None)` and `count(self, request, q=None, filters=None)`.

## Behavior changes to report

Include these in the final summary even when no code change is needed:

* Datetimes now display in the viewer's local timezone by default.
* Old bookmarked list URLs fall back to default list state; DataTables saved states are not migrated.
* `EmailField` validates server-side when `email-validator` is installed.
* CSRF protection is built-in and cookie-based. Remove any custom CSRF middleware wrapping the admin, and confirm `secret_key` is set.

## Needs human decision

Ask the user instead of guessing when you find:

* JavaScript render functions or DataTables plugins (Step 3): the ported template needs their review.
* `datatables_options` carrying meaningful config (custom ordering, page lengths): confirm the server-side equivalent they want.
* Odmantic usage: version pin versus Beanie migration.
* Missing `secret_key` source: which env var or settings entry to use.
