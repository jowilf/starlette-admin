---
title: Tortoise ORM Contrib API 参考
description: starlette-admin 的 Tortoise ORM 后端集成 API 参考文档。
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib：Tortoise ORM

Tortoise ORM 后端（`starlette_admin.contrib.tortoise`）的完整属性和方法参考，由 docstring 生成。如需面向任务的指引，请参阅 [Tortoise ORM 集成](../../integrations/tortoise.md)。

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## 字段

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## 转换器

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    具体的过滤器类（`ContainsFilter`、`EnumInFilter`、`RelationIsNullFilter` 等）不在此处一一列出。它们与[过滤器](../filters.md)中记录的与后端无关的过滤器类一一对应；Tortoise 特定的行为（不区分大小写的查找、枚举强制转换、原始键列的空值检查）请参阅 [Tortoise ORM 集成](../../integrations/tortoise.md#filter-registry)。
