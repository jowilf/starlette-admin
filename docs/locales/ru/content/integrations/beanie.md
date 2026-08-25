---
title: Интеграция с Beanie
description: Интегрируйте Beanie ODM со starlette-admin, чтобы создать расширяемый
  административный интерфейс для ваших коллекций MongoDB в FastAPI.
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Интеграция с Beanie

Beanie представляет документы MongoDB в виде асинхронных моделей Pydantic. Модуль `starlette_admin.contrib.beanie` предоставляет специализированные классы `Admin` и `ModelView`, настроенные на прямое взаимодействие с этими документами.

**Ключевые возможности:**

- Нативная поддержка операторов запросов и фильтрации MongoDB.
- Автоматическое преобразование ошибок валидации Pydantic в ошибки форм, привязанные к конкретным полям.
- Встроенная интеграция полнотекстового поиска MongoDB.

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

Необходимо инициализировать Beanie до того, как любой запрос достигнет административного интерфейса. Лучший способ гарантировать выполнение этого условия — обернуть логику подключения в контекстный менеджер `lifespan` вашего основного приложения.

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

`ModelView` принимает класс Beanie `Document` напрямую. Он автоматически выводит список полей, формы и фильтры из полей документа.

## Основные классы

### Класс `beanie.Admin`

Класс `beanie.Admin` наследуется от `BaseAdmin` и не требует конфигурации, специфичной для базы данных, при инициализации. Настройка подключения полностью выполняется внутри lifespan приложения. Всегда импортируйте `Admin` из `starlette_admin.contrib.beanie`, чтобы обеспечить совместимость с будущими улучшениями, специфичными для backend.

### Класс `beanie.ModelView`

Класс `beanie.ModelView` обеспечивает интеграционный слой между вашей базой данных и интерфейсом. Он автоматически выполняет ряд операций:

- **Заполнение полей:** автоматически генерирует поля из определения документа, если вы явно их не указали.
- **Фильтрация внутренних полей:** по умолчанию исключает внутреннее поле Beanie `revision_id` из списков и форм.
- **Разрешение связей:** выполняет чтение из базы данных с параметрами `fetch_links=True` и `nesting_depth=1`, благодаря чему ссылки `Link` разрешаются в связанные объекты, а не возвращаются как сырые ссылки на записи в базе данных.
- **Обработка ошибок:** преобразует ошибки валидации Pydantic в ошибки форм, привязанные к конкретным полям, указывая пользователю непосредственно на некорректные данные.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## Поле `BeanieObjectIdField`

Beanie использует тип `PydanticObjectId` для первичных ключей. Административная панель автоматически отображает эти ключи, а также любые сырые ссылки ObjectId, с помощью специализированного поля `BeanieObjectIdField`.

Хотя оно отображается и валидируется точно так же, как стандартное `StringField`, оно имеет собственный слот в реестре фильтров. Такое разделение гарантирует, что специфичные для ObjectId фильтры применяются только к полям ObjectId, а не ко всем стандартным текстовым полям вашего приложения. Эти специализированные фильтры безопасно преобразуют строки в корректные объекты `PydanticObjectId` перед выполнением запроса к базе данных.

## Реестр фильтров {#filter-registry}

Каждый тип поля получает набор фильтров по умолчанию из `BeanieFilterRegistry`.

- **Сравнение строк:** фильтр равенства использует регулярные выражения без учёта регистра символов для согласованности с другими текстовыми поисками, такими как «Contains» или «Starts with».
- **Операции с массивами:** реестр предоставляет встроенную поддержку фильтрации по массивам, благодаря чему операции «Is one of» над полями со списочными значениями (например, `TagsField`) работают сразу после установки.
- **Первичные ключи:** поле `id` автоматически преобразуется в нативное `_id` MongoDB при построении фрагментов запросов.

## Полнотекстовый поиск

Когда пользователь взаимодействует с полем поиска на странице списка, административная панель проверяет наличие текстового индекса в коллекции MongoDB и соответствующим образом корректирует стратегию запроса:

- **Текстовый индекс присутствует:** запрос использует нативный оператор `$text` MongoDB. Это обеспечивает полноценный полнотекстовый поиск, включая токенизацию, стемминг и ранжирование по релевантности.
- **Текстовый индекс отсутствует:** система переключается на поиск с помощью регулярных выражений без учёта регистра по всем полям, помеченным как `searchable`. Хотя такой подход не требует настройки, он не может ранжировать результаты по релевантности и не может использовать стандартные индексы.

Административная панель обнаруживает существующие текстовые индексы, но не создаёт их. Вы должны определить индекс в документе Beanie, чтобы включить нативный текстовый поиск. Например, этого можно добиться, добавив в модель `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]`.

!!! note
Если вы включите текстовый индекс, то можете установить `full_text_override_order_by = True` в подклассе `ModelView`, чтобы сортировать результаты поиска по показателю релевантности MongoDB вместо сортировки по столбцу по умолчанию.

## Полный рабочий пример

В этом разделе представлен полный, готовый к запуску пример интеграции Beanie со `starlette-admin`.

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

Перейдите в браузере по адресу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть административную панель и работать с ней.

> **Расширенный пример:** каталог [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) в репозитории содержит полнофункциональный пример, включающий inline views, события и пользовательские пакетные действия.

## Что читать дальше

- **[Views](../user-guide/views.md)**: ознакомьтесь с параметрами конфигурации `BaseModelView`, независимыми от используемого backend.
- **[Filters](../user-guide/filters.md):** конструктор фильтров и подключение фильтров, специфичных для ORM.
- **[MongoEngine](mongoengine.md):** ещё один backend для MongoDB, встроенный в starlette-admin.
- **[SQLAlchemy](sqlalchemy.md):** реляционный backend, встроенный в starlette-admin.
