---
title: Установка
description: Узнайте, как установить starlette-admin и его необязательные зависимости
  для создания административного интерфейса в вашем приложении FastAPI или Starlette.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
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

Базовый пакет не зависит от backend-решений. Чтобы создать административный интерфейс для вашего приложения, установите вместе с базовым пакетом подходящую интеграцию для вашего слоя данных (например, SQLAlchemy, Beanie, MongoEngine или Tortoise ORM).

## Включённые зависимости

Базовая установка содержит всё необходимое для работы административного интерфейса. По умолчанию необязательные зависимости не устанавливаются.

| Зависимость | Назначение |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Обеспечивает работу административного приложения. |
| [Jinja2](https://jinja.palletsprojects.com/) | Предоставляет шаблонизатор для страниц списков, деталей и форм. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Разбирает отправленные формы и загружаемые файлы. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Подписывает cookies для CSRF-токенов и flash-сообщений. |

Приложениям на FastAPI не требуется дополнительная интеграция, поскольку FastAPI построен на Starlette. Достаточно подключить административный интерфейс к вашему существующему приложению FastAPI.

## Необязательные зависимости

starlette-admin предоставляет следующие необязательные зависимости:

- `pdf`: добавляет поддержку экспорта в PDF ([reportlab](https://www.reportlab.com/)).
- `i18n`: добавляет поддержку интернационализации ([Babel](https://babel.pocoo.org/)).
- `tinymce`: добавляет поддержку rich text editor. Устанавливает [nh3](https://nh3.readthedocs.io/), который очищает HTML, отправляемый через `TinyMCEEditorField`.
- `s3`: добавляет поддержку объектных хранилищ, совместимых с S3. Устанавливает [aiobotocore](https://aiobotocore.readthedocs.io/) для асинхронной загрузки в AWS S3 и совместимые сервисы объектных хранилищ, такие как MinIO.

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

Чтобы использовать новейшие ещё не выпущенные изменения, установите пакет напрямую из репозитория GitHub.

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

- **[Быстрый старт](quickstart.md)**: создайте свой первый административный интерфейс с реальными данными.
- **[Концепции](concepts.md)**: ознакомьтесь с основной архитектурой и принципами проектирования starlette-admin.
