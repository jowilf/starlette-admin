# 11: SQLAlchemy + Pydantic Validation

Form validation powered by Pydantic schemas on top of a SQLAlchemy backend.

## What it shows

- `ModelView` from `starlette_admin.contrib.sqla.ext.pydantic` instead of the regular one
- A Pydantic `BaseModel` passed as `pydantic_model=` drives all validation rules
- Field-level constraints via `Field(min_length=…)` and `EmailStr` / `HttpUrl` type checking
- Custom `@field_validator` for business-logic rules (full name must contain first + last name)
- Validation errors surface inline on the form, no custom error-handling code needed
- `PostView` subclasses `ModelView` to add a `SlugField` (auto-populated from `title`) and a
  `ComputedField` for word count, plus `form_layout`, `exclude_fields_from_create` /
  `exclude_fields_from_edit`, `searchable_fields`, `fields_default_sort`, and `search_auto_submit`
  overrides

## Run

```bash
cd examples/11-sqla-pydantic-fastapi
uv run app.py
```

Then open <http://localhost:8000/admin/>.
