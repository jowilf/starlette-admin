---
title: Интеграция с Beanie
description: Интегрируйте Beanie ODM со starlette-admin, чтобы создать расширяемый
  интерфейс администрирования для коллекций MongoDB в FastAPI.
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Интеграция с Beanie

Beanie представляет документы MongoDB в виде асинхронных моделей Pydantic. Модуль `starlette_admin.contrib.beanie` предоставляет специализированные классы `Admin` и `ModelView`, настроенные для непосредственной работы с этими документами.

**Ключевые возможности:**

- Встроенная поддержка операторов запросов MongoDB и фильтрации.
- Автоматическое преобразование ошибок валидации Pydantic в ошибки конкретных полей в формах интерфейса.
- Встроенная интеграция с полнотекстовым поиском MongoDB.

## Установка

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## Минимальный пример

Необходимо инициализировать Beanie до того, как любой запрос достигнет интерфейса администрирования. Лучший способ гарантировать выполнение этого условия — обернуть логику подключения в контекстный менеджер `lifespan` основного приложения.

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

`ModelView` принимает класс `Document` из Beanie напрямую. Он автоматически выводит список полей, формы и фильтры на основе полей документа.

## Основные классы

### Класс `beanie.Admin`

Класс `beanie.Admin` наследуется от `BaseAdmin` и не требует специфичной для базы данных конфигурации при инициализации. Настройка подключения полностью выполняется внутри `lifespan` приложения. Всегда импортируйте `Admin` из `starlette_admin.contrib.beanie`, чтобы обеспечить совместимость с будущими улучшениями, специфичными для бэкендов.

### Класс `beanie.ModelView`

Класс `beanie.ModelView` обеспечивает интеграционный слой между вашей базой данных и интерфейсом. Он автоматически выполняет несколько операций:

- **Заполнение полей:** автоматически генерирует поля из определения документа, если вы не задали их явно.
- **Фильтрация внутренних полей:** по умолчанию исключает внутреннее поле Beanie `revision_id` из списков и форм.
- **Разрешение связей:** выполняет чтение из базы данных с параметрами `fetch_links=True` и `nesting_depth=1`, благодаря чему ссылки `Link` разрешаются в связанные объекты, а не возвращаются как необработанные ссылки базы данных.
- **Обработка ошибок:** преобразует ошибки валидации Pydantic в ошибки конкретных полей формы, указывая пользователю прямо на некорректные данные.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## Поле `BeanieObjectIdField`

Beanie использует тип `PydanticObjectId` для первичных ключей. Панель администрирования автоматически отображает эти ключи, а также любые необработанные ссылки ObjectId, с помощью специального поля `BeanieObjectIdField`.

Хотя оно отрисовывается и валидируется точно так же, как стандартное поле `StringField`, оно имеет собственный слот в реестре фильтров. Такое разделение гарантирует, что фильтры, специфичные для ObjectId, применяются только к полям ObjectId, а не ко всем текстовым полям вашего приложения. Эти специализированные фильтры безопасно разбирают строки в объекты `PydanticObjectId` перед выполнением запроса к базе данных.

## Реестр фильтров {#filter-registry}

Каждый тип полей получает набор фильтров по умолчанию из `BeanieFilterRegistry`.

- **Сравнение строк:** фильтр равенства использует регулярные выражения без учёта регистра символов, чтобы сохранять согласованность с другими текстовыми поисками, такими как «Contains» или «Starts with».
- **Операции с массивами:** реестр предоставляет встроенную поддержку фильтрации по массивам, благодаря чему операции «Is one of» над полями со списочными значениями (например, `TagsField`) работают сразу после установки.
- **Первичные ключи:** поле `id` автоматически заменяется на нативное `_id` MongoDB при построении фрагментов запросов.

## Полнотекстовый поиск

Когда пользователь взаимодействует с полем поиска на странице списка, панель администрирования проверяет коллекцию MongoDB на наличие текстового индекса и соответствующим образом корректирует стратегию запроса:

- **Текстовый индекс присутствует:** запрос использует нативный оператор `$text` MongoDB. Это обеспечивает полноценный полнотекстовый поиск, включая токенизацию, стемминг и ранжирование по релевантности.
- **Текстового индекса нет:** система переключается на поиск с помощью регулярных выражений без учёта регистра по всем полям, помеченным как `searchable`. Такой подход не требует настройки, но не позволяет ранжировать результаты по релевантности и не может использовать стандартные индексы.

Панель администрирования обнаруживает существующие текстовые индексы, но не создаёт их. Чтобы включить нативный текстовый поиск, необходимо определить индекс в документе Beanie. Например, это можно сделать, добавив в модель `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]`.

!!! note
Если вы включите текстовый индекс, то можете установить `full_text_override_order_by = True` в подклассе `ModelView`, чтобы сортировать результаты поиска по оценке релевантности MongoDB вместо сортировки по столбцу по умолчанию.

## Полный рабочий пример

В этом разделе представлен полный запускаемый пример интеграции Beanie со `starlette-admin`.

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, что позволяет запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

Сохраните следующий код в файл с именем `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

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

Откройте в браузере страницу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть дашборд администрирования и поработать с ним.

> **Расширенный пример:** каталог [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) в репозитории содержит полнофункциональный пример, включающий инлайн-представления, события и пользовательские групповые действия.

## Что читать дальше

- **[Представления](../user-guide/views.md):** ознакомьтесь с параметрами конфигурации `BaseModelView`, независимыми от бэкенда.
- **[Фильтры](../user-guide/filters.md):** конструктор фильтров и подключение фильтров, специфичных для ORM.
- **[MongoEngine](mongoengine.md):** ещё один бэкенд MongoDB, встроенный в starlette-admin.
- **[SQLAlchemy](sqlalchemy.md):** реляционный бэкенд, встроенный в starlette-admin.
