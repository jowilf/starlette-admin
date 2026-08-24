---
title: Установка
description: Узнайте, как установить starlette-admin и его необязательные зависимости,
  чтобы создать интерфейс администрирования для вашего приложения FastAPI или Starlette.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# Установка

Установите **starlette-admin** с помощью предпочитаемого менеджера пакетов.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin требует **Python 3.11 или новее**.

Базовый пакет не зависит от бэкенда. Чтобы создать интерфейс администрирования для своего приложения, установите вместе с базовым пакетом подходящую интеграцию для вашего слоя данных (например, SQLAlchemy, Beanie, MongoEngine или Tortoise ORM).

## Включённые зависимости

Базовая установка включает всё необходимое для работы интерфейса администрирования. Необязательные зависимости по умолчанию не устанавливаются.

| Зависимость | Назначение |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Обеспечивает работу приложения администрирования. |
| [Jinja2](https://jinja.palletsprojects.com/) | Предоставляет шаблонизатор для страниц списка, деталей и форм. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Разбирает отправленные формы и загружаемые файлы. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Подписывает cookie для CSRF-токенов и флеш-сообщений. |

Приложениям на FastAPI дополнительная интеграция не требуется, так как FastAPI построен на Starlette. Просто подключите интерфейс администрирования к своему существующему приложению FastAPI.

## Необязательные зависимости

starlette-admin предоставляет следующие необязательные зависимости:

- `pdf`: добавляет поддержку экспорта в PDF ([reportlab](https://www.reportlab.com/)).
- `i18n`: добавляет поддержку интернационализации ([Babel](https://babel.pocoo.org/)).
- `tinymce`: добавляет поддержку редактора форматированного текста. Устанавливает [nh3](https://nh3.readthedocs.io/), который очищает HTML, отправляемый полем `TinyMCEEditorField`.
- `s3`: добавляет поддержку объектного хранилища, совместимого с S3. Устанавливает [aiobotocore](https://aiobotocore.readthedocs.io/) для асинхронной загрузки в AWS S3 и совместимые сервисы объектного хранения, такие как MinIO.

Установите одну или несколько необязательных зависимостей вместе со starlette-admin:

=== "pip"

    ```bash
    # Install the `pdf` extra.
    pip install "starlette-admin[pdf]"

    # Install multiple extras.
    pip install "starlette-admin[i18n,pdf,s3]"
    ```

=== "uv"

    ```bash
    # Install the `pdf` extra.
    uv add "starlette-admin[pdf]"

    # Install multiple extras.
    uv add "starlette-admin[i18n,pdf,s3]"
    ```

## Установка из исходного кода

Чтобы использовать последние ещё не выпущенные изменения, установите пакет напрямую из репозитория GitHub.

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## Следующие шаги

- **[Быстрый старт](quickstart.md)**: создайте свой первый интерфейс администрирования с реальными данными.
- **[Концепции](concepts.md)**: узнайте об основной архитектуре и принципах проектирования starlette-admin.
