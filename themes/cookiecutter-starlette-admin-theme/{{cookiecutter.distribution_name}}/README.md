# {{ cookiecutter.theme_name }}

{{ cookiecutter.description }}

A [starlette-admin](https://github.com/jowilf/starlette-admin) theme.

## Install

```bash
pip install {{ cookiecutter.distribution_name }}
```

## Usage

```python
from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Theme

admin = Admin(engine, theme={{ cookiecutter.class_prefix }}Theme())
```

See [docs/index.md](docs/index.md) for options and the template/asset override guide.

## Development

```bash
uv sync
uv run pytest
uv run python example/app.py  # demo at http://localhost:8000/admin/
```

## License

{{ cookiecutter.license }}
