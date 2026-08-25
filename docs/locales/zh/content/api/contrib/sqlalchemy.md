---
title: SQLAlchemy Contrib API 参考
description: starlette-admin 的 SQLAlchemy 后端集成 API 参考文档。
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib：SQLAlchemy

SQLAlchemy 后端（`starlette_admin.contrib.sqla`）的完整属性和方法参考，由 docstring 生成。如需面向任务的指引，请参阅 [SQLAlchemy 集成](../../integrations/sqlalchemy.md)。

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Pydantic 校验

`ext.pydantic` 扩展会在写入记录之前，先针对 Pydantic 模型校验表单数据。完整流程请参阅 [Pydantic 校验](../../integrations/sqlalchemy.md#pydantic-validation)。

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## 字段

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## 转换器

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## 异常

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    具体的过滤器类（`EqualFilter`、`ContainsFilter`、`BetweenFilter` 等）不在此处一一列出。它们与[过滤器](../filters.md)中记录的与后端无关的过滤器类一一对应；值得了解的 SQLAlchemy 特定行为请参阅 [SQLAlchemy 集成](../../integrations/sqlalchemy.md#filter-registry)。
