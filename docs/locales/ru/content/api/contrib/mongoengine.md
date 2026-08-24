---
title: Справочник API модуля Contrib для MongoEngine
description: Справочная документация по интеграции бэкенда MongoEngine в starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib: MongoEngine

Полный справочник атрибутов и методов для бэкенда MongoEngine
(`starlette_admin.contrib.mongoengine`), сгенерированный из докстрингов. Пошаговое руководство по задачам см. в разделе [MongoEngine](../../integrations/mongoengine.md).

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## Поля

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## Конвертеры

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## Исключения

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    Конкретные классы фильтров (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` и так далее) здесь не перечислены. Они повторяют не зависящие от бэкенда фильтры, описанные в разделе [Фильтры](../filters.md); специфичное для MongoEngine поведение рассматривается в разделе [MongoEngine](../../integrations/mongoengine.md#filter-registry).
