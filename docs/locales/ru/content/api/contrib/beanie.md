---
title: Справочник API модуля Beanie Contrib
description: Справочная документация по API интеграции бэкенда Beanie в starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib: Beanie

Полный справочник атрибутов и методов для бэкенда Beanie (`starlette_admin.contrib.beanie`),
сгенерированный из докстрингов. Пошаговое руководство с примерами задач см. в разделе
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Поля

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Конвертеры

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Конкретные классы фильтров (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` и так далее)
    здесь не перечислены. Они повторяют не зависящие от бэкенда фильтры, описанные в разделе
    [Фильтры](../filters.md); специфичное для Beanie поведение (сопоставление строк с помощью
    заякоренных регулярных выражений, полнотекстовый поиск) рассматривается в разделе
    [Beanie](../../integrations/beanie.md#filter-registry).
