# Plugins

A plugin is a Python package that extends `starlette-admin` through a single constructor argument. A plugin can bundle any combination of fields, templates, static assets, model converters, filters, import/export formats, storage backends, event subscribers, views, routes, middlewares, theme assets, and translation catalogs.

## Using a Plugin

Plugins are supplied through the `plugins` argument when initializing your `Admin` instance:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

The plugin constructor handles any options, and the plugin list is passed directly to `Admin`. No additional setup or registration is required. Options flow directly from the plugin constructor down to the Python backend, Jinja templates, and frontend Javascript.

## Building a Plugin

To author a plugin, use the official cookiecutter template. This template generates a complete, publishable package with the correct directory structure and configuration.

### Prerequisites

Install `cookiecutter` via your package manager (see the [official installation guide](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) for more details):

```bash
pip install cookiecutter
```

### Scaffolding

Run the cookiecutter template from any location:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

The template prompts for several variables like your plugin name, package slug, and version. Once generated, you receive a self-contained package with:

* A `src/` directory containing your plugin class and fields.
* The required `templates/`, `static/`, and `translations/` folders correctly namespaced.
* A complete test suite.
* A runnable example application.

## The Plugin API

At the core of every plugin is a subclass of `BasePlugin` (`starlette_admin.plugins.BasePlugin`). This class provides hooks to register your features during the `Admin` initialization phase.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

The `name` attribute is a unique kebab-case identifier. It doubles as the namespace for all your templates and static assets. Every template and static file your plugin ships must reside strictly under `plugins/<name>/`.

### Asset Folders

A plugin can include exactly three folders at the root of its package. There is nothing to register because the admin discovers them by convention:

* `templates/`: Contains Jinja templates, which must sit beneath `templates/plugins/<name>/`.
* `static/`: Contains static assets like CSS and JS files, which must sit beneath `static/plugins/<name>/`.
* `translations/`: Contains Babel translation catalogs.

By adhering to the `plugins/<name>/` namespace, your assets will never collide with core files or other plugins, yet they remain fully overridable by the end user via their own `templates_dir` or `static_dir`.

### Declarative Hooks

Override declarative hooks to inject assets, register views, or mount routes.

* `css_links(self, request: Request) -> Sequence[str]`: Injects stylesheets into every admin page layout.
* `js_links(self, request: Request) -> Sequence[str]`: Injects scripts into every admin page layout.
* `views(self) -> Sequence[BaseView]`: Returns a list of views to register with the admin sidebar. You can group these views by returning a `DropDown`.
* `routes(self) -> Sequence[Route | Mount]`: Returns headless endpoints mounted under `/plugins/<name>/` (useful for webhooks or proxy endpoints).
* `middlewares(self) -> Sequence[Middleware]`: Injects Starlette middlewares.
* `template_globals(self) -> dict[str, Any]`: Exposes Jinja globals, which are automatically prefixed with `<name>_` to prevent collisions.
* `template_filters(self) -> dict[str, Callable]`: Exposes Jinja filters, automatically prefixed with `<name>_`.

### The Setup Hook

The `setup(self, admin: BaseAdmin) -> None` hook handles integration with existing core registries. Use this to register model converters, filters, import/export formats, storage backends, and event subscribers. This runs after the declarative hooks are applied.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### The Lifecycle Hook

The `on_mount(self, admin: BaseAdmin) -> None` hook runs exactly once after the Starlette sub-application is fully built and mounted. The built application is accessible via `admin.app`.

## Templates and Overrides

Plugin templates are automatically added to the loader chain. A user can override any plugin template by placing a file at the matching path inside their own `templates_dir`. For example, to override `plugins/geospatial/fields/form/point.html`, the user creates `templates_dir/plugins/geospatial/fields/form/point.html` because the user directory always takes priority.

To allow user templates to safely extend the original plugin templates, every plugin receives a `@<name>` prefix mapping. This functions exactly like the `@core` prefix. A user override can include `{% extends "@geospatial/fields/form/point.html" %}` to extend the base plugin template without recursive inclusion.


## Frontend JavaScript Integration

Plugins that provide custom fields should package their frontend scripts according to the field initializer contract. This ensures stability across full page loads and dynamic fragment insertions.

* **Target locally:** Always query within the provided `container` element, not the global `document`.
* **Be idempotent:** Core calls the initialization routine on DOM ready, and again whenever inline rows or fragments are inserted.
* **Use data attributes:** Read configuration directly from `data-*` attributes rendered on the field element.

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

  // Registers the initializer to run on appropriate lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## Extension Points via the Setup Hook

Plugins leverage existing public registries rather than inventing separate extension pathways.

* **Converters**: Call `register_converter` (from the respective contrib backend) to map ORM column types to your custom field classes. Define the field itself as a regular `StringField` subclass, storing and displaying geometries as WKT text:

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

* **Filters**: Call `register_filters` to attach filter classes to specific field types.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Storage**: Call `register_storage` to expose a new backend (like Azure or GCS).

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importers and Exporters**: Use `register_import_format` and `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Since a plugin might support multiple ORM backends, you should use conditional imports inside `setup()` to avoid breaking if the user only installed one backend:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```
