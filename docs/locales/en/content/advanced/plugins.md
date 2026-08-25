---
title: Plugins
description: Package reusable admin features and extensions as drop-in plugins for starlette-admin.
---

# Plugins

A plugin is a Python package that extends `starlette-admin` through a single constructor argument. A plugin can bundle any combination of fields, templates, static assets, model converters, filters, import/export formats, storage backends, event subscribers, views, routes, middlewares, theme assets, and translation catalogs.

## Using a plugin

Pass plugins through the `plugins` argument when you construct your `Admin` instance:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

The plugin constructor takes the options, and the list goes straight to `Admin`. Nothing else to set up or register. Options flow from the constructor down to the Python backend, the Jinja templates, and the frontend JavaScript.

## Building a plugin

To write a plugin, start from the official cookiecutter template. It generates a publishable package with the right directory structure and configuration.

### Prerequisites

Install `cookiecutter` with your package manager. See the [official installation guide](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) for the details:

```bash
pip install cookiecutter
```

### Scaffolding

Run the cookiecutter template from any location:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

The template prompts you for the plugin name, package slug, version, and a few other variables. When it finishes, you have a self-contained package with:

* A `src/` directory holding your plugin class and fields.
* Correctly namespaced `templates/`, `static/`, and `translations/` folders.
* A complete test suite.
* A runnable example application.

## The plugin API

At the core of every plugin is a subclass of `BasePlugin` (`starlette_admin.plugins.BasePlugin`), which gives you hooks to register your features while `Admin` initializes.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

The `name` attribute is a unique kebab-case identifier that doubles as the namespace for your templates and static assets. Every template and static file your plugin ships has to live under `plugins/<name>/`.

### Asset folders

A plugin can carry exactly three folders at the root of its package. There's nothing to register, because the admin finds them by convention:

* `templates/`: Jinja templates, which have to sit under `templates/plugins/<name>/`.
* `static/`: Static assets such as CSS and JS files, which have to sit under `static/plugins/<name>/`.
* `translations/`: Babel translation catalogs.

Staying inside the `plugins/<name>/` namespace keeps your assets from colliding with core files or other plugins, while leaving them overridable through the user's own `templates_dir` or `static_dir`.

### Declarative hooks

Override the declarative hooks to inject assets, register views, or mount routes.

* `css_links(self, request: Request) -> Sequence[str]`: Adds stylesheets to every admin page layout.
* `js_links(self, request: Request) -> Sequence[str]`: Adds scripts to every admin page layout.
* `views(self) -> Sequence[BaseView]`: Returns the views to register in the admin sidebar. Return a `DropDown` to group them.
* `routes(self) -> Sequence[Route | Mount]`: Returns headless endpoints mounted under `/plugins/<name>/`, which is handy for webhooks and proxy endpoints.
* `middlewares(self) -> Sequence[Middleware]`: Adds Starlette middlewares.
* `template_globals(self) -> dict[str, Any]`: Exposes Jinja globals, prefixed with `<name>_` so they can't collide.
* `template_filters(self) -> dict[str, Callable]`: Exposes Jinja filters, prefixed with `<name>_` the same way.

### The setup hook

`setup(self, admin: BaseAdmin) -> None` integrates your plugin with the core registries. Use it to register model converters, filters, import and export formats, storage backends, and event subscribers. It runs after the declarative hooks are applied.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### The lifecycle hook

`on_mount(self, admin: BaseAdmin) -> None` runs exactly once, after the Starlette sub-application is built and mounted. The built application is available as `admin.app`.

## Templates and overrides

Plugin templates join the loader chain automatically. A user overrides one by putting a file at the matching path inside their own `templates_dir`, which always takes priority. To override `plugins/geospatial/fields/form/point.html`, for example, they create `templates_dir/plugins/geospatial/fields/form/point.html`.

So that a user override can extend the original safely, every plugin gets a `@<name>` prefix mapping that works like the `@core` prefix. The override starts with `{% extends "@geospatial/fields/form/point.html" %}` and extends the base plugin template without including itself recursively.

## Frontend JavaScript integration

A plugin that ships custom fields should package its frontend scripts according to the field initializer contract. That keeps them working across both full page loads and dynamically inserted fragments.

* **Target locally:** Query inside the `container` element you're given, never the global `document`.
* **Be idempotent:** Core runs the initializer on DOM ready and again whenever it inserts inline rows or fragments.
* **Use data attributes:** Read configuration from the `data-*` attributes rendered on the field element.

```javascript title="plugins/<name>/js/slider.js"
(function () {
  function initSlider(container) {
    var input = container.querySelector('input[type="range"]');
    var output = container.querySelector(".sa-slider-output");
    var suffix = container.dataset.suffix || "";

    input.addEventListener("input", function () {
      output.textContent = input.value + suffix;
    });
  }

  // Register the initializer so core runs it on the right lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## Extension points via the setup hook

Plugins use the existing public registries rather than a separate extension path of their own.

* **Converters**: Call `register_converter`, from the contrib backend you're targeting, to map ORM column types to your field classes. Define the field itself as an ordinary `StringField` subclass, storing and displaying geometries as WKT text:

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField):
    ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **Filters**: Call `register_filters` to attach filter classes to a field type.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Storage**: Call `register_storage` to expose a new backend, such as Azure or GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importers and Exporters**: Use `register_import_format` and `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

A plugin can support several ORM backends, so import them conditionally inside `setup()`. That way the plugin still loads when the user installed only one of them:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## What's next

* **[Custom Themes](custom-themes.md):** Package and share a full visual system, using the same cookiecutter workflow.
* **[Events](events.md):** The subscriber API a plugin registers from its `setup()` hook.
* **[Extension Points](extension-points.md):** Every registry and base class a plugin can hook into.
