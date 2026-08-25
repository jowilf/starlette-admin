---
title: MongoEngine Contrib API 参考
description: starlette-admin 的 MongoEngine 后端集成 API 参考文档。
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib：MongoEngine

MongoEngine 后端（`starlette_admin.contrib.mongoengine`）的完整属性和方法参考，由 docstring 生成。如需面向任务的指引，请参阅 [MongoEngine 集成](../../integrations/mongoengine.md)。

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## 字段

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## 转换器

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## 异常

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    具体的过滤器类（`EqualFilter`、`ArrayInFilter`、`ObjectIdEqualFilter` 等）不在此处一一列出。它们与[过滤器](../filters.md)中记录的与后端无关的过滤器类一一对应；MongoEngine 特定的行为请参阅 [MongoEngine 集成](../../integrations/mongoengine.md#filter-registry)。
