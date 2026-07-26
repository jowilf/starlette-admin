# Custom Themes

You can customize the appearance of your admin interface using the theme abstractions, custom templates, and static files. The `DefaultTheme` class controls the default styling by applying specific data attributes to the `<html>` tag through `TablerSettings`. For more advanced customizations, you can subclass `BaseTheme` to bundle your own templates, static assets, and icon sets, or simply pass custom template and static directories to the `Admin` application.

## Applying a Theme

Use the `TablerSettings` class to define your color palette, border radius, and color mode. Pass this configuration to the `DefaultTheme`, which is then passed to the `theme` parameter of your `Admin` instance.

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

## `TablerSettings` Reference

| Attribute | Type | Default | Valid Values |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Restyling Components with a Class Map

Core templates avoid hardcoding component styling. Instead, they render class attributes using the `cls('role.name')` Jinja helper. This helper resolves a semantic role, such as `form.save_button` or `list.table`, to a CSS class string. The default values for every role reside in `starlette_admin.theme.CoreClasses`.

To restyle specific roles, create a `ClassMap` subclass. Any unmapped role automatically falls back to `CoreClasses`, making partial overrides completely safe. Note that a button role controls the element's entire class attribute, including its variant, size, and spacing. Mapping a button role completely replaces its visual appearance.

You do not need to build a full custom theme to utilize class maps. To adjust the default theme, subclass `DefaultTheme` and return your map from the `get_class_map()` method:

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

Review `CoreClasses.classes` in `starlette_admin/theme.py` to see the full vocabulary of roles. Roles manage three distinct types of styling:

* **Buttons:** Assigns one role per button location, including form footers, list toolbars, filter bars, action modals, and inline editing. The assigned value becomes the button's entire class attribute.
* **Component classes:** Defines framework-specific classes that a custom CSS framework must swap out, such as `list.table`, `modal.base`, or `filter.chip`.
* **Runtime classes:** Specifies classes that core JavaScript applies dynamically, such as `alert.success` or `import.status_badge`.

## Building and Sharing Custom Themes

With `starlette-admin`, you can author, package, and share complete theme packages on PyPI, much like plugins. Subclassing `BaseTheme` lets you create a reusable Python package that replaces the admin layout and UI styling across multiple projects or distributes a custom visual system to the broader community.

### Scaffolding with Cookiecutter

Use the official cookiecutter template to start authoring a theme. It generates a complete, publishable package with the correct directory structure and configuration files.

Install `cookiecutter` via your preferred package manager. Refer to the [official installation guide](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) for specific details:

```bash
pip install cookiecutter

```

Next, run the template from any directory:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

The template prompts you for variables like the theme name, package slug, and version. Once finished, it provides a self-contained package featuring:

* A `src/` directory containing the theme class, icon set, and class map.
* Preconfigured `templates/`, `static/`, and translation folders.
* A test suite and a runnable example application.

### `BaseTheme` Architecture

A theme serves as the root of the rendering engine. Each `Admin` instance supports exactly one active theme. A `BaseTheme` subclass configures the following components:

* **Templates:** Ships replacement templates inside the package's `templates/` folder using bare relative paths like `base.html`, `layout.html`, or `list.html`. The active theme sits above plugins in Jinja's loader chain, which allows it to restyle both core and plugin template structures.
* **Static Assets:** Distributes stylesheets, scripts, and images within the package's `static/` directory.
* **Icon Set:** Replaces the admin icon library by returning a custom `IconSet` subclass from `get_icon_set()`. This maps semantic keys like `list.new` or `auth.logout` to concrete CSS classes.
* **Class Map:** Restyles component roles by returning a `ClassMap` subclass from `get_class_map()`, as detailed in the [Restyling Components with a Class Map](%23restyling-components-with-a-class-map) section.
* **Template Globals:** Exposes global variables to Jinja templates by overriding the `template_globals()` method.

### Example Theme Package

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

### Template Loader Hierarchy

The template engine resolves files in the following order:

1. User `templates_dir` (always overrides all templates).
2. Active Theme `templates/` (restyles core and plugin templates).
3. Namespaced Plugin `templates/`.
4. Core `starlette_admin` default templates.

You can safely extend themes from user overrides or theme subclasses using the `@theme` Jinja prefix mapping, for example, `{% extends "@theme/layout.html" %}`.

## Custom Templates Directory

To override the default HTML without building a full custom theme, provide a directory path to the `templates_dir` parameter.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Any file placed inside your custom directory shadows the built-in template at the exact same relative path. The rest of the built-in template tree remains unaffected. For a complete list of overridable templates and a detailed guide, refer to the [Templates](templates.md) documentation.

## Custom Static Directory

To include custom CSS, JavaScript, or images without creating a full theme, provide a directory path to the `static_dir` parameter.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Files placed in this directory are served alongside the built-in assets at the `/admin/static/` endpoint. For example, a file located at `my_static/custom.css` becomes accessible at `/admin/static/custom.css`.

You can reference this custom stylesheet from your templates using the following snippet:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## What's Next

* **[Templates](templates.md):** Override a single page, cell, or widget without forking the entire template tree.
* **[Extension Points](extension-points.md):** Explore hooks and customization points beyond basic themes.
* **[Quickstart](../getting-started/quickstart.md):** Build a working admin interface from scratch.
