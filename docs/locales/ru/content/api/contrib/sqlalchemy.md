---
title: Справочник API SQLAlchemy Contrib
description: Справочная документация по API интеграции SQLAlchemy backend в starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Полный справочник атрибутов и методов для SQLAlchemy backend (`starlette_admin.contrib.sqla`),
сгенерированный из docstrings. Пошаговое руководство по решению задач см. в разделе
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Валидация с помощью Pydantic

Расширение `ext.pydantic` выполняет валидацию данных формы на соответствие модели Pydantic
перед записью объекта. Полное пошаговое руководство см. в разделе
[Валидация с помощью Pydantic](../../integrations/sqlalchemy.md#pydantic-validation).

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Поля (Fields)

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
    здесь не перечисляются. Они один к одному повторяют фильтры, не зависящие от backend,
    задокументированные в разделе [Фильтры](../filters.md); специфика поведения, связанная
    с SQLAlchemy, описана в разделе [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry).
