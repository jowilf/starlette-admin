# 17-tortoise: Tortoise ORM + SQLite example

A small blog admin built on [Tortoise ORM](https://tortoise.github.io/) and
SQLite, showcasing the `starlette_admin.contrib.tortoise` backend.

## Features demonstrated

- Tortoise models with foreign key, one-to-one and many-to-many relations
- Automatic field conversion: enums, JSON, dates and auto timestamps
- `InlineModelView`: comments edited inline inside the Post form
- Backward relations rendered read-only on the Author view
- Full-text search, sorting and the filter builder

## Run

From this directory:

```bash
uv sync
uv run python app.py
```

Then open <http://127.0.0.1:8000/admin>. The database (`blog.sqlite3`) is
created and seeded automatically on first run.
