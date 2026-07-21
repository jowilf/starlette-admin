# Geospatial

A starlette-admin plugin

A [starlette-admin](https://github.com/jowilf/starlette-admin) plugin.

## Install

```bash
pip install starlette-admin-geospatial
```

## Usage

```python
from starlette_admin_geospatial import GeospatialPlugin

admin = Admin(engine, plugins=[GeospatialPlugin()])
```

See [docs/index.md](docs/index.md) for options and the `GeospatialRatingField` field.

## Development

```bash
uv sync
uv run pytest
uv run python example/app.py  # demo at http://localhost:8000/admin/
```

## License

MIT
