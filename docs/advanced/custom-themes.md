# Custom Themes

You can customize the appearance of your admin interface using Bootstrap theme attributes, custom templates, and static files. The `ThemeSettings` class controls the default styling by applying specific data attributes to the `<html>` tag. For more advanced customizations, the `Admin` application also accepts custom template and static directories.

## Applying a Theme

Use the `ThemeSettings` class to define your color palette, border radius, and color mode. Pass this configuration to the `theme` parameter of your `Admin` instance.

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin import ThemeSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=ThemeSettings(base="slate", primary="blue", radius=2, mode="dark"),
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

## `ThemeSettings` Reference

| Attribute | Type | Default | Valid Values |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Custom Templates Directory

To override the default HTML, provide a path to the `templates_dir` parameter.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")

```

Any file placed inside your custom directory will shadow the built-in template at the exact same relative path. The rest of the built-in template tree remains intact. For a complete list of overridable templates and a detailed override guide, refer to the [Templates](templates.md) documentation.

## Custom Static Directory

To include custom CSS, JavaScript, or images, provide a path to the `static_dir` parameter.

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