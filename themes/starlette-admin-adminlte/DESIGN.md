# AdminLTE 4 Theme for starlette-admin

Design for `starlette-admin-adminlte`: a complete layout theme that replaces
the default Tabler shell with [AdminLTE 4](https://adminlte.io) while every
view, field, filter, row action, and route keeps working untouched.

```python
from starlette_admin_adminlte import AdminlteTheme

admin = Admin(engine, theme=AdminlteTheme(skin="dark"))
```

The theme travels in `Admin(theme=...)`, consistent with the theme system in
`ai/THEME_DESIGN.md`. One line, one shell swap, done.

## Design principle: blocks-first

The overriding constraint is: **minimize rewriting HTML from scratch**. Use
Jinja block inheritance first; add blocks to core if that is the cheapest way
to make a clean override; rewrite a template only when its DOM structure is
fundamentally incompatible.

The reason this works at all is that **Tabler and AdminLTE 4 are both built
on Bootstrap 5**. Every page body in starlette-admin (list, detail, create,
edit, dashboard, login) draws its visual structure from Bootstrap component
classes (`card`, `card-header`, `card-body`, `btn`, `form-control`, `table`,
`dropdown`, `breadcrumb`, `alert`, `pagination`, `input-group`, ...). Those
classes render identically under AdminLTE 4 because AdminLTE IS Bootstrap
plus a layout layer on top. The differences live in the **shell** (the
sidebar/navbar/content wrapper) and in a set of **Tabler-specific utility
classes** sprinkled through the page bodies. Both are addressable without
rewriting the page bodies.

### Three mechanisms, in priority order

1. **Block override** (cheapest). Extend `@core/base.html` and override named
   blocks (`core_css`, `core_js`, `icon_css`, `fonts`) to swap frameworks.
   This reskins the entire admin through the asset pipeline, no HTML rewrite.

2. **CSS compatibility shim** (medium). For Tabler-specific utility classes
   that core page bodies use (`row-deck`, `btn-list`, `container-tight`,
   `empty`, ...), ship a `tabler-compat.css` that re-implements them on top
   of Bootstrap variables. The page template stays untouched; the classes
   just resolve to equivalent styles.

3. **Full template rewrite** (last resort). When the DOM structure itself is
   incompatible (the shell layout), replace the template entirely while
   preserving the exact same block names so children that extend it keep
   working.

### What gets rewritten vs inherited

| Template | Strategy | Reason |
|----------|----------|--------|
| `base.html` | **Extend** `@core/base.html` + override asset/inline-CSS blocks | Swap Tabler CSS/JS for Bootstrap 5 + AdminLTE 4; drop Tabler-variable select2 CSS |
| `layout.html` | **Full rewrite** | DOM is structurally different: `.app-wrapper` + `.app-sidebar` + `.app-header` + `.app-main` vs Tabler's `.page` + `.navbar-vertical` |
| `macros/views.html` | **Theme-specific** macros file | AdminLTE sidebar-menu tree (`nav sidebar-menu`, `nav-treeview`, `nav-icon`, `nav-arrow`) differs from Tabler's flat `navbar-nav` |
| `list.html` | **Inherit** (no override) | Bootstrap card/table/btn classes render correctly under AdminLTE; Tabler-specific classes shimmed via CSS |
| `detail.html` | **Inherit** | Same reasoning |
| `create.html` | **Inherit** | Same reasoning |
| `edit.html` | **Inherit** | Same reasoning |
| `index.html` | **Inherit** | Renders `widget_html`; widgets use Bootstrap card classes |
| `login.html` | **Inherit** + CSS shim | `container-tight` and `navbar-brand-autodark` are shimmed; form uses Bootstrap classes |
| `error.html` | **Inherit** + CSS shim | `empty` family shimmed with Bootstrap equivalents |
| Field templates | **Inherit** | `fields/list/*`, `fields/detail/*`, `fields/form/*` use Bootstrap form classes |
| Widget templates | **Inherit** | `widgets/*` use Bootstrap card classes; `subheader` shimmed |
| Partial templates | **Inherit** | `_pagination`, `_form_footer`, `_filter_bar`, `_filter_builder`, `_list_row`, `actions`, `row-actions` all use Bootstrap classes |

Result: **2 templates rewritten** (base.html extended, layout.html replaced),
**1 macros file added**, **0 page templates rewritten**. Every page body is
inherited from core through block inheritance and styled via the CSS shim.

## Framework mapping: Tabler to AdminLTE 4

### Shell structure

```
Tabler (current)                      AdminLTE 4 (target)
─────────────────────                 ─────────────────────────────
<body>                                <body class="layout-fixed
<div class="page">                         sidebar-expand-lg
  <aside                                  bg-body-tertiary">
    class="navbar navbar-vertical">    <div class="app-wrapper">
    brand + sidebar_menu                 <nav class="app-header
  <header                                       navbar navbar-expand
    class="navbar navbar-expand-md">            bg-body">
    navbar_extra + user menu              sidebar toggle + navbar_extra
  <div class="page-wrapper">              + user menu
    <div class="page-header">            <aside class="app-sidebar
      header block                              bg-body-secondary
    <div class="page-body">                     shadow">
      <div class="container-xl">           sidebar-brand (brand block)
        flash_messages                    sidebar-wrapper
        content                                 sidebar_menu block
      page_footer                         sidebar_footer block
                                         <main class="app-main">
                                           <div class="app-content-header">
                                             header block
                                           <div class="app-content">
                                             <div class="container-fluid">
                                               flash_messages
                                               content
                                               page_footer
```

Key structural differences that force a layout.html rewrite:

1. **Wrapper**: Tabler wraps everything in `.page`; AdminLTE uses
   `.app-wrapper` as a CSS grid/flex container for header + sidebar + main.
2. **Header position**: Tabler puts the top navbar inside `.page-wrapper`,
   after the sidebar. AdminLTE puts `.app-header` at the top of
   `.app-wrapper`, before the sidebar. The DOM order matters for CSS grid
   layout.
3. **Sidebar toggle**: Tabler uses Bootstrap collapse
   (`data-bs-toggle="collapse"`). AdminLTE uses its own JS
   (`data-lte-toggle="sidebar"`) and renders the sidebar as a push overlay
   on mobile, not a collapse.
4. **Content wrapper**: Tabler uses `.page-wrapper` > `.page-body` >
   `.container-xl`. AdminLTE uses `.app-main` > `.app-content-header` +
   `.app-content` > `.container-fluid`.
5. **Menu**: Tabler renders a flat `navbar-nav` with `dropdown-toggle` for
   groups. AdminLTE renders `nav sidebar-menu` with `data-lte-toggle="treeview"`
   for collapsible tree items, including `nav-icon`, `nav-arrow`, and
   `nav-treeview` for submenu containers.

### Block contract preserved

Despite the DOM rewrite, every Jinja block that page templates depend on is
provided with the same name and semantics:

| Block | Tabler location | AdminLTE location |
|-------|----------------|-------------------|
| `sidebar` | `<aside class="navbar-vertical">` | `<aside class="app-sidebar">` |
| `brand` | `.navbar-brand > .brand-link` | `.sidebar-brand > .brand-link` |
| `sidebar_menu` | `.collapse > ul.navbar-nav` | `.sidebar-wrapper > nav > ul.sidebar-menu` |
| `sidebar_footer` | after `.collapse` | after `.sidebar-wrapper` |
| `navbar` | `<header class="navbar">` | `<nav class="app-header">` |
| `navbar_extra` | `.navbar-nav > .navbar_extra` | `.navbar-nav > .navbar_extra` |
| `user_menu_trigger` | avatar + username | avatar + username |
| `user_menu_items` | logout dropdown | logout dropdown |
| `header` | `.page-header > .container-xl` | `.app-content-header > .container-fluid` |
| `flash_messages` | before `content` | before `content` |
| `content_before` | before `content` | before `content` |
| `content` | `.page-body > .container-xl` | `.app-content > .container-fluid` |
| `content_after` | after `content` | after `content` |
| `page_footer` | after `.page-body` | after `.app-content` |

Page templates (`list.html`, `detail.html`, etc.) extend `layout.html` by
bare name. Through the loader chain (user > theme > plugins > core), they
resolve to the theme's `layout.html`, inheriting the AdminLTE shell while
populating the same `content`, `header`, `modal`, `head_css`, and `script`
blocks. No page template is aware that a different shell renders it.

## Core changes required

All changes are **additive**. None break the default Tabler theme or any
existing user override. Each adds a named block where a hardcoded Tabler
construct currently prevents clean theme overrides.

### 1. `base.html`: `body_attributes` block

AdminLTE 4 requires body classes (`layout-fixed`, `sidebar-expand-lg`,
`bg-body-tertiary`) for the layout to function. Today the `<body>` tag has
no extension point.

```jinja
{# starlette_admin/templates/base.html #}
- <body>
+ <body{% block body_attributes %}{% endblock %}>
```

The default block renders nothing, so the Tabler shell is unaffected. The
theme overrides it:

```jinja
{# starlette_admin_adminlte/templates/base.html #}
{% block body_attributes %} class="layout-fixed sidebar-expand-lg bg-body-tertiary"{% endblock %}
```

### 2. `base.html`: `core_inline_css` block

`base.html` currently has two inline `<style>` blocks that are NOT wrapped
in any block:

1. `.navbar-logo` / `mark` styles (between `fonts` and `plugin_css`).
2. Select2 integration CSS (between `plugin_css` and `head`), which
   references `--tblr-*` CSS variables extensively
   (`--tblr-bg-forms`, `--tblr-border-color`, `--tblr-danger`, etc.).
   These variables do not exist outside Tabler; the rules silently produce
   no styling under AdminLTE.

Wrap both in a single named block so a theme can replace them:

```jinja
{# starlette_admin/templates/base.html #}
+ {% block core_inline_css %}
      <style>
          .navbar-logo { width: auto; height: 2rem; }
          .mark, mark { padding: 0em; }
      </style>
      ...
      <style>
          .is-invalid .select2-selection { border-color: var(--tblr-danger) !important; }
          ...full select2 block...
      </style>
+ {% endblock %}
```

The theme overrides `core_inline_css` with its own select2 integration CSS
that references Bootstrap/AdminLTE variables (`--bs-*`, `--lte-*`) instead
of `--tblr-*`, and drops the `.navbar-logo` rule (AdminLTE uses
`.brand-image` instead).

### 3. `login.html`: fix hardcoded icon class

`login.html` has a hardcoded Tabler icon class in the error alert:

```jinja
<i class="ti ti-alert-circle icon"></i>
```

This bypasses the icon abstraction. Every other template uses
`{{ icon('flash.error') }}`. Fix:

```jinja
- <i class="ti ti-alert-circle icon"></i>
+ <i class="{{ icon('flash.error') }}"></i>
```

This is a bug fix, not a theme-specific change: the hardcoded class renders
a broken glyph under any non-Tabler icon set.

### Summary of core diffs

```
starlette_admin/templates/base.html   3 lines changed (2 block wrappers added)
starlette_admin/templates/login.html  1 line changed (icon fixed)
```

No behavioral change for the default theme. No new dependencies. No API
change.

## Theme template plan

### `templates/base.html` (extend `@core/base.html`)

Overrides five blocks and adds one. Does not rewrite the HTML skeleton:

```jinja
{% extends "@core/base.html" %}

{% block body_attributes %}
    class="layout-fixed sidebar-expand-lg bg-body-tertiary"
{% endblock %}

{% block core_css %}
    {# Bootstrap 5 (AdminLTE 4's foundation) #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/vendor/bootstrap/bootstrap.min.css', v=V) }}">
    {# AdminLTE 4 #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/vendor/adminlte/adminlte.min.css', v=V) }}">
    {# Tabler compatibility shim #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/css/tabler-compat.css', v=V) }}">
    {# Theme-specific overrides #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/css/adminlte-theme.css', v=V) }}">
{% endblock %}

{% block icon_css %}
    {# Bootstrap Icons, the AdminLTE 4 icon library #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/vendor/bootstrap-icons/bootstrap-icons.min.css', v=V) }}">
{% endblock %}

{% block fonts %}
    {# AdminLTE 4 uses Source Sans 3; drop Tabler's Inter import #}
    <link rel="stylesheet"
          href="{{ static_url(request, 'plugins/adminlte/vendor/fontsource/source-sans-3.css', v=V) }}">
{% endblock %}

{% block core_inline_css %}
    {# Replace Tabler-variable select2 CSS with Bootstrap-variable equivalents #}
    <style>
        .navbar-logo { width: auto; height: 2rem; }
        .select2-container { width: 100% !important; }
        ...Bootstrap-variable select2 rules...
    </style>
{% endblock %}

{% block head %}
    {# FOUC prevention: resolve dark/light before first paint #}
    <script>
        (() => {
            'use strict';
            const stored = localStorage.getItem('lte-theme');
            const prefersDark = matchMedia('(prefers-color-scheme: dark)').matches;
            let resolved = 'light';
            if (stored === 'dark' || stored === 'light') resolved = stored;
            else if (prefersDark) resolved = 'dark';
            document.documentElement.setAttribute('data-bs-theme', resolved);
            document.documentElement.style.colorScheme = resolved;
        })();
    </script>
{% endblock %}

{% block core_js %}
    <script src="{{ static_url(request, 'js/vendor/jquery.min.js', v='v4.0.0') }}"></script>
    <script src="{{ static_url(request, 'js/vendor/js.cookie.min.js', v='3.0.8') }}"></script>
    {# Bootstrap 5 bundle (includes Popper) #}
    <script src="{{ static_url(request, 'plugins/adminlte/vendor/bootstrap/bootstrap.bundle.min.js', v=V) }}"></script>
    {# AdminLTE 4 JS #}
    <script src="{{ static_url(request, 'plugins/adminlte/vendor/adminlte/adminlte.min.js', v=V) }}"></script>
{% endblock %}
```

What stays from `@core/base.html` unchanged: `<html>` attributes (driven by
`theme_settings.html_attrs()` which renders `data-bs-theme`), `<head>` meta,
favicon, title, `plugin_css`, `plugin_js`, `script`, `tail`, the
`window.StarletteAdmin` icon registry, the CSRF/language/timezone jQuery
setup, and the entire `<body>` > `{% block body %}` structure.

### `templates/layout.html` (full rewrite)

The only fully rewritten template. Produces the AdminLTE 4 shell while
exposing every block the page templates need:

```jinja
{% extends "base.html" %}
{% import "plugins/adminlte/macros/views.html" as menu with context %}
{% if is_auth_enabled and not request.state.is_anonymous %}
    {% set current_user = request.state.admin_user %}
{% endif %}

{% block body %}
<div class="app-wrapper">

    {# ===== Top header (app-header) ===== #}
    {% block navbar %}
    <nav class="app-header navbar navbar-expand bg-body">
        <div class="container-fluid">
            <ul class="navbar-nav">
                {% block navbar_start %}
                    <li class="nav-item">
                        <a class="nav-link" data-lte-toggle="sidebar" href="#"
                           role="button" aria-label="{{ _('Toggle sidebar') }}">
                            <i class="bi bi-list"></i>
                        </a>
                    </li>
                {% endblock %}
            </ul>
            <ul class="navbar-nav ms-auto">
                {% block navbar_extra %}{% endblock %}
                {# language switcher, timezone switcher #}
                {# user menu (user_menu_trigger + user_menu_items) #}
            </ul>
        </div>
    </nav>
    {% endblock %}

    {# ===== Sidebar (app-sidebar) ===== #}
    {% block sidebar %}
    <aside class="app-sidebar bg-body-secondary shadow" data-bs-theme="dark">
        <div class="sidebar-brand">
            <a class="brand-link" href="{{ url_for(__name__ ~ ':index') }}">
                {% block brand %}
                    {% if logo_url(request) %}
                        <img src="{{ logo_url(request) }}" class="brand-image" />
                        <span class="brand-text fw-light">{{ app_title }}</span>
                    {% else %}
                        <span class="brand-text fw-light">{{ app_title }}</span>
                    {% endif %}
                {% endblock %}
            </a>
        </div>
        <div class="sidebar-wrapper">
            <nav class="mt-2" aria-label="{{ _('Main navigation') }}">
                {% block sidebar_menu %}
                    <ul class="nav sidebar-menu flex-column"
                        data-lte-toggle="treeview" data-accordion="false">
                        {% for view in views if view.is_accessible(request) %}
                            {# delegates to theme's macros file #}
                        {% endfor %}
                    </ul>
                {% endblock %}
            </nav>
            {% block sidebar_footer %}{% endblock %}
        </div>
    </aside>
    {% endblock %}

    {# ===== Main content (app-main) ===== #}
    <main class="app-main">
        <div class="app-content-header">
            <div class="container-fluid">
                {% block header %}{% endblock %}
            </div>
        </div>
        <div class="app-content">
            <div class="container-fluid">
                {% block flash_messages %}...{% endblock %}
                {% block content_before %}{% endblock %}
                {% block content %}{% endblock %}
                {% block content_after %}{% endblock %}
            </div>
        </div>
        {% block page_footer %}{% endblock %}
    </main>

</div>
{% endblock %}
```

A new `navbar_start` block holds the left side of the header (sidebar
toggle button). The right side keeps `navbar_extra` for parity. The mobile
user-menu controls (which Tabler renders inside the sidebar) move into the
header under AdminLTE's convention, but `user_menu_trigger` and
`user_menu_items` blocks are defined once and reused exactly as in core.

### `templates/plugins/adminlte/macros/views.html` (theme-specific macros)

Core's `macros/views.html` renders Tabler `navbar-nav` structure
(`nav-item`, `nav-link`, `nav-link-icon`, `nav-link-title`). AdminLTE's
sidebar uses a different structure (`nav-item`, `nav-link`, `nav-icon`,
`<p>` wrapper, `nav-arrow`, `nav nav-treeview` for collapsible submenus).

The theme ships its own macros file, imported by the rewritten
`layout.html`. The macros receive the same `view` objects and use the same
filters (`is_link`, `is_model_view`, `is_dropdown`, `is_custom_view`),
so no Python change is needed:

```jinja
{# macros/views.html #}

{% macro view_link(view) %}
    <li class="nav-item">
        <a href="{{ url_for(__name__ ~ ':list', key=view.key) }}"
           class="nav-link {% if view.is_active(request) %}active{% endif %}">
            {% if view.icon %}
                <i class="nav-icon {{ icon(view.icon) }}"></i>
            {% endif %}
            <p>{{ view.menu_label }}</p>
        </a>
    </li>
{% endmacro %}

{% macro dropdown_link(view) %}
    <li class="nav-item {% if view.is_active(request) %}menu-open{% endif %}">
        <a href="#" class="nav-link {% if view.is_active(request) %}active{% endif %}"
           data-lte-toggle="treeview" role="button">
            {% if view.icon %}
                <i class="nav-icon {{ icon(view.icon) }}"></i>
            {% endif %}
            <p>
                {{ view.menu_label }}
                <i class="nav-arrow bi bi-chevron-right"></i>
            </p>
        </a>
        <ul class="nav nav-treeview">
            {% for item in view.views if item.is_accessible(request) %}
                {# recursive: links, model views, sub-dropdowns #}
            {% endfor %}
        </ul>
    </li>
{% endmacro %}
```

The `data-lte-toggle="treeview"` attribute wires AdminLTE's JS to
expand/collapse the submenu. The `menu-open` class marks an expanded
ancestor when a child route is active. The `nav-arrow` icon rotates on
expand, driven by AdminLTE CSS.

## CSS compatibility layer

### Why a shim, not a rewrite

Core page templates use a small set of Tabler-specific utility classes
alongside standard Bootstrap classes. These Tabler classes are pure CSS
(no JS dependency), and they have straightforward Bootstrap/AdminLTE
equivalents. Rewriting every page template to replace `row-deck` with a
custom class would be far more invasive than providing the CSS rule.

The shim file (`static/css/tabler-compat.css`) loads after
AdminLTE's CSS and re-implements each Tabler class on top of Bootstrap
variables. It is not a full Tabler port: only the classes starlette-admin's
core templates actually use.

### Catalog of shimmed classes

Derived from `grep` across `starlette_admin/templates/`:

| Class | Used in | Shim implementation |
|-------|---------|---------------------|
| `row-deck` | list, detail, create, edit | `> * { --tblr-gutter-x: 0.75rem; margin-bottom: var(--tblr-gutter-x); }` flex/grid spacing |
| `row-cards` | list, detail, create, edit | Row with consistent card gutter; `.row.row-cards { --bs-gutter-x: .75rem; --bs-gutter-y: .75rem; }` |
| `card-table` | list | Removes card border when table is flush: `.card-table > .table { margin: 0; border-radius: inherit; }` |
| `table-vcenter` | list, detail | `.table-vcenter td { vertical-align: middle; }` |
| `table-mobile-md` | detail | Responsive breakpoint behavior; implemented with Bootstrap's responsive table utilities |
| `btn-list` | list, form footer, row actions | `.btn-list { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }` |
| `btn-ghost-primary` | row actions (kebab) | Maps to a Bootstrap ghost button: `color: var(--bs-primary); background: transparent;` |
| `btn-icon` | row actions | Square padding: `width/height: 2rem; display: inline-flex; align-items: center;` |
| `btn-animate-icon` | form footer | Transition on `.icon`: `transition: transform .2s;` |
| `btn-animate-icon-rotate` | form footer | `:hover .icon { transform: rotate(-90deg); }` |
| `container-tight` | login | `.container-tight { max-width: 30rem; margin: 0 auto; }` |
| `navbar-brand-autodark` | login | In dark mode, invert the logo: `[data-bs-theme="dark"] .navbar-brand-autodark img { filter: ...; }` |
| `navbar-brand-image` | login | `.navbar-brand-image { height: 2rem; }` |
| `input-group-flat` | login | Removes input-group border radius seam: `.input-group-flat > * { border-radius: 0; }` |
| `input-icon` | detail search | `.input-icon { position: relative; }` with `.input-icon-addon` absolutely positioned inside |
| `empty` | error page | Centered column layout: `.empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; text-align: center; }` |
| `empty-header` | error page | `.empty-header { font-size: 4rem; font-weight: 300; }` |
| `empty-title` | error page | `.empty-title { font-size: 1.5rem; font-weight: 300; }` |
| `empty-subtitle` | error page | `.empty-subtitle { color: var(--bs-secondary-color); }` |
| `empty-action` | error page | `.empty-action { margin-top: 1.5rem; }` |
| `checkbox-cell` | list row | `.checkbox-cell { cursor: pointer; width: 1%; }` |
| `subheader` | stat widget | `.subheader { font-size: .625rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--bs-secondary-color); }` |
| `card-link` | stat widget | `.card-link:hover { text-decoration: none; }` |
| `icon`, `icon-1`, `icon-2` | various | Sizing: `.icon { width: 1em; height: 1em; } .icon-1 { width: 1.5rem; } .icon-2 { width: 2rem; }` |

Total: ~25 classes. Each is 1-5 lines of CSS. The entire shim file is
estimated at ~150 lines.

### `adminlte-theme.css` (theme-specific overrides)

On top of the shim, a small `adminlte-theme.css` file adjusts how
starlette-admin's page bodies look inside the AdminLTE shell:

- Card headers: AdminLTE uses slightly different padding than Tabler; add
  `.card-header { display: flex; align-items: center; justify-content: space-between; }`
  so the list toolbar's title + actions row aligns.
- Form labels: Tabler bolds labels; AdminLTE does not. Match the Tabler
  look for consistency with field templates.
- Select2 dropdown: ensure the dropdown renders above the AdminLTE sidebar
  z-index.
- Flash alerts: AdminLTE alert styling is close to Bootstrap; ensure the
  `.alert-icon` wrapper aligns.

## Icon mapping: Bootstrap Icons

AdminLTE 4 ships with [Bootstrap Icons](https://icons.getbootstrap.com/)
(`bi bi-*`). The theme's `IconSet` maps every semantic name in core's
vocabulary to the corresponding Bootstrap Icon:

```python
class AdminlteIcons(IconSet):
    library = "bootstrap-icons"
    icons = {
        "list.new": "bi bi-plus-lg",
        "list.search": "bi bi-search",
        "list.filter": "bi bi-funnel",
        "list.columns": "bi bi-table",
        "list.import": "bi bi-upload",
        "list.export": "bi bi-download",
        "list.row_actions": "bi bi-three-dots-vertical",
        "default_actions.view": "bi bi-eye",
        "default_actions.edit": "bi bi-pencil",
        "default_actions.delete": "bi bi-trash",
        "pagination.prev": "bi bi-chevron-left",
        "pagination.next": "bi bi-chevron-right",
        "sort.none": "bi bi-arrow-down-up",
        "sort.asc": "bi bi-sort-up",
        "sort.desc": "bi bi-sort-down",
        "auth.logout": "bi bi-box-arrow-right",
        "nav.language": "bi bi-translate",
        "nav.world": "bi bi-globe",
        "nav.user": "bi bi-person",
        "flash.success": "bi bi-check-circle",
        "flash.warning": "bi bi-exclamation-triangle",
        "flash.error": "bi bi-exclamation-circle",
        "flash.info": "bi bi-info-circle",
        "action.close": "bi bi-x-lg",
        "action.copy": "bi bi-clipboard",
        "field.file": "bi bi-file-earmark",
        "field.boolean_true": "bi bi-check-circle-fill",
        "field.boolean_false": "bi bi-x-circle",
        "list_field.add": "bi bi-plus",
        "inline.add_row": "bi bi-plus",
        "inline.delete_row": "bi bi-trash",
        "panel.collapse_toggle": "bi bi-chevron-down",
        "filter.remove_chip": "bi bi-x-lg",
        "filter_builder.add_condition": "bi bi-plus",
        "filter_builder.add_group": "bi bi-layers",
        "filter_builder.remove": "bi bi-trash",
        "import.preview": "bi bi-eye",
    }

    def css_links(self, request):
        return [static_url(request, "plugins/adminlte/vendor/bootstrap-icons/bootstrap-icons.min.css", v=V)]
```

The full vocabulary is enumerated in `CoreIcons.icons`
(`starlette_admin/theme.py:43`). Every key must be mapped; unmapped keys
fall through to the raw key string (broken class). The current scaffolded
theme maps to Tabler Icons; this design replaces that with Bootstrap Icons.

## Theme options

```python
@dataclass(frozen=True)
class AdminlteConfig:
    """Options for AdminlteTheme(**options)."""
    skin: Literal["light", "dark"] | None = None
    sidebar_fixed: bool = True
    header_fixed: bool = False
    sidebar_collapsed: bool = False
    brand_image: str | None = None
    brand_text: str | None = None
```

| Option | Default | Effect |
|--------|---------|--------|
| `skin` | `None` | Color scheme. `None` follows `TablerSettings.mode`; `"light"` or `"dark"` overrides it. Sets `data-bs-theme` on `<html>` and the AdminLTE theme-init script. |
| `sidebar_fixed` | `True` | Adds `layout-fixed` to `<body>`. Makes the sidebar scroll independently (with OverlayScrollbars). |
| `header_fixed` | `False` | Adds `layout-navbar-fixed` to `<body>`. Pins the header to the top on scroll. |
| `sidebar_collapsed` | `False` | Adds `sidebar-collapse` to `<body>`. Renders the sidebar in mini mode on load. |
| `brand_image` | `None` | URL for the sidebar brand logo image. Overrides `Admin(logo_url=...)` when set. |
| `brand_text` | `None` | Text next to the brand image. Defaults to `app_title`. |

Options reach templates via the `theme_config` global (exposed by
`template_globals()`). The body-attributes block reads them:

```jinja
{% block body_attributes %}
    class="{{ theme_config.sidebar_fixed and 'layout-fixed' or '' }}
           sidebar-expand-lg bg-body-tertiary
           {{ theme_config.header_fixed and 'layout-navbar-fixed' or '' }}
           {{ theme_config.sidebar_collapsed and 'sidebar-collapse' or '' }}"
{% endblock %}
```

### Palette integration

The theme receives `TablerSettings` through `Admin(theme=...)`. The `skin`
option defaults to `TablerSettings.mode`, so a user who sets
`TablerSettings(mode="dark")` gets the dark skin without duplicating the
setting. The `data-bs-theme` attribute (produced by
`theme_settings.html_attrs()`) is what AdminLTE's CSS and theme-init script
read, so the palette token flows through with no theme-specific code.

`TablerSettings.base`, `.primary`, and `.radius` are Tabler-specific CSS
variable tokens that AdminLTE does not consume. They are ignored: AdminLTE
has its own accent system (Bootstrap's `$primary` SCSS variable). A future
enhancement could map `.primary` to Bootstrap's `--bs-primary` override,
but that is out of scope for the initial implementation.

## JavaScript considerations

### Script loading order

```
base.html core_js block (theme-overridden):
  1. jquery.min.js              (kept from core)
  2. js.cookie.min.js           (kept from core)
  3. bootstrap.bundle.min.js    (replaces tabler.min.js; includes Popper)
  4. adminlte.min.js            (AdminLTE 4 widgets)

base.html inline script (inherited from core):
  5. window.StarletteAdmin icon registry
  6. $.ajaxSetup CSRF
  7. language/timezone switchers

Page script block (inherited from core page templates):
  8. utils.js, alerts.js, actions.js, list.js/form.js/detail.js, ...
```

Core's JavaScript (`list.js`, `form.js`, `actions.js`, etc.) depends on:
- jQuery (`$`) - loaded in step 1.
- Bootstrap data API (`data-bs-toggle`, `data-bs-dismiss`) - available from
  step 3.
- Bootstrap JS API (`new bootstrap.Popover(...)`, `new bootstrap.Modal(...)`)
  - the `bootstrap` global is provided by `bootstrap.bundle.min.js` (step 3),
  same as Tabler's bundle provided it.
- `window.StarletteAdmin.getIcon()` - from step 5 (inherited, unchanged).

No core JS file needs modification. The script-loading order is preserved.

### AdminLTE JS widgets

AdminLTE's JS provides:
- `data-lte-toggle="sidebar"`: mobile sidebar push animation.
- `data-lte-toggle="treeview"`: collapsible sidebar menu items.
- `data-lte-toggle="card-collapse"`: card collapse/expand (used by inline
  formsets if they expose collapse buttons).
- `data-lte-toggle="fullscreen"`: fullscreen toggle (optional, available in
  the `navbar_start` block for users who want it).

These are additive: they handle AdminLTE-specific interactions that
Bootstrap's JS does not cover. They do not conflict with Bootstrap's own
widgets (dropdowns, modals, popovers, tooltips).

### OverlayScrollbars

AdminLTE 4 uses [OverlayScrollbars](https://kingsora.github.io/OverlayScrollbars/)
for the sidebar's scrollbar. It is an optional enhancement: without it, the
sidebar uses the native scrollbar. The CSS is loaded in `core_css`; the JS
initialization is part of `adminlte.min.js`. Bundled under
`static/plugins/adminlte/vendor/overlayscrollbars/`.

## Static assets and vendoring

All vendored frameworks ship bundled under
`static/plugins/adminlte/vendor/` for air-gapped installs (CDN option
documented but not default):

```
static/plugins/adminlte/
├── vendor/
│   ├── bootstrap/
│   │   ├── bootstrap.min.css
│   │   └── bootstrap.bundle.min.js
│   ├── adminlte/
│   │   ├── adminlte.min.css
│   │   └── adminlte.min.js
│   ├── bootstrap-icons/
│   │   ├── bootstrap-icons.min.css
│   │   └── fonts/                      (bootstrap-icons woff/woff2)
│   ├── overlayscrollbars/
│   │   ├── overlayscrollbars.min.css
│   │   └── overlayscrollbars.browser.es6.min.js
│   └── fontsource/
│       └── source-sans-3.css           (and font files)
├── css/
│   ├── tabler-compat.css               (CSS shim for Tabler utility classes)
│   └── adminlte-theme.css              (theme-specific overrides)
└── js/
    └── (none expected; AdminLTE JS is vendor-bundled)
```

Assets are addressed through `static_url(request, "plugins/adminlte/...")`,
served by the shared `/static` mount. The theme's `static/` folder is
wired into the packages list by `_register_theme` in `base.py`.

## Package layout

```
starlette-admin-adminlte/
├── pyproject.toml
├── README.md
├── DESIGN.md                           (this file)
├── babel.cfg
├── Makefile
├── src/starlette_admin_adminlte/
│   ├── __init__.py                     (exports AdminlteTheme, AdminlteConfig, __version__)
│   ├── theme.py                        (BaseTheme subclass + AdminlteConfig dataclass)
│   ├── icons.py                        (AdminlteIcons: semantic names -> bi classes)
│   ├── templates/
│   │   ├── base.html                   (extends @core/base.html, swaps assets)
│   │   ├── layout.html                 (AdminLTE 4 shell, full rewrite)
│   │   └── plugins/adminlte/
│   │       └── macros/
│   │           └── views.html          (sidebar-menu macros)
│   ├── static/plugins/adminlte/
│   │   ├── vendor/...                  (bundled CSS/JS/fonts)
│   │   ├── css/
│   │   │   ├── tabler-compat.css
│   │   │   └── adminlte-theme.css
│   └── translations/                   (Babel catalogs for theme strings)
├── tests/
│   ├── conftest.py
│   ├── test_shell_renders.py           (every core page renders under the theme)
│   └── test_icon_mapping.py            (full vocabulary mapped)
├── example/
│   └── app.py                          (demo with auth, multiple model views, dropdowns)
└── docs/
    └── index.md
```

## Implementation plan

### Phase 1: Core changes (starlette-admin)

Small additive PRs against `starlette-admin` core. Each is independently
shippable.

1. Add `{% block body_attributes %}{% endblock %}` to `<body>` in
   `base.html`.
2. Wrap the two inline `<style>` blocks in `{% block core_inline_css %}`
   in `base.html`.
3. Fix the hardcoded `ti ti-alert-circle` in `login.html` to
   `{{ icon('flash.error') }}`.

### Phase 2: Asset swap and icon mapping

4. Replace `icons.py` contents: swap the Tabler Icons mapping for Bootstrap
   Icons. Verify every `CoreIcons.icons` key is mapped.
5. Write `base.html` override: extend `@core/base.html`, swap `core_css`,
   `icon_css`, `fonts`, `core_inline_css`, `core_js`, add `body_attributes`
   and `head` (FOUC script).
6. Vendor Bootstrap 5, AdminLTE 4, Bootstrap Icons, OverlayScrollbars, and
   Source Sans 3 under `static/plugins/adminlte/vendor/`.
7. Write `tabler-compat.css` with all ~25 shimmed classes.
8. Write `adminlte-theme.css` with shell-specific overrides.
9. Verify: the admin renders with AdminLTE assets but Tabler layout. The
   shell is still Tabler's (sidebar, navbar), but the CSS framework is
   AdminLTE's. This isolates asset-swap bugs from layout bugs.

### Phase 3: Shell rewrite

10. Write `layout.html`: full AdminLTE 4 shell with all block names from
    the contract table above.
11. Write `plugins/adminlte/macros/views.html`: sidebar-menu macros for
    `view_link`, `custom_link`, `extern_link`, `dropdown_link` (recursive
    for nested `DropDown`).
12. Update `theme.py`: add `AdminlteConfig` fields (`skin`,
    `sidebar_fixed`, `header_fixed`, `sidebar_collapsed`, `brand_image`,
    `brand_text`), wire them through `template_globals()`.
13. Verify: every core page (list, detail, create, edit, index, login,
    error) renders correctly under the AdminLTE shell.

### Phase 4: Polish and test

14. Write `test_shell_renders.py`: parametrized test that GETs every core
    page route and asserts HTTP 200 plus key AdminLTE class presence
    (`app-wrapper`, `app-sidebar`, `app-main`, `app-content`).
15. Write `test_icon_mapping.py`: assert every key in `CoreIcons.icons` is
    present in `AdminlteIcons.icons` and resolves to a `bi bi-*` class.
16. Manual visual QA against the example app with auth, dropdown menus,
    search, filters, inline forms, widgets, login, error pages, dark mode.
17. Update `README.md`, `docs/index.md`, `example/app.py`.

## Testing plan

### Automated

| Test | What it verifies |
|------|-----------------|
| `test_theme_is_active` | `admin.theme is AdminlteTheme()` instance |
| `test_icon_set_is_bootstrap_icons` | `icon_set.library == "bootstrap-icons"` |
| `test_full_vocabulary_mapped` | every `CoreIcons.icons` key is in `AdminlteIcons.icons` |
| `test_icon_classes_are_bi` | every value in `AdminlteIcons.icons` starts with `"bi "` |
| `test_list_page_renders` | GET `/admin/<model>/list` returns 200 |
| `test_detail_page_renders` | GET `/admin/<model>/<pk>/detail` returns 200 |
| `test_create_page_renders` | GET `/admin/<model>/create` returns 200 |
| `test_edit_page_renders` | GET `/admin/<model>/<pk>/edit` returns 200 |
| `test_index_page_renders` | GET `/admin/` returns 200 |
| `test_login_page_renders` | GET `/admin/login` returns 200 |
| `test_error_page_renders` | GET `/admin/nonexistent` returns 404 with AdminLTE shell |
| `test_adminlte_classes_present` | response contains `app-wrapper`, `app-sidebar`, `app-main` |
| `test_tabler_classes_absent` | response does not contain `navbar-vertical`, `page-wrapper` |
| `test_bootstrap_icons_linked` | response contains `bootstrap-icons` CSS link |
| `test_adminlte_css_linked` | response contains `adminlte.min.css` |
| `test_tabler_css_absent` | response does not contain `tabler.min.css` |
| `test_compatibility_css_linked` | response contains `tabler-compat.css` |
| `test_dark_mode` | with `skin="dark"`, `data-bs-theme="dark"` on `<html>` |
| `test_body_classes` | `<body>` has `layout-fixed sidebar-expand-lg` |
| `test_sidebar_menu_renders` | response contains `sidebar-menu` and `nav-treeview` for dropdown views |
| `test_crud_works` | create, edit, delete through the admin UI succeeds |

### Manual visual QA checklist

- [ ] Sidebar renders with correct brand, menu items, icons, active states
- [ ] Dropdown menus expand/collapse via treeview toggle
- [ ] Sidebar toggle works on mobile (push overlay)
- [ ] Top navbar shows language/timezone switchers and user menu
- [ ] List page: search, filter builder, column visibility, pagination, row
      actions all functional
- [ ] List page: inline edit popover works (if enabled)
- [ ] Detail page: attribute/value table, row actions, detail search
- [ ] Create/Edit: form fields render correctly (select2, flatpickr, etc.)
- [ ] Create/Edit: inline formsets add/remove rows
- [ ] Dashboard: widgets render with correct card styling
- [ ] Login page: centered card, error alert, password toggle
- [ ] Error page: 404/403 render with AdminLTE empty state
- [ ] Dark mode: all pages render correctly with dark skin
- [ ] Flash messages: alert icons and dismiss work
- [ ] Select2 dropdowns: render above sidebar z-index, correct styling
- [ ] Modals: delete/action/import modals render and function

## Resolved decisions

- **Extend `@core/base.html`, do not rewrite it.** The `<head>` structure,
  favicon, title, plugin CSS/JS loops, the `window.StarletteAdmin` icon
  registry, CSRF setup, and language/timezone switcher jQuery code are all
  framework-agnostic. Overriding 5 named blocks is cleaner than duplicating
  250 lines.

- **Rewrite `layout.html` entirely.** The DOM structure
  (`.app-wrapper` / `.app-sidebar` / `.app-header` / `.app-main`) is
  fundamentally different from Tabler's (`.page` / `.navbar-vertical` /
  `.page-wrapper`). No block override can reconcile CSS-grid-based layout
  differences. The rewrite preserves every block name so page templates
  inherit transparently.

- **CSS shim over template rewrite for page bodies.** Both frameworks are
  Bootstrap 5. The page bodies use Bootstrap classes (`card`, `btn`,
  `table`, `form-control`) plus ~25 Tabler utility classes. A ~150-line CSS
  file reimplements those utilities on Bootstrap variables, far cheaper
  than rewriting 8 page templates and maintaining them in sync with core.

- **Bootstrap Icons, not FontAwesome or Tabler Icons.** AdminLTE 4 ships
  with Bootstrap Icons; matching the framework's native icon library is the
  expected choice. The `IconSet` maps every semantic name; unmapped names
  fall through to the raw key.

- **Add `body_attributes` and `core_inline_css` blocks to core.** Both are
  additive (empty default, zero behavioral change for Tabler). Without
  `body_attributes`, the theme cannot set AdminLTE's required body classes
  without rewriting base.html entirely. Without `core_inline_css`, the
  theme inherits select2 CSS that references non-existent `--tblr-*`
  variables.

- **Vendor all frameworks bundled.** Admin panels frequently run air-gapped.
  Bootstrap 5, AdminLTE 4, Bootstrap Icons, OverlayScrollbars, and Source
  Sans 3 all ship under `static/<js|css>/vendor/`.

- **No `list.html` / `detail.html` / `create.html` / `edit.html` override.**
  This is the proof that the block contract works: every CRUD page body is
  inherited from core, styled by the CSS shim, and rendered inside the
  AdminLTE shell. If a future page body introduces an unshimmed Tabler
  class, the fix is a CSS rule, not a template fork.
