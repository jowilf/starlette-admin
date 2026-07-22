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

## Building and Sharing Custom Themes

`starlette-admin` allows you to author, package, and share complete theme packages on PyPI, similar to how plugins work. By subclassing `BaseTheme`, you can create a reusable Python package that replaces the admin layout and UI styling across multiple projects or distributes a custom visual system to the community.

### `BaseTheme` Architecture

A theme acts as the root of the rendering engine. Exactly one theme is active per `Admin` instance. A `BaseTheme` subclass configures:

* **Templates**: Ships replacement templates inside its package `templates/` folder at bare relative paths (such as `base.html`, `layout.html`, or `list.html`). The active theme sits above plugins in Jinja's loader chain, allowing it to restyle both core and plugin template structures.
* **Static Assets**: Ships stylesheets, scripts, and images under its package `static/` directory.
* **Icon Set**: Replaces the admin icon library by returning a custom `IconSet` subclass from `get_icon_set()`. Maps semantic keys (such as `list.new` or `auth.logout`) to concrete library CSS classes.
* **Template Globals**: Exposes global variables to Jinja templates by overriding `template_globals()`.

### Example Theme Package

```python
from typing import Any
from starlette_admin.theme import BaseTheme, IconSet

class CustomIconSet(IconSet):
    library = "heroicons"
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }

class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### Template Loader Hierarchy

Template resolution resolves in the following order:

1. User `templates_dir` (always overrides all templates).
2. Active Theme `templates/` (re-styles core and plugin templates).
3. Namespaced Plugin `templates/`.
4. Core `starlette_admin` default templates.

Themes can also be safely extended from user overrides or theme subclasses using the `@theme` Jinja prefix mapping (for example `{% extends "@theme/layout.html" %}`).

## Custom Templates Directory

To override the default HTML without building a full theme, provide a path to the `templates_dir` parameter.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Any file placed inside your custom directory will shadow the built-in template at the exact same relative path. The rest of the built-in template tree remains intact. For a complete list of overridable templates and a detailed override guide, refer to the [Templates](templates.md) documentation.

## Custom Static Directory

To include custom CSS, JavaScript, or images without a full theme, provide a path to the `static_dir` parameter.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Files placed in this directory are served alongside the built-in assets at the `/admin/static/` endpoint. For example, a file located at `my_static/custom.css` is accessible at `/admin/static/custom.css`.

You can reference this custom stylesheet from your templates using the following snippet:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">
```

---

## What's Next

* **[Templates](templates.md):** Override a single page, cell, or widget without forking the entire template tree.
* **[Extension Points](extension-points.md):** Explore hooks and customization points beyond basic themes.
* **[Quickstart](../getting-started/quickstart.md):** Build a working admin from scratch.