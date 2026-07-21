# Geospatial

A starlette-admin plugin

## Install

```bash
pip install starlette-admin-geospatial
```

## Usage

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin()])
```

That is the only integration point. Options are passed straight to the
constructor:

```python
GeospatialPlugin(example_option="custom value")
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `example_option` | `"default value"` | Replace with this plugin's real options, documented from `GeospatialConfig` in `src/starlette_admin_geospatial/plugin.py`. |


## Fields

### `GeospatialRatingField`

Renders an integer as clickable stars.

```python
from starlette_admin_geospatial import GeospatialRatingField

class ProductView(ModelView):
    fields = ["id", "name", GeospatialRatingField("rating", max_stars=5)]
```

## Overriding templates and assets

Every file this plugin ships lives under `plugins/geospatial/`.
Drop a file at the matching path under your own `templates_dir` (for
templates) or `static_dir` (for static assets) to override it, the same way
you would override a core template:

```
your_project/
├── templates/
│   └── plugins/geospatial/fields/form/rating.html   # overrides this plugin's template
└── static/
    └── plugins/geospatial/css/rating.css           # overrides this plugin's stylesheet
```

Extend the shipped original from your override with the `@geospatial`
prefix, which always resolves to the plugin's own copy:

```jinja
{% extends "@geospatial/fields/form/rating.html" %}
```
