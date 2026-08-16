# 14: SQLModel (comprehensive)

A CMS-style demo that showcases a broad slice of starlette-admin features
using **SQLModel** as the ORM layer.

## Features covered

| Feature | Where |
|---|---|
| SQLModel models with relationships & enums | `models.py` |
| `EmailStr` / Pydantic field validation | `Author.email` |
| Field types: Email, Color, Tags, TextArea, Enum, DateTime, Boolean | `views.py` |
| `InlineModelView` for comments inside the Article form | `CommentInline` |
| Lifecycle hooks (`before_create`, `before_edit`) for timestamps | `AuthorView`, `ArticleView`, `CommentView` |
| `AdminEventSubscriber` for cross-view audit logging | `AuditSubscriber` in `app.py` |
| Batch `@action` (publish, archive) | `ArticleView` |
| Per-row `@row_action` (quick-publish) | `ArticleView` |
| Column-level filter (`DateTimeBetween` on `created_at`) | `ArticleView` |
| Export to CSV and Excel | `AuthorView`, `ArticleView` |
| `searchable_fields`, `sortable_fields`, `fields_default_sort` | all views |

## Domain

```
Author ──< Article >── Category
               │
               └──< Comment
```

## Running

```bash
cd examples/14-sqlmodel
uv run app.py
```

Then open <http://localhost:8000/admin/>.

The database is seeded automatically on the first run.
