---
title: Справочник API Contrib для Tortoise ORM
description: Справочная документация по API интеграции backend'а Tortoise ORM в starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM

Полный справочник атрибутов и методов backend'а Tortoise ORM
(`starlette_admin.contrib.tortoise`), сгенерированный из docstring. Пошаговое
руководство по использованию см. в разделе [Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Fields

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Converters

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Конкретные классы фильтров (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter` и т. д.)
    здесь не перечисляются. Они повторяют не зависящие от backend'а фильтры, описанные в разделе
    [Filters](../filters.md); специфичное для Tortoise поведение (поиск без учёта регистра,
    приведение enum, проверки на NULL по «сырым» ключевым столбцам) рассматривается в разделе
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry).
