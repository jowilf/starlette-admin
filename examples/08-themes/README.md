# 08: Themes (TablerSettings + SQLAlchemy)

A minimal admin that demonstrates `TablerSettings` by picking a random palette on every startup.

## What it shows

- **`TablerSettings`**: passed to `DefaultTheme(settings=...)`, which is in turn passed as `theme=` to `Admin`, it controls the Tabler palette via `data-bs-theme-*` attributes on the `<html>` element.
- **Random palette on startup**: `base`, `primary`, and `radius` are chosen at random each time the server starts, so refreshing after a restart shows a different look.


## Run

```bash
cd examples/08-themes
uv run app.py
```

Then open <http://localhost:8000/admin/>. Restart the server to get a new random theme.
