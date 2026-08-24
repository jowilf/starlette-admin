---
title: Admin API 参考
description: starlette-admin 的 Admin 类 API 参考文档。
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

`BaseAdmin` 的完整属性与方法参考，内容由其 docstring 生成。有关构造函数选项的面向任务式讲解，请参阅[配置 Admin](../user-guide/admin.md)。

`starlette_admin` 本身不导出具体的 `Admin` 类。`starlette_admin.contrib` 中的每个后端（`sqla`、`sqlmodel`、`beanie`、`mongoengine`、`tortoise`）都提供自己的 `Admin` 子类，其构造函数签名与下文所述相同。

::: starlette_admin.base.BaseAdmin
