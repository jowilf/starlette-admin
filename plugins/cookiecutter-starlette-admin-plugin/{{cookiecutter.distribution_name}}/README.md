# {{ cookiecutter.plugin_name }}

{{ cookiecutter.description }}

A [starlette-admin](https://github.com/jowilf/starlette-admin) plugin.

## Install

```bash
pip install {{ cookiecutter.distribution_name }}
```

## Usage

```python
from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Plugin

admin = Admin(engine, plugins=[{{ cookiecutter.class_prefix }}Plugin()])
```

See [docs/index.md](docs/index.md) for options{% if cookiecutter.include_example_field == "yes" %} and the `{{ cookiecutter.class_prefix }}RatingField` field{% endif %}.

## Development

```bash
uv sync
uv run pytest
uv run python example/app.py  # demo at http://localhost:8000/admin/
```

## License

{{ cookiecutter.license }}
