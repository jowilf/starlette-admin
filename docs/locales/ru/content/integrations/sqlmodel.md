---
title: Интеграция с SQLModel
description: Создайте полноценный дашборд администрирования для приложений FastAPI
  на SQLModel с помощью starlette-admin.
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# Интеграция с SQLModel

[SQLModel](https://sqlmodel.tiangolo.com/) объединяет таблицы SQLAlchemy и валидацию Pydantic в одном классе модели. Поскольку модели SQLModel под капотом являются моделями SQLAlchemy, модуль `starlette_admin.contrib.sqlmodel` представляет собой тонкую обёртку над существующим [бэкендом SQLAlchemy](sqlalchemy.md).

Эта интеграция не реализует отдельную систему, а наследует все возможности — автоматическое определение полей, управление первичными ключами, обработку связей, фильтрацию и session middleware — напрямую от основного бэкенда SQLAlchemy. Она добавляет надёжный слой валидации: перед любой записью в базу данных отправленные данные формы проходят через нативные валидаторы Pydantic вашей модели (например, `Field(min_length=...)` или пользовательские методы `@field_validator`). Все возникающие исключения `ValidationError` автоматически преобразуются в ошибки по отдельным полям формы в интерфейсе.

!!! note
    Всё, что описано на [странице SQLAlchemy](sqlalchemy.md), применимо без изменений. Это касается синхронных и асинхронных движков, провайдеров `sessionmaker`, жизненного цикла сессии с одним коммитом на запрос, полей со связями и реестра фильтров.

## Установка

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## Минимальный пример

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

Класс `ModelView` принимает класс таблицы SQLModel напрямую и автоматически выводит список полей, формы и фильтры из схемы модели.

## Основные классы

### `sqlmodel.Admin`

Класс `sqlmodel.Admin` — это переэкспортированный класс `sqla.Admin`. Он использует тот же конструктор, принимающий обязательный аргумент `session_provider`: `Engine`, `AsyncEngine`, `sessionmaker` или `async_sessionmaker`. Он также вставляет то же самое session middleware, которое заполняет `request.state.session` при каждом запросе.

### `sqlmodel.ModelView`

Класс `sqlmodel.ModelView` наследует всё от `sqla.ModelView` и добавляет слой валидации. Его метод `validate()` вызывает `self.model.model_validate(data)` перед записью записи, благодаря чему отправленные формы проверяются валидаторами Pydantic модели, а не только ограничениями столбцов SQLAlchemy. Поля файлов и поля со связями намеренно исключены из этого вызова валидации, поскольку они выходят за пределы поверхности валидации Pydantic модели.

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

Инлайн-представления позволяют редактировать связанные строки прямо внутри родительской формы. Класс наследует определение внешних ключей и обработку сессий от класса SQLAlchemy `InlineModelView` и применяет ту же валидацию Pydantic к каждой инлайн-строке.

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Валидация Pydantic

Ограничения, объявленные в модели, автоматически применяются к формам создания и редактирования:

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

Значение `full_name` короче двух символов или некорректный адрес электронной почты не пройдут валидацию. В этом случае форма вернётся с ошибками по соответствующим полям ещё до того, как какая-либо операция `INSERT` или `UPDATE` достигнет базы данных.

!!! note
    Тип `EmailStr` требует пакет `email-validator`, который устанавливается командой `pip install "pydantic[email]"`.

## Полный рабочий пример

В этом разделе приведён полный запускаемый пример интеграции SQLModel с `starlette-admin`.

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, позволяющий запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

Сохраните следующий код в файл с именем `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts"]


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
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Если вы отправите форму со значением `title` короче трёх символов или значением `name` короче двух символов, форма отобразится повторно с ошибкой, привязанной к соответствующему полю.

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

Откройте в браузере страницу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы увидеть дашборд администрирования и поработать с ним.

> **Расширенный пример:** каталог [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) в репозитории содержит полнофункциональный пример CMS со связями, инлайн-представлениями, действиями, фильтрами, событиями и экспортом.

## Что читать дальше

* **[SQLAlchemy](sqlalchemy.md):** бэкенд, на котором построена эта интеграция; охватывает движки, сессии, транзакции и реестр фильтров.
* **[Представления](../user-guide/views.md):** изучите параметры конфигурации `BaseModelView`, независимые от бэкенда.
* **[Фильтры](../user-guide/filters.md):** узнайте о конструкторе фильтров и о том, как подключаются специфичные для ORM фильтры.
