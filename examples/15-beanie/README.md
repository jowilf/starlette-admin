# 15: Beanie (comprehensive)

A library-catalog demo that showcases a broad slice of starlette-admin features
using **Beanie** as the ODM layer (MongoDB via PyMongo's async API).

## Features covered

| Feature | Where |
|---|---|
| Beanie Documents with `Link` relationships & enums | `models.py` |
| `EmailStr` / Pydantic field validation | `Member.email` |
| Field types: Email, Color, Tags, TextArea, Enum, DateTime, Boolean, Integer | `views.py` |
| `ImageField` with `LocalStorage`: book cover photo | `BookView` |
| `FileField` with `LocalStorage`: sample PDF preview | `BookView` |
| Custom file-type validator (`filetype` library) | `validate_pdf` in `views.py` |
| `InlineModelView` for loans embedded inside the Member form | `LoanInline` |
| Lifecycle hook (`before_create`) for automatic timestamps | `BookView`, `MemberView` |
| `AdminEventSubscriber` for cross-view audit logging | `AuditSubscriber` in `app.py` |
| Batch `@action` (mark returned, mark overdue) | `LoanView` |
| Per-row `@row_action` (quick return) | `LoanView` |
| Column-level filter (`DateTimeBetween` on `loan_date`) | `LoanView` |
| Export to CSV and Excel | `BookView`, `MemberView`, `LoanView` |
| `searchable_fields`, `sortable_fields`, `fields_default_sort` | all views |

## Domain

```
Genre <──< Book
            │
Member ──< Loan >── Book
```

## Running

```bash
cd examples/15-beanie
uv run app.py
```

Then open <http://localhost:8000/admin/>.

MongoDB must be reachable at `mongodb://localhost:27017` (override with the
`MONGO_URI` environment variable). The database is seeded automatically on the
first run.
