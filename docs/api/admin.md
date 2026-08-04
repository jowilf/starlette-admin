---
title: Admin API Reference
description: API reference documentation for the Admin class in starlette-admin.
---

# Admin

Full attribute and method reference for `BaseAdmin`, generated from its docstrings. For a
task-oriented walkthrough of its constructor options, see
[Configuring Admin](../user-guide/admin.md).

`starlette_admin` exports no concrete `Admin` class of its own. Each backend in
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) ships its own `Admin`
subclass with the same constructor signature documented below.

::: starlette_admin.base.BaseAdmin
