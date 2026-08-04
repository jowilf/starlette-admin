---
title: Custom Themes
description: Override Tabler CSS variables, inject custom stylesheets, and modify the overall aesthetic of your starlette-admin dashboard.
---

# Custom Themes

You can restyle the admin through theme settings, custom templates, and static files. `DefaultTheme` controls the default look by writing data attributes onto the `<html>` tag from a `TablerSettings` object. For deeper changes, subclass `BaseTheme` to bundle your own templates, static assets, and icon sets, or pass your own template and static directories to `Admin`.

## Applying a theme

Use `TablerSettings` to set your color palette, border radius, and color mode. Pass it to `DefaultTheme`, then pass that to the `theme` parameter of your `Admin` instance.

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

See [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) for a runnable app that picks a random theme on every startup.

This configuration applies `data-bs-theme*` attributes directly to the root `<html>` element:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## `TablerSettings` reference

| Attribute | Type | Default | Valid values |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Restyling components with a class map

Core templates don't hardcode component styling. They render class attributes through the `cls('role.name')` Jinja helper, which resolves a semantic role such as `form.save_button` or `list.table` to a CSS class string. The default value for every role lives in `starlette_admin.theme.CoreClasses`.

To restyle a role, write a `ClassMap` subclass. Any role you don't map falls back to `CoreClasses`, so partial overrides are safe. Keep in mind that a button role sets the element's entire class attribute, including variant, size, and spacing, so mapping one replaces the button's appearance outright.

Class maps don't require a full custom theme. To adjust the default theme, subclass `DefaultTheme` and return your map from `get_class_map()`:

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

Read `CoreClasses.classes` in `starlette_admin/theme.py` for the full vocabulary of roles. Roles cover three kinds of styling:

* **Buttons:** One role per button location, covering form footers, list toolbars, filter bars, action modals, and inline editing. The value you set becomes the button's entire class attribute.
* **Component classes:** Framework-specific classes a different CSS framework has to swap out, such as `list.table`, `modal.base`, or `filter.chip`.
* **Runtime classes:** Classes the core JavaScript applies dynamically, such as `alert.success` or `import.status_badge`.

## Building and sharing custom themes

You can package a theme and publish it on PyPI, much like a plugin. Subclass `BaseTheme` to build a reusable Python package that replaces the admin layout and styling across several projects, or to share a visual system with other people.

### Scaffolding with Cookiecutter

Start from the official cookiecutter template. It generates a publishable package with the right directory structure and configuration files.

Install `cookiecutter` with your package manager. See the [official installation guide](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) for the details:

```bash
pip install cookiecutter

```

Then run the template from any directory:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

The template prompts you for the theme name, package slug, version, and a few other variables. When it finishes, you have a self-contained package with:

* A `src/` directory holding the theme class, icon set, and class map.
* Preconfigured `templates/`, `static/`, and translation folders.
* A test suite and a runnable example application.

### `BaseTheme` architecture

A theme sits at the root of the rendering chain, and each `Admin` instance has exactly one active theme. A `BaseTheme` subclass configures these pieces:

* **Templates:** Replacement templates in the package's `templates/` folder, using bare relative paths such as `base.html`, `layout.html`, or `list.html`. The active theme sits above plugins in Jinja's loader chain, so it can restyle both core and plugin templates.
* **Static assets:** Stylesheets, scripts, and images in the package's `static/` directory.
* **Icon set:** A custom `IconSet` subclass returned from `get_icon_set()`, mapping semantic keys such as `list.new` or `auth.logout` to CSS classes.
* **Class map:** A `ClassMap` subclass returned from `get_class_map()`, as described in [Restyling components with a class map](#restyling-components-with-a-class-map).
* **Template globals:** Global variables exposed to Jinja by overriding `template_globals()`.

### Example theme package

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### Template loader hierarchy

The template engine resolves files in this order:

1. Your `templates_dir`, which overrides everything below it.
2. The active theme's `templates/`, which restyles core and plugin templates.
3. The namespaced plugin `templates/`.
4. The core `starlette_admin` default templates.

To extend a theme template from a user override or a theme subclass, use the `@theme` Jinja prefix, for example `{% extends "@theme/layout.html" %}`.

## Custom templates directory

To override the default HTML without building a full theme, pass a directory path to `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Any file you put in that directory shadows the built-in template at the same relative path, and the rest of the built-in tree keeps rendering as before. For the full list of overridable templates, see [Templates](templates.md).

## Custom static directory

To add your own CSS, JavaScript, or images without building a full theme, pass a directory path to `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Files in this directory are served alongside the built-in assets under `/admin/static/`. A file at `my_static/custom.css`, for example, becomes available at `/admin/static/custom.css`.

Reference the stylesheet from your templates like this:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## What's next

* **[Templates](templates.md):** Override a single page, cell, or widget without forking the entire template tree.
* **[Extension Points](extension-points.md):** Explore hooks and customization points beyond basic themes.
* **[Quickstart](../getting-started/quickstart.md):** Build a working admin interface from scratch.
