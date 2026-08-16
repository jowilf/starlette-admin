---
title: Beanie Contrib API Reference
description: API reference documentation for the Beanie backend integration in starlette-admin.
---

# Contrib: Beanie

Full attribute and method reference for the Beanie backend (`starlette_admin.contrib.beanie`),
generated from docstrings. For a task-oriented walkthrough, see
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Fields

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converters

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Concrete filter classes (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, and so on) are
    not enumerated here. They mirror the backend-agnostic filters documented in
    [Filters](../filters.md); Beanie-specific behavior (anchored regex string matching, full-text
    search) is covered in [Beanie](../../integrations/beanie.md#filter-registry).
