---
title: Справочник API Contrib для MongoEngine
description: Справочная документация по интеграции backend'а MongoEngine в starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

Полный справочник атрибутов и методов backend'а MongoEngine
(`starlette_admin.contrib.mongoengine`), сгенерированный из docstring. Пошаговое руководство по использованию см. в разделе [MongoEngine](../../integrations/mongoengine.md).

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## Fields

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## Converters

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## Exceptions

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    Конкретные классы фильтров (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` и т. д.) здесь не перечислены. Они повторяют фильтры, независимые от backend'а, описанные в разделе [Filters](../filters.md); специфичное для MongoEngine поведение рассматривается в разделе
    [MongoEngine](../../integrations/mongoengine.md#filter-registry).
