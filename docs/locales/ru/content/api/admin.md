---
title: Справочник по API класса Admin
description: Справочная документация по классу Admin в starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Полный справочник атрибутов и методов `BaseAdmin`, созданный на основе его докстрингов. Пошаговое описание параметров конструктора с примерами решения конкретных задач см. в разделе [Настройка Admin](../user-guide/admin.md).

В `starlette_admin` нет собственного конкретного класса `Admin`. Каждый бэкенд в `starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) предоставляет собственный подкласс `Admin` с той же сигнатурой конструктора, которая описана ниже.

::: starlette_admin.base.BaseAdmin
