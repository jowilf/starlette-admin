# 01: Quickstart

A minimal blog administration interface built using SQLAlchemy and starlette-admin.

## Key Features Demonstrated

- `ModelView` wired to a SQLAlchemy model
- `SlugField` that auto-populates from the title
- `ComputedField` (word count) derived at render time
- Column sorting, full-text search with auto-submit
- Enum status column (`DRAFT` / `PUBLISHED` / `ARCHIVED`)

## Usage

```bash
cd examples/01-quickstart
uv run app.py
```

Then open <http://localhost:8000/admin/>.

Sample posts are seeded automatically on first startup.
