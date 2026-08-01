---
title: Templates
description: Override Jinja2 templates in starlette-admin to completely customize the HTML structure of specific views or fields.
---

# Templates

Every page in the admin interface is a Jinja2 template you can override. Whether you need to customize a single list page, a specific field's table cell, or a dashboard widget, you can apply your changes without forking the built-in template tree.

## How the Template Loader Works

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

The `Admin` class builds a Jinja2 `ChoiceLoader` that evaluates paths in a specific order: it checks your `templates_dir` first, followed by the built-in `starlette_admin/templates/` package directory. If you place a file under `my_templates/` using the exact relative path it has inside `starlette_admin/templates/`, your file shadows the built-in version. All other templates will continue to render from the built-in directory.

!!! note
    The loader chain also registers a `PrefixLoader` under the key `@starlette-admin` that always resolves to the built-in templates, regardless of any files shadowing them in `templates_dir`. You can access these using the path format `@starlette-admin/<name>.html` (omitting the trailing slash on the prefix itself). See [Overriding a Single Page Template](#overriding-a-single-page-template) below for practical applications.

## Template Directory Map

| Path | Rendered for |
| --- | --- |
| `base.html` | Outer HTML layout (`<html>`, `<head>`, scripts) |
| `layout.html` | Sidebar and topbar chrome (extends `base.html`) |
| `index.html` | Dashboard or home page |
| `list.html` | Model list page (table, filter bar, pagination) |
| `detail.html` | Detail (read-only) view of one record |
| `create.html` | Create form |
| `edit.html` | Edit form |
| `login.html` | Login page |
| `error.html` | HTTP error page (403, 404, etc.) |
| `actions.html` | Bulk-action modal |
| `row-actions.html` | Per-row action dropdown |
| `inline.html` | Inline formset on create/edit page |
| `inline_detail.html` | Inline table on detail page |
| `inline_row.html` | Single row inside an inline formset |
| `_filter_bar.html` | Active filter chips bar above the list |
| `_filter_builder.html` | Filter builder modal |
| `_pagination.html` | Pagination controls |
| `_column_header.html` | Sortable column header cell |
| `_form_footer.html` | Save, Save and continue, or Add another buttons |
| `_form_group.html` | A single [form layout](form-layout.md) group's fieldset on the create/edit form |
| `_form_group_fields.html` | The field inputs rendered inside a form layout group |
| `fields/list/<type>.html` | List column cell for a field type |
| `fields/detail/<type>.html` | Detail page display for a field type |
| `fields/form/<type>.html` | Form input widget for a field type |
| `widgets/<name>.html` | Dashboard widget template |
| `modals/actions.html` | Action confirmation modal |
| `modals/delete.html` | Delete confirmation modal |
| `modals/error.html` | Error modal |
| `modals/import.html` | Import modal |
| `macros/views.html` | Shared Jinja2 macros used across pages |

!!! note
    The built-in tree also includes `modals/loading.html` (a generic loading-state modal) and several field-specific templates in `fields/list/`, `fields/detail/`, and `fields/form/`. Verify the exact filenames in `starlette_admin/templates/` for your installed version before attempting to override generic `<type>.html` files.

## Overriding a Single Page Template

```
my_templates/
└── list.html   ← shadows the built-in list.html

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Custom banner above the list.</div>
  {{ super() }}
{% endblock %}

```

Using `{% extends "list.html" %}` directly would resolve back to your custom `my_templates/list.html` because the `templates_dir` is checked first. This circular reference causes an infinite recursion error. The `@starlette-admin/` prefix always points to the built-in copy. Therefore, any `extends` or `include` statements inside an override must use this prefix instead of the bare filename.

## Overridable Blocks

Every built-in page extends `layout.html`, which in turn extends `base.html`. By overriding a specific `{% block %}` instead of an entire file, you can customize a specific fragment without duplicating the rest of the page's code:

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Custom report</a>
{% endblock %}

```

### `base.html`

| Block | Contains |
| --- | --- |
| `favicon` | The favicon `<link>` tag |
| `title` | The `<title>` tag |
| `head_meta` | The `<meta>` tags within the `<head>` element |
| `head_css` | Stylesheet `<link>` tags |
| `head` | A free-form insertion point within the `<head>` element |
| `body` | The entire `<body>` content (this is overridden by `layout.html`) |
| `modal` | A page-level insertion point for modals |
| `script` | The `<script>` tags located just before the closing `</body>` tag |
| `tail` | An empty insertion point at the very end of `<body>`, after `script` |

### `layout.html`

| Block | Contains |
| --- | --- |
| `sidebar` | The entire sidebar `<aside>` element (including the nav brand, menu, and footer) |
| `brand` | The logo image (or `app_title` fallback) inside the sidebar's nav brand link |
| `sidebar_menu` | The list of view links inside the sidebar |
| `sidebar_footer` | The bottom area of the sidebar |
| `user_menu_trigger` | The avatar and username shown on the user-menu button. Defined once and reused on both the mobile sidebar and desktop navbar via `self.user_menu_trigger()`, so overriding it updates both |
| `user_menu_items` | The dropdown items located in the user menu |
| `navbar` | The top navigation bar |
| `navbar_extra` | Additional content placed in the navbar next to the user menu |
| `header` | The page header area positioned above `content` (includes the title and breadcrumbs) |
| `flash_messages` | The designated area for rendering flash messages |
| `content_before` | An insertion point immediately preceding `content` |
| `content` | The main page content (this is the block populated by `list.html`, `detail.html`, etc.) |
| `content_after` | An insertion point immediately following `content` |
| `page_footer` | The footer area located below the page content |

### `list.html`

| Block | Contains |
| --- | --- |
| `header` | The page header (includes the title and breadcrumbs) |
| `page_title` | The `<h1>` heading inside the header |
| `breadcrumbs` | The breadcrumb trail inside the header |
| `modal` | The delete, action, and import modals |
| `content` | The complete body of the list page |
| `list_search` | The search input area |
| `list_toolbar` | The toolbar row containing filters, export, import, and create buttons |
| `list_toolbar_extra` | An extra insertion point at the very end of the toolbar |
| `list_before_table` | An insertion point preceding the table |
| `list_table` | The `<table>` element itself |
| `list_header` | The `<thead>` row containing the checkbox and column header cells |
| `list_row` | A single `<tr>` in the results table (a scoped block; has access to `row`, `row_pk`, and `row_clickable`) |
| `list_row_actions_before` | The row-actions cell when `row_actions_position` is `BEFORE_COLUMNS` (a scoped block) |
| `list_row_actions_after` | The row-actions cell when `row_actions_position` is `AFTER_COLUMNS` (a scoped block) |
| `list_empty` | The "No data" placeholder (a scoped block rendered for empty states) |
| `list_after_table` | An insertion point following the table |
| `list_footer` | The pagination and range footer |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `detail.html`

| Block | Contains |
| --- | --- |
| `header` | The page header (includes the title, breadcrumbs, and actions) |
| `page_title` | The `<h1>` heading inside the header |
| `breadcrumbs` | The breadcrumb trail inside the header |
| `modal` | The delete and action modals |
| `content` | The complete body of the detail page |
| `detail_before` | An insertion point preceding the detail card |
| `detail_title` | The title area inside the detail card |
| `detail_actions` | The action buttons inside the detail card |
| `details_table` | The primary field and value table |
| `detail_after` | An insertion point following the detail card |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `create.html` / `edit.html`

| Block | Contains |
| --- | --- |
| `header` | The page header (includes the title and breadcrumbs) |
| `page_title` | The `<h1>` heading inside the header |
| `breadcrumbs` | The breadcrumb trail inside the header |
| `content` | The complete body of the form page |
| `form_before` | An insertion point preceding the form card |
| `create_card_header` / `edit_card_header` | The header area inside the form card |
| `create_form` / `edit_form` | The [form layout](form-layout.md) groups (each rendered via `_form_group.html`) and their field input elements |
| `create_inlines` / `edit_inlines` | The inline formset area |
| `form_footer` | The Save, Save and continue, and Add another buttons |
| `form_after` | An insertion point following the form card |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `login.html`

| Block | Contains |
| --- | --- |
| `header` / `sidebar` | Left empty (the login page hides the standard application chrome) |
| `content` | The complete body of the login page |
| `login_logo` | The logo displayed above the login form |
| `login_title` | The title text of the login page |
| `login_form_before` | An insertion point preceding the form fields |
| `login_fields` | The username and password input fields |
| `login_form_footer` | An insertion point after the fields but within the form |
| `login_card_footer` | An insertion point located directly below the login card |
| `script` | Page-specific script additions |

### `index.html`

| Block | Contains |
| --- | --- |
| `head_css` | Widget-specific stylesheet additions |
| `content` | The dashboard widget grid |
| `script` | Widget-specific script additions |

### `error.html`

| Block | Contains |
| --- | --- |
| `header` / `sidebar` | Left empty (the error page hides the standard application chrome) |
| `content` | The error message and associated actions |
| `error_actions` | Action buttons displayed below the error message (such as a "Go back" button) |

!!! tip
    Call `{{ super() }}` inside an override to retain the built-in block's existing content and append to it, rather than replacing it entirely. This pattern is demonstrated in the `list_toolbar_extra` example above, and it is also used internally by the built-in `index.html` and `create.html` files for the `head_css` block.

### Example: Replacing the Sidebar Logo with an Inline SVG

Passing a URL to `Admin(logo_url=...)` is the quickest way to set a logo and covers most use cases, including linking to external `.svg` files. However, the built-in template renders this URL inside a standard `<img>` tag, which restricts the SVG from inheriting CSS properties from the surrounding page.

**When to use this approach:** Override the `brand` block to inject **inline `<svg>` markup** when you need the logo to dynamically interact with the UI.

#### Implementation

Create a `layout.html` file in your custom templates directory. Since every page in the admin interface inherits from `layout.html`, this single override applies sitewide.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! note "Best Practice:"
    Always retain the `navbar-logo` CSS class on your custom `<svg>` element. This ensures your inline graphic inherits the framework's built-in alignment, padding, and sizing constraints without requiring additional custom CSS.

## Overriding Field Templates

Each field context utilizes three sub-directories:

| Directory | Used in |
| --- | --- |
| `fields/list/<type>.html` | List table cell (compact, read-only) |
| `fields/detail/<type>.html` | Detail page display (full, read-only) |
| `fields/form/<type>.html` | Create and edit form input |

You can override the cell used for text fields without affecting the form or the detail display:

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

To point a specific **field instance** to your custom template instead of overriding the type globally, set `list_template`, `detail_template`, `form_template`, `null_template`, or `empty_template` directly on the field definition:

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (default `"fields/detail/_null.html"`) and `empty_template` (default `"fields/detail/_empty.html"`) are separate slots rendered on the list and detail pages in place of `list_template` or `detail_template`, whenever the field's value is `None` or an empty list/tuple respectively:

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Overriding Widget Templates

You can apply the exact same override pattern for widgets by placing files under the `widgets/` directory:

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Global Template Variables

These variables are available in every template without being passed explicitly. The `Admin` class installs them as Jinja2 globals once during setup:

| Variable | Type | Description |
| --- | --- | --- |
| `views` | `list[BaseView]` | All registered views (used to render the sidebar) |
| `app_title` | `str` | The admin's title (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True` if an auth provider is configured |
| `__name__` | `str` | The admin's route name prefix (e.g., `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL for a built-in static asset. The `v` argument appends a `?v=` cache-busting query parameter. |
| `logo_url` | `callable` | `logo_url(request)` → URL for the sidebar logo, or `None` if unset |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL for the login page logo, or `None` if unset |
| `favicon_url` | `callable` | `favicon_url(request)` → URL for the favicon, or `None` if unset |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL with `overrides` merged into its query string (used for sort, pagination, or search links). Pass `None` to drop a key. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL of a record's detail page |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL of a record's edit page |
| `export_url` | `callable` | `export_url(request, key, fmt)` → Export download URL carrying the current list page's filter/sort/search state |
| `import_url` | `callable` | `import_url(request, key)` → Import POST URL |
| `get_locale` | `callable` | `get_locale()` → Active locale string (requires no `request` argument) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Human-readable name of a locale string |
| `i18n_config` | `I18nConfig` | The admin's i18n configuration object |
| `get_timezone` | `callable` | `get_timezone()` → Active timezone string (requires no `request` argument) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Human-readable name of a timezone string |
| `timezone_config` | `TimezoneConfig | None` | The admin's timezone configuration |
| `theme_settings` | `TablerSettings` | Active Tabler theme configuration (base, primary, radius, mode) exposed by `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Renders the hidden CSRF `<input>` |

!!! note
    Functions like `get_locale`, `get_locale_display_name`, `get_timezone`, and `get_timezone_display_name` do not take a `request` parameter. Locale and timezone are read from `contextvars` populated by `LocaleMiddleware` for the duration of the request rather than being looked up on the `Request` object itself.

## Per-Page Context Variables

Beyond the global variables above, each page passes its own context dictionary to `TemplateResponse`.

### `list.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | The current view |
| `title` | `str` | Page title |
| `fields` | `list[BaseField]` | Currently visible columns |
| `all_fields` | `list[BaseField]` | All list fields (including hidden ones) |
| `rows` | `list[dict]` | Serialized row data |
| `total` | `int` | Total matching records for pagination |
| `total_pages` | `int` | Total page count |
| `range_start` | `int` | First record number on this page (1-based) |
| `range_end` | `int` | Last record number on this page |
| `list_params` | `ListParams` | Parsed URL state (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Evaluates to `"and"` or `"or"` for the active top-level filter group |
| `filter_chips` | `list` | Active filter chip descriptors |
| `filter_builder_fields` | `list` | Fields available in the filter builder UI |
| `raw_filter` | `str | None` | Raw JSON filter string from the URL |
| `_actions` | `list` | Available bulk actions |
| `row_actions` | `dict[Any, list]` | Available row actions per record, keyed by pk |

### `detail.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | The current view |
| `title` | `str` | Page title |
| `obj` | `dict` | Serialized record |
| `raw_obj` | `Any` | The raw model object before serialization |
| `inlines` | `list[dict]` | Inline context (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Available row actions |

### `create.html` / `edit.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | The current view |
| `title` | `str` | Page title |
| `obj` | `dict` | Current field values (defaults on create, existing values on edit) |
| `raw_obj` | `Any` | Raw model object (edit only, absent on create) |
| `errors` | `dict[str, list[str]]` | Validation errors keyed by field name (only present after a failed submit) |
| `inlines` | `list[dict]` | Inline formset context |

## Adding Your Own Globals and Filters

You can inject custom variables and functions into your templates by subclassing `Admin` and overriding `__init__`. Be sure to call `super().__init__()` first so `self.templates` is set up before you add to it:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## Built-in Jinja2 Filters

These filters are registered automatically on every admin instance during `_setup_templates`:

| Filter | Signature | Description |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | Returns `True` if the resource is a `CustomView` |
| `is_link` | `view | is_link` | Returns `True` if the resource is a `Link` |
| `is_model_view` | `view | is_model_view` | Returns `True` if the resource is a `BaseModelView` |
| `is_dropdown` | `view | is_dropdown` | Returns `True` if the resource is a `DropDown` |
| `tojson` | `value | tojson` | HTML-safe JSON serialization (replaces Jinja2's default `tojson`) |
| `file_icon` | `mime_type | file_icon` | Returns a full icon class for a MIME type (e.g., `application/pdf` → `fa-solid fa-fw fa-file-pdf`); override `self.templates.env.filters["file_icon"]` to use your own icon set |
| `to_view` | `key | to_view` | Looks up a registered `BaseModelView` by its key string; raises a 404 `HTTPException` if not found |
| `is_iter` | `value | is_iter` | Returns `True` if value is a `list` or `tuple` |
| `is_str` | `value | is_str` | Returns `True` if value is a `str` |
| `is_dict` | `value | is_dict` | Returns `True` if value is a `dict` |
| `ra` | `value | ra` | Converts a string to a `RequestAction` enum member |
| `safe_url` | `url | safe_url` | Returns the URL only if it passes the safe-URL check, otherwise returns `""` |
| `sanitize_html` | `html | sanitize_html` | Strips disallowed tags from an HTML string and returns a `Markup` |

---

**What's Next**

* **[Form Layout](form-layout.md):** Split the create/edit forms into titled, optionally collapsible groups, and override `_form_group.html` to customize their markup.
* **[Custom Themes](custom-themes.md):** Restyle the admin interface without altering individual templates.
* **[Custom Fields](custom-fields.md):** Pair a field's Python class with its own specific `list_template` or `form_template`.
* **[Extension Points](extension-points.md):** Review the full list of pluggable configuration surfaces beyond basic templates.
