---
title: 校验器 API 参考
description: starlette-admin 表单字段校验器的 API 参考文档。
source_hash: 42e3fab8cab328d3c9f6ee206f8e80a246ccb8d84625a9da35ee0afd4f8bd644
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/validators/)
<!-- translation-notice:end -->

# 校验器

内置字段校验器，可通过 `BaseField(validators=[...])` 附加到任意字段，并由 `BaseField.validate` 执行。有关校验流程的概述，请参阅[字段](../user-guide/fields.md)。

::: starlette_admin.validators.length

::: starlette_admin.validators.number_range

::: starlette_admin.validators.number_gt

::: starlette_admin.validators.number_lt

::: starlette_admin.validators.date_range

::: starlette_admin.validators.regexp

::: starlette_admin.validators.disallow

::: starlette_admin.validators.mac_address

::: starlette_admin.validators.slug

::: starlette_admin.validators.color

::: starlette_admin.validators.email

::: starlette_admin.validators.url

::: starlette_admin.validators.uuid

::: starlette_admin.validators.ip_address

::: starlette_admin.validators.any_of

::: starlette_admin.validators.none_of

::: starlette_admin.validators.items

## 文件校验器

::: starlette_admin.validators.file_size

::: starlette_admin.validators.file_type

::: starlette_admin.validators.valid_image

::: starlette_admin.validators.image_size
