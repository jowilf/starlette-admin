---
title: Интеграция с Tortoise ORM
description: Легко создавайте интерфейс администрирования для моделей Tortoise ORM
  в FastAPI с помощью starlette-admin.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Интеграция с Tortoise ORM

Tortoise ORM — это нативный для asyncio объектно-реляционный преобразователь, вдохновлённый Django. Модуль `starlette_admin.contrib.tortoise` предоставляет специализированные классы `Admin`, `ModelView` и `InlineModelView`, которые заранее настроены для прямой интеграции с вашими моделями Tortoise.

**Ключевые возможности:**

* **Автоматическое преобразование полей:** поля моделей Tortoise напрямую сопоставляются с компонентами интерфейса. Это включает полную поддержку перечислений, JSON, дат и автоматических меток времени.
* **Сопоставление связей:** связи «один к одному» и внешние ключи преобразуются в поля `HasOne`, а связи «многие ко многим» — в поля `HasMany`. Обратные связи автоматически отображаются как доступные только для чтения.
* **Расширенная фильтрация:** конструктор фильтров использует выражения `Q` из Tortoise, а также поддерживает поиск по строковым полям без учёта регистра.
* **Преобразование ошибок:** ошибки валидации Tortoise напрямую сопоставляются с ошибками конкретных полей формы в интерфейсе.

## Установка

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Минимальный пример

Tortoise подключается к базе данных внутри контекстного менеджера `lifespan` вашего приложения. Поскольку представления администрирования обычно создаются во время импорта (до выполнения `Tortoise.init()`), необходимо разрешить связи заранее.

Вызовите `Tortoise.init_models()` сразу после определения моделей, чтобы связи были доступны при построении представлений администрирования.

```python
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from tortoise import Tortoise, fields
from tortoise.models import Model
from starlette_admin.contrib.tortoise import Admin, ModelView


class Genre(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)


# Разрешите связи на этапе импорта до построения представлений.
Tortoise.init_models(["app"], "models")


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(
        db_url="sqlite://library.sqlite3", modules={"models": ["app"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

`ModelView` принимает класс модели Tortoise (`Model`) напрямую и автоматически формирует список полей, формы и фильтры на основе схемы модели.

## Основные классы

### `tortoise.Admin`

Класс `tortoise.Admin` наследуется от `BaseAdmin` и не требует специфичной для базы данных конфигурации при инициализации. Настройка подключения полностью выполняется внутри `lifespan` приложения. Всегда импортируйте `Admin` из `starlette_admin.contrib.tortoise`, чтобы обеспечить совместимость с будущими улучшениями, специфичными для бэкендов.

### `tortoise.ModelView`

Класс `tortoise.ModelView` обеспечивает уровень интеграции между вашей базой данных и пользовательским интерфейсом. Он автоматически выполняет следующие операции:

* **Заполнение полей:** если вы явно не указали поля, они генерируются из определения модели. По умолчанию исключаются исходные ключевые столбцы, лежащие в основе связей «к одному» (например, `author_id` для связи с именем `author`), а также обратные связи.
* **Разрешение связей:** все связи, отображаемые представлением, загружаются заранее. Благодаря этому страницы списка и деталей никогда не вызывают ленивую загрузку.
* **Автоматические метки времени:** столбцы с `DatetimeField(auto_now=...)` или `DatetimeField(auto_now_add=...)` отображаются как доступные только для чтения и никогда не помечаются как обязательные.
* **Обработка ошибок:** ошибки валидации Tortoise (`"<field>: <detail>"`) преобразуются в ошибки конкретных полей формы, которые указывают пользователю прямо на некорректное значение.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Инлайн-представления позволяют редактировать связанные строки прямо в родительской форме. Внешний ключ определяется автоматически, если дочерняя модель имеет ровно одну связь, указывающую на родительскую модель. Если связей несколько, необходимо явно задать `fk_attr`, указав либо имя связи, либо её исходный ключевой столбец.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Работа со связями

Интеграция сопоставляет связи базы данных с полями администрирования в зависимости от типа поля. Для каждой связанной модели необходимо зарегистрировать `ModelView`, чтобы поля связей могли успешно найти соответствующие представления.

| Тип связи | Конфигурация Tortoise | Поведение в панели администрирования |
| --- | --- | --- |
| **Прямая (к одному)** | `ForeignKeyField`, `OneToOneField` | Преобразуется в `HasOne`. |
| **Прямая (ко многим)** | `ManyToManyField` | Преобразуется в `HasMany`. |
| **Обратная** | свойства `related_name` | Отображается только для чтения. Чтобы показать её, добавьте её в `fields` явно. |

**Фильтрация и сортировка по связям:**
Для связей «к одному» доступны фильтры «Is null» и «Is not null», работающие с исходным ключевым столбцом. Чтобы сделать связь доступной в конструкторе фильтров, добавьте имя связи в `searchable_fields`. Чтобы включить сортировку по исходному ключевому столбцу, добавьте имя связи в `sortable_fields`.

## Поиск и фильтрация

### Реестр фильтров {#filter-registry}

Каждый тип поля получает набор фильтров по умолчанию из `TortoiseFilterRegistry`, реализованный с помощью выражений `Q` из Tortoise:

* **Поиск по строкам:** фильтры «содержит», «начинается/заканчивается на» и «равно» используют поиск без учёта регистра (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Перечисления:** исходные значения фильтров приводятся обратно к членам перечисления перед выполнением запроса как для столбцов `CharEnumField`, так и для `IntEnumField`.
* **Столбцы времени:** столбцы `TimeField` поддерживают только проверки на пустое значение. Это ограничение существует потому, что параметры типа «время» невозможно переносимо привязать во всех бэкендах баз данных.

### Полнотекстовый поиск

Поле поиска на странице списка выполняет проверку `contains` без учёта регистра (выражения `Q`, объединённые через `OR`) по всем доступным для поиска строковым полям. Вы можете изменить это поведение, переопределив метод `get_search_query()` в своём представлении.

## Полный рабочий пример

В этом разделе приведён полный запускаемый пример интеграции Tortoise ORM с `starlette-admin`.

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, что позволяет запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

Сохраните следующий код в файл с именем `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from starlette_admin import SlugField
from starlette_admin.contrib.tortoise import Admin, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

DB_URL = "sqlite://blog.sqlite3"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __admin_repr__(self, request) -> str:
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts")

    def __admin_repr__(self, request) -> str:
        return self.title


# Разрешите связи на этапе импорта до построения представлений.
Tortoise.init_models(["main"], "models")


class AuthorView(ModelView):
    fields = ["id", "name"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["main"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Поскольку `created_at` использует `auto_now_add`, панель администрирования автоматически отображает его как доступное только для чтения. Настраивать `exclude_fields_from_create` или `exclude_fields_from_edit` не требуется.

### 3. Запустите сервер

Запустите сервер разработки FastAPI:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Откройте в браузере страницу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть дашборд и поработать с ним.

> **Расширенный пример:** каталог [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) в репозитории содержит полнофункциональный пример со связями, инлайн-представлениями, перечислениями и JSON-полями на базе SQLite.

## Что читать дальше

* **[Представления](../user-guide/views.md):** изучите параметры конфигурации `BaseModelView`, независимые от бэкенда.
* **[Фильтры](../user-guide/filters.md):** узнайте о конструкторе фильтров и о том, как подключаются фильтры, специфичные для ORM.
* **[SQLAlchemy](sqlalchemy.md):** документация по другому реляционному бэкенду, встроенному в starlette-admin.
