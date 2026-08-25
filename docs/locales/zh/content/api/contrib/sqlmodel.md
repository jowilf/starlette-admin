---
title: SQLModel Contrib API 参考
description: starlette-admin 的 SQLModel 后端集成 API 参考文档。
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib：SQLModel

SQLModel 后端（`starlette_admin.contrib.sqlmodel`）的完整属性和方法参考，由 docstring 生成。SQLModel 底层基于 SQLAlchemy，因此 `Admin` 和 `ModelView` 是 [SQLAlchemy 后端](sqlalchemy.md)的轻量子类，并通过模型的 Pydantic 层校验表单数据。如需面向任务的指引，请参阅 [SQLModel 集成](../../integrations/sqlmodel.md)。

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
