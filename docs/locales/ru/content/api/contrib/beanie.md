---
title: Справочник API Contrib для Beanie
description: Справочная документация по API интеграции Beanie backend в starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib: Beanie

Полный справочник атрибутов и методов для Beanie backend (`starlette_admin.contrib.beanie`),
сгенерированный из docstrings. Пошаговое руководство с примерами задач см. в разделе
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Fields

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converters

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Конкретные классы фильтров (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` и т. д.)
    здесь не перечисляются. Они повторяют фильтры, не зависящие от backend, описанные в разделе
    [Filters](../filters.md); специфичное для Beanie поведение (поиск по строкам с привязанным regex,
    полнотекстовый поиск) рассматривается в разделе [Beanie](../../integrations/beanie.md#filter-registry).
