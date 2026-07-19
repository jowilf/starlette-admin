# Contrib: SQLAlchemy

Full attribute and method reference for the SQLAlchemy backend (`starlette_admin.contrib.sqla`),
generated from docstrings. For a task-oriented walkthrough, see
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Pydantic validation

The `ext.pydantic` extension validates form data against a Pydantic model before writing the
record. See [Pydantic validation](../../integrations/sqlalchemy.md#pydantic-validation) for the
full walkthrough.

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Fields

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Converters

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Exceptions

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Concrete filter classes (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, and so on) are not
    enumerated here. They mirror the backend-agnostic filters documented in
    [Filters](../filters.md) one-to-one; the SQLAlchemy-specific behavior worth knowing is
    covered in [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry).
