# 12: SQLAlchemy Composite Primary Keys

Managing many-to-many join tables where the primary key spans multiple foreign-key columns.

## What it shows

- `Enrollment` model with a composite PK (`student_id` + `course_id`), no surrogate `id` column
- `ModelView` works with composite PKs out of the box; no extra configuration needed
- `__admin_repr__` on related models (`Student`, `Course`) for human-readable select dropdowns
- `EnumField` with a custom `choices` list for letter grades (no `select2` styling)
- `handle_exception` overridden on `EnrollmentView` to catch `IntegrityError` on duplicate enrollment and surface it as a friendly inline `FormValidationError`

## Run

```bash
cd examples/12-sqla-composite-pks
uv run app.py
```

Then open <http://localhost:8000/admin/>.
