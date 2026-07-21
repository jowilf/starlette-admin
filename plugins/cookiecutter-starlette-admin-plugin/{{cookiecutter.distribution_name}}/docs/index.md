# {{ cookiecutter.plugin_name }}

{{ cookiecutter.description }}

## Install

```bash
pip install {{ cookiecutter.distribution_name }}
```

## Usage

```python
from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Plugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[{{ cookiecutter.class_prefix }}Plugin()])
```

That is the only integration point. Options are passed straight to the
constructor:

```python
{{ cookiecutter.class_prefix }}Plugin(example_option="custom value")
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `example_option` | `"default value"` | Replace with this plugin's real options, documented from `{{ cookiecutter.class_prefix }}Config` in `src/{{ cookiecutter.package_slug }}/plugin.py`. |

{% if cookiecutter.include_example_field == "yes" %}

## Fields

### `{{ cookiecutter.class_prefix }}SliderField`

Renders an integer as a range slider with a live value label.

```python
from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}SliderField

class ProductView(ModelView):
    fields = ["id", "name", {{ cookiecutter.class_prefix }}SliderField("discount", min_value=0, max_value=100, suffix="%")]
```
{% endif %}

## Overriding templates and assets

Every file this plugin ships lives under `plugins/{{ cookiecutter.plugin_slug }}/`.
Drop a file at the matching path under your own `templates_dir` (for
templates) or `static_dir` (for static assets) to override it, the same way
you would override a core template:

```
your_project/
├── templates/
│   └── plugins/{{ cookiecutter.plugin_slug }}/fields/form/slider.html   # overrides this plugin's template
└── static/
    └── plugins/{{ cookiecutter.plugin_slug }}/css/slider.css           # overrides this plugin's stylesheet
```

Extend the shipped original from your override with the `@{{ cookiecutter.plugin_slug }}`
prefix, which always resolves to the plugin's own copy:

```jinja
{{ '{%' }} extends "@{{ cookiecutter.plugin_slug }}/fields/form/slider.html" {{ '%}' }}
```
