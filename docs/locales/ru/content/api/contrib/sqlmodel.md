---
title: Справочник API для Contrib SQLModel
description: Справочная документация по API интеграции с backend SQLModel в starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel

Полный справочник атрибутов и методов backend'а SQLModel (`starlette_admin.contrib.sqlmodel`),
сгенерированный из docstring. В основе SQLModel лежит SQLAlchemy, поэтому `Admin` и `ModelView` — это
тонкие подклассы [SQLAlchemy backend'а](sqlalchemy.md), которые валидируют данные форм через
Pydantic-слой модели. Пошаговое практическое руководство см. в разделе
[Интеграция SQLModel](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
