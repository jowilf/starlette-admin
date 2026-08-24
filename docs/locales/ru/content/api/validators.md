---
title: Справочник API валидаторов
description: Справочная документация по валидаторам полей форм в starlette-admin.
source_hash: 42e3fab8cab328d3c9f6ee206f8e80a246ccb8d84625a9da35ee0afd4f8bd644
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/validators/)
<!-- translation-notice:end -->

# Валидаторы

Встроенные валидаторы полей, которые можно подключить к любому полю через `BaseField(validators=[...])` и которые выполняются методом `BaseField.validate`. Обзор процесса валидации см. в разделе [Поля](../user-guide/fields.md).

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

## Валидаторы файлов

::: starlette_admin.validators.file_size

::: starlette_admin.validators.file_type

::: starlette_admin.validators.valid_image

::: starlette_admin.validators.image_size
