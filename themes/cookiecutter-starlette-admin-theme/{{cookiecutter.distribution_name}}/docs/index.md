# {{ cookiecutter.theme_name }}

{{ cookiecutter.description }}

## Install

```bash
pip install {{ cookiecutter.distribution_name }}
```

## Usage

```python
from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Theme
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, theme={{ cookiecutter.class_prefix }}Theme())
```

That is the only integration point. Options are passed straight to the constructor:

```python
{{ cookiecutter.class_prefix }}Theme(example_option="custom value")
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `example_option` | `"default value"` | Replace with this theme's real options, documented from `{{ cookiecutter.class_prefix }}Config` in `src/{{ cookiecutter.package_slug }}/theme.py`. |

## What this theme ships

- **Icon set**: swaps the default FontAwesome for [Tabler Icons](https://tabler.io/icons). See `src/{{ cookiecutter.package_slug }}/icons.py`.
- **Templates**: `templates/base.html` extends the core base and appends this theme's stylesheet. Add `layout.html`, `index.html`, `login.html`, ... at the same bare paths to override more of the shell.
- **Static assets**: `static/css/theme.css` holds the example visual overrides.

## Overriding templates and assets

A theme sits above plugins in the loader chain (precedence: user > theme > plugins > core). Drop a file at the matching path under your own `templates_dir` or `static_dir` to override it, the same way you would override a core template.

When your own override needs to extend this theme's template (instead of the core's), use the `@theme` prefix, which always resolves to this theme's own copy:

```jinja
{{ '{%' }} extends "@theme/base.html" {{ '%}' }}
```
