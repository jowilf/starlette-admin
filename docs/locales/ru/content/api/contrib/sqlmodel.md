---
title: Справочник API для contrib-модуля SQLModel
description: Справочная документация по интеграции бэкенда SQLModel в starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel

Полный справочник атрибутов и методов бэкенда SQLModel (`starlette_admin.contrib.sqlmodel`),
сгенерированный из докстрингов. В основе SQLModel лежит SQLAlchemy, поэтому `Admin` и `ModelView` —
это тонкие подклассы [бэкенда SQLAlchemy](sqlalchemy.md), которые валидируют данные форм через слой
Pydantic модели. Пошаговое руководство с примерами задач см. в разделе
[Интеграция SQLModel](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
