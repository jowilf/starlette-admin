---
title: Справочник по Admin API
description: Справочная документация по классу Admin в starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Полный справочник атрибутов и методов `BaseAdmin`, сгенерированный на основе его docstring. Пошаговое
описание параметров конструктора, ориентированное на практические задачи, см. в разделе
[Configuring Admin](../user-guide/admin.md).

`starlette_admin` не экспортирует собственный конкретный класс `Admin`. Каждый backend в
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) предоставляет свой подкласс `Admin`
с той же сигнатурой конструктора, которая описана ниже.

::: starlette_admin.base.BaseAdmin
