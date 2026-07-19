# Contrib: Tortoise ORM

Full attribute and method reference for the Tortoise ORM backend
(`starlette_admin.contrib.tortoise`), generated from docstrings. For a
task-oriented walkthrough, see [Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Fields

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Converters

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Concrete filter classes (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter`, and so on)
    are not enumerated here. They mirror the backend-agnostic filters documented in
    [Filters](../filters.md); Tortoise-specific behavior (case-insensitive lookups, enum coercion,
    raw key column null checks) is covered in
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry).
