---
title: Справочник API модуля contrib для Tortoise ORM
description: Справочная документация по API интеграции бэкенда Tortoise ORM в starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM

Полный справочник атрибутов и методов для бэкенда Tortoise ORM
(`starlette_admin.contrib.tortoise`), сгенерированный из докстрингов.
Пошаговое руководство см. в разделе [Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Поля

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Конвертеры

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Конкретные классы фильтров (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter` и так далее)
    здесь не перечислены. Они повторяют не зависящие от бэкенда фильтры, описанные в разделе
    [Фильтры](../filters.md); специфичное для Tortoise поведение (поиск без учёта регистра,
    приведение перечислений, проверки на NULL в исходных столбцах ключей) рассматривается в
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry).
