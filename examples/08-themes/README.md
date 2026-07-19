# 08: Themes (ThemeSettings + SQLAlchemy)

A minimal admin that demonstrates `ThemeSettings` by picking a random theme on every startup.

## What it shows

- **`ThemeSettings`**: passed as `theme=` to `Admin`, it controls the Bootstrap theme via `data-bs-theme-*` attributes on the `<html>` element.
- **Random theme on startup**: `base`, `primary`, and `radius` are chosen at random each time the server starts, so refreshing after a restart shows a different look.


## Run

```bash
cd examples/08-themes
uv run app.py
```

Then open <http://localhost:8000/admin/>. Restart the server to get a new random theme.
