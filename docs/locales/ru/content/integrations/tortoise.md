---
title: Интеграция с Tortoise ORM
description: Легко создавайте административный интерфейс для ваших моделей Tortoise
  ORM в FastAPI с помощью starlette-admin.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Интеграция с Tortoise ORM

Tortoise ORM — это нативный для asyncio объектно-реляционный преобразователь, вдохновлённый Django. Модуль `starlette_admin.contrib.tortoise` предоставляет специализированные классы `Admin`, `ModelView` и `InlineModelView`, которые предварительно настроены для прямой интеграции с вашими моделями Tortoise.

**Ключевые возможности:**

* **Автоматическое преобразование полей:** Поля моделей Tortoise напрямую сопоставляются с UI-компонентами. Это включает полную поддержку enum-ов, JSON, дат и автоматических меток времени.
* **Сопоставление связей:** Связи «один к одному» и внешние ключи преобразуются в поля `HasOne`, а связи «многие ко многим» — в поля `HasMany`. Обратные связи автоматически отображаются в режиме только для чтения.
* **Расширенная фильтрация:** В конструкторе фильтров используются выражения `Q` из Tortoise, а также доступен нечувствительный к регистру полнотекстовый поиск по строковым полям.
* **Преобразование ошибок:** Ошибки валидации Tortoise напрямую сопоставляются с ошибками конкретных полей формы в интерфейсе.

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

Tortoise подключается к базе данных внутри контекстного менеджера `lifespan` вашего приложения. Поскольку admin-представления обычно создаются на этапе импорта (до выполнения `Tortoise.init()`), необходимо заранее разрешить связи.

Вызывайте `Tortoise.init_models()` сразу после определения моделей, чтобы связи были доступны к моменту построения admin-представлений.

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


# Разрешение связей на этапе импорта до построения admin-представлений.
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

`ModelView` принимает класс модели Tortoise `Model` напрямую и автоматически формирует список полей, формы и фильтры на основе схемы модели.

## Основные классы

### `tortoise.Admin`

Класс `tortoise.Admin` наследуется от `BaseAdmin` и не требует специфичной для базы данных конфигурации при инициализации. Настройка подключения полностью выполняется внутри `lifespan` приложения. Всегда импортируйте `Admin` из `starlette_admin.contrib.tortoise`, чтобы обеспечить совместимость с будущими улучшениями, специфичными для этого backend-а.

### `tortoise.ModelView`

Класс `tortoise.ModelView` обеспечивает уровень интеграции между вашей базой данных и пользовательским интерфейсом. Он автоматически выполняет следующие операции:

* **Заполнение полей:** Если вы явно не указали поля, они генерируются из определения модели. Необработанные ключевые столбцы, лежащие в основе связей «к одному» (например, `author_id` для связи с именем `author`), а также обратные связи по умолчанию исключаются.
* **Разрешение связей:** Все связи, отображаемые представлением, загружаются упреждающе. Это гарантирует, что списки и страницы деталей никогда не вызывают ленивую загрузку.
* **Автоматические метки времени:** Столбцы с `DatetimeField(auto_now=...)` или `DatetimeField(auto_now_add=...)` отображаются в режиме только для чтения и никогда не помечаются как обязательные.
* **Обработка ошибок:** Ошибки валидации Tortoise (`"<field>: <detail>"`) преобразуются в ошибки конкретных полей формы, которые указывают пользователю прямо на некорректное значение.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Встроенные представления позволяют редактировать связанные строки внутри родительской формы. Внешний ключ определяется автоматически, если дочерняя модель имеет ровно одну связь, указывающую на родительскую модель. Если связей несколько, необходимо явно задать `fk_attr`, указав либо имя связи, либо её необработанный ключевой столбец.

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

Интеграция сопоставляет связи базы данных с полями admin-интерфейса в зависимости от типа поля. Для каждой связанной модели необходимо зарегистрировать `ModelView`, чтобы поля связей могли успешно разрешить свои внешние представления.

| Тип связи | Конфигурация Tortoise | Поведение в admin |
| --- | --- | --- |
| **Прямая (To-One)** | `ForeignKeyField`, `OneToOneField` | Преобразуется в `HasOne`. |
| **Прямая (To-Many)** | `ManyToManyField` | Преобразуется в `HasMany`. |
| **Обратная** | свойства `related_name` | Отображается в режиме только для чтения. Чтобы показать её, нужно явно добавить её в `fields`. |

**Фильтрация и сортировка по связям:**
Для связей «к одному» доступны фильтры «Is null» и «Is not null», работающие с необработанным ключевым столбцом. Чтобы сделать связь доступной в конструкторе фильтров, добавьте имя связи в `searchable_fields`. Чтобы включить сортировку по необработанному ключевому столбцу, добавьте имя связи в `sortable_fields`.

## Поиск и фильтрация

### Реестр фильтров {#filter-registry}

Каждый тип поля получает набор фильтров по умолчанию из `TortoiseFilterRegistry`, реализованный с помощью выражений `Q` из Tortoise:

* **Сопоставление строк:** Фильтры «содержит», «начинается/заканчивается на» и равенство используют поиск без учёта регистра (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enum-ы:** Необработанные значения фильтров приводятся обратно к членам enum перед выполнением запроса как для столбцов `CharEnumField`, так и для `IntEnumField`.
* **Столбцы времени:** Столбцы `TimeField` поддерживают только проверки на null. Это ограничение существует потому, что параметры типа time невозможно переносимо привязать во всех поддерживаемых базах данных.

### Полнотекстовый поиск

Поле поиска на странице списка выполняет нечувствительное к регистру сравнение `contains` (выражения `Q`, объединённые через `OR`) по всем доступным для поиска строковым полям. Это поведение можно настроить, переопределив метод `get_search_query()` в вашем представлении.

## Полный рабочий пример

В этом разделе представлен полный, готовый к запуску пример интеграции Tortoise ORM с `starlette-admin`.

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


# Разрешение связей на этапе импорта до построения admin-представлений.
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

Поскольку `created_at` использует `auto_now_add`, admin автоматически отображает это поле в режиме только для чтения. Настраивать `exclude_fields_from_create` или `exclude_fields_from_edit` не требуется.

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

Перейдите в браузере по адресу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы открыть панель администрирования и работать с ней.

> **Расширенный пример:** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) в репозитории содержит полнофункциональный пример, включающий связи, встроенные представления, enum-ы и JSON-поля на базе SQLite.

## Что читать дальше

* **[Представления](../user-guide/views.md):** Изучите параметры конфигурации `BaseModelView`, независимые от используемого backend-а.
* **[Фильтры](../user-guide/filters.md):** Узнайте о конструкторе фильтров и о том, как подключаются специфичные для ORM фильтры.
* **[SQLAlchemy](sqlalchemy.md):** Документация по другому реляционному backend-у, встроенному в starlette-admin.
