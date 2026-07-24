# AdminLTE

A starlette-admin theme

A [starlette-admin](https://github.com/jowilf/starlette-admin) theme.

## Install

```bash
pip install starlette-admin-adminlte
```

## Usage

```python
from starlette_admin_adminlte import AdminlteTheme

admin = Admin(engine, theme=AdminlteTheme())
```

See [docs/index.md](docs/index.md) for options and the template/asset override guide.

## Development

```bash
uv sync
uv run pytest
uv run python example/app.py  # demo at http://localhost:8000/admin/
```

## License

MIT
