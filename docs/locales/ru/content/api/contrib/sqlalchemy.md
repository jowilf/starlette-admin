---
title: Справочник API для SQLAlchemy Contrib
description: Справочная документация по интеграции с бэкендом SQLAlchemy в starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Полный справочник атрибутов и методов бэкенда SQLAlchemy (`starlette_admin.contrib.sqla`),
сгенерированный из докстрингов. Пошаговое руководство по задачам см. в разделе
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Валидация Pydantic

Расширение `ext.pydantic` проверяет данные формы на соответствие модели Pydantic перед записью
записи. Полное пошаговое описание см. в разделе
[Валидация Pydantic](../../integrations/sqlalchemy.md#pydantic-validation).

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Поля

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Конвертеры

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Исключения

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Конкретные классы фильтров (`EqualFilter`, `ContainsFilter`, `BetweenFilter` и так далее)
    здесь не перечислены. Они один к одному повторяют фильтры, не зависящие от бэкенда,
    описанные в разделе [Фильтры](../filters.md); специфичное для SQLAlchemy поведение,
    о котором стоит знать, рассмотрено в разделе
    [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry).
