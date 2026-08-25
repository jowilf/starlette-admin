---
title: Интеграция с SQLAlchemy
description: Узнайте, как интегрировать starlette-admin с SQLAlchemy. Создайте панель
  администрирования для моделей вашей реляционной базы данных в FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

Бэкенд для SQLAlchemy служит эталонной реализацией `BaseModelView`. Он тестировался только с моделями `DeclarativeBase` из SQLAlchemy 2. Остальные бэкенды (такие как Beanie, MongoEngine, Tortoise ORM или ваша собственная реализация) выполняют этот же контракт применительно к своим хранилищам данных.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


class ProductView(ModelView):
    fields = ["id", "name", "price"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

## Установка

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

Замените `aiosqlite` на `asyncpg` (PostgreSQL) или `aiomysql`/`asyncmy` (MySQL), если вы не хотите использовать SQLite. Драйвер базы данных имеет значение только для асинхронных движков. Синхронный движок использует стандартный DBAPI-драйвер, требуемый обычным SQLAlchemy (например, `psycopg2` или `pymysql`), и не требует дополнительных пакетов от `starlette-admin`.

## Асинхронные и синхронные движки

`Admin` принимает либо `Engine`, либо `AsyncEngine`. Передайте тот экземпляр, который вы уже настроили:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` проверяет движок один раз во время обработки запроса и открывает соответствующий тип сессии: `AsyncSession` для `AsyncEngine` или обычную `Session` для синхронного `Engine`. Внутри `ModelView` ветвление происходит по условию `isinstance(session, AsyncSession)`. Для синхронных сессий блокирующий вызов направляется через `anyio.to_thread.run_sync`, чтобы не блокировать event loop.

## Передача `sessionmaker` вместо движка

Параметр `session_provider` также принимает `sessionmaker` или `async_sessionmaker`. Используйте фабрику сессий вместо «голого» движка, когда вам необходимо настроить сессию напрямую.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
Мидлварь сессий вызывает `session_maker()` для создания новой сессии на каждый запрос вместо того, чтобы конструировать её самостоятельно.

## `sqla.Admin` и `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` принимает те же аргументы, что и `starlette_admin.BaseAdmin`, а также один обязательный позиционный аргумент: `session_provider`. Этот провайдер может быть экземпляром `Engine`, `AsyncEngine`, `sessionmaker` или `async_sessionmaker`. При инициализации панель администрирования настраивает мидлварь сессий, привязанную к выбранному провайдеру, и вставляет её в начало стека middleware. Этот механизм гарантирует, что `request.state.session` будет автоматически заполнен при каждом запросе до выполнения кода вашего представления.

`sqla.ModelView` требует модель SQLAlchemy. При инициализации он анализирует модель, чтобы автоматически определить поля, управлять первичными ключами и настроить реестр фильтров непосредственно на основе метаданных.

## Объявление моделей

Определяйте модели с помощью стандартных декларативных классов SQLAlchemy:

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

Если вы не задали `fields` у представления, `ModelView` использует все атрибуты, объявленные в модели, в порядке их следования. Первичный ключ определяется автоматически и исключается из форм создания и редактирования. Все остальные столбцы и связи автоматически преобразуются в соответствующие типы полей (например, `IntegerField`, `StringField`, `EnumField`, `HasOne` или `HasMany`).

## Автоматически определяемые значения по умолчанию

Конфигурация `default=` на стороне Python заполняется автоматически при первом открытии формы создания. Повторять это определение на самом поле не требуется:

```python
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    views: Mapped[int] = mapped_column(default=0)  # form shows 0
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )  # form shows now()
```

Скалярное значение по умолчанию (`default=0`) копируется точно так, как определено. Вызываемое значение по умолчанию (`default=datetime.utcnow` или `default=uuid.uuid4`) срабатывает один раз при отрисовке формы, что позволяет увидеть реальное значение вместо `repr`-представления функции.

!!! important
    Столбцы первичного ключа никогда не получают предзаполненное значение по умолчанию, даже если оно определено. Предполагается, что они генерируются на стороне сервера (через `autoincrement` или последовательность), и они полностью исключаются из форм создания и редактирования. Значения по умолчанию в виде SQL-выражений (например, `server_default=func.now()` или `DEFAULT` на стороне базы данных) также пропускаются, поскольку отсутствует значение уровня Python для отображения. База данных сама заполняет эти значения при вставке.

## Поля связей

`relationship()` в модели SQLAlchemy автоматически преобразуется в `HasOne` (связь «многие к одному» или «один к одному») или `HasMany` («один ко многим» или «многие ко многим») в зависимости от атрибута `RelationshipProperty.direction`. Явно объявлять тип поля не требуется:

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")
```

При задании `PostView.fields = ["id", "title", "author"]` поле `author` отображается как выпадающий список Select2. Этот список заполняется через AJAX из endpoint `/_api/{key}/relation-lookup` связанного представления (где `{key}` — это `author`, ключ `AuthorView`). Приложение никогда не загружает всю таблицу авторов на страницу целиком. Такое ленивое поведение критически важно для производительности, когда связанная таблица содержит тысячи строк. Аналогично, при задании `AuthorView.fields = ["id", "name", "posts"]` поле `posts` отображается как элемент множественного выбора, использующий тот же lookup-endpoint.

## Составные первичные ключи

Модели, использующие несколько столбцов с `primary_key=True` для составного первичного ключа, поддерживаются «из коробки» без какой-либо дополнительной конфигурации. Это касается и сценариев, где каждый столбец первичного ключа одновременно является внешним ключом, например объект ассоциации «многие ко многим».

Полностью рабочий пример см. в [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks).

## Реестр фильтров {#filter-registry}

Каждый тип поля получает набор фильтров по умолчанию из `SqlaFilterRegistry`. Они разрешаются путём обхода иерархии классов поля, как описано в документации [Фильтры](../user-guide/filters.md). Важная деталь, специфичная для SQLAlchemy, заключается в том, как каждый фильтр транслируется во фрагмент запроса. Каждый метод `apply()` в этом модуле возвращает самостоятельное булево выражение SQLAlchemy (например, `column == value` или `column.between(a, b)`).

!!! note
    Фильтр `Is null` для связи вычисляет `~column.has()` (для связей «многие к одному») или `~column.any()` (для связей «один ко многим» и «многие ко многим») вместо `column.is_(None)`. Поскольку атрибут связи не является обычным столбцом, содержащим значение `NULL`, его пустота полностью зависит от наличия связанных строк.

!!! note
    Бэкенд SQLAlchemy не предоставляет `ArrayInFilter` и `ArrayNotInFilter` (фильтры «is one of» для столбцов со списочными значениями), в отличие от Beanie и MongoEngine. Если вам нужна фильтрация «is one of» по JSON- или ARRAY-столбцу на основе `TagsField`, придётся написать собственную логику `apply()`. Подробнее см. документацию [Пользовательские фильтры](../advanced/custom-filters.md).

## Сессии и транзакции

Мидлварь сессий открывает ровно одну сессию на запрос и надёжно сохраняет её в `request.state.session`. Это будет `AsyncSession` при использовании асинхронного движка (или `async_sessionmaker`) и обычная `Session` в остальных случаях. Все компоненты, задействованные в обработке запроса, используют эту единственную сессию. Запрос списка, lookup-запросы связей внутри форм и любая пользовательская логика в hook, action или endpoint будут выполняться в рамках одной и той же транзакции. Получить её можно единообразно независимо от типа базового движка:

```python
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    @action(name="publish", text="Publish selected")
    async def publish(self, request: Request, pks: list[Any]) -> str:
        session: AsyncSession = request.state.session
        for post in await self.find_by_pks(request, pks):
            post.status = "PUBLISHED"
            session.add(post)
        await session.flush()
        return f"{len(pks)} post(s) published."
```

При использовании синхронного движка `request.state.session` возвращает обычную `Session`, а `session.flush()` вызывается без `await`. Всё остальное в приведённом фрагменте кода остаётся без изменений. Вам не нужно импортировать отдельную зависимость `get_session()`. Сессия привязывается к запросу до выполнения вашего hook или action, потому что мидлварь сессий устанавливает соединение перед вызовом обработчика маршрута.

**Один commit на запрос.** Никогда не вызывайте `session.commit()` вручную. Достаточно вызвать `flush()` (или вообще ничего не делать при выполнении запросов только на чтение). Мидлварь сессий фиксирует сессию ровно один раз после возврата из обработчика маршрута, при условии что ответ указывает на успех. При возникновении ошибки мидлварь автоматически откатывает всю транзакцию:

* Если обработчик выбрасывает исключение, сессия откатывается, а приложение повторно возбуждает это исключение.
* Если обработчик возвращает ответ с `status_code >= 400` (например, при ошибке валидации формы), сессия откатывается, а сервер возвращает ответ без изменений. Этот откат крайне важен, поскольку транзакция на этом этапе может содержать неудачный flush. Его фиксация могла бы случайно сохранить частично записанные данные.
* Если сама операция commit выбрасывает исключение (например, нарушение ограничения базы данных, обнаруженное при flush), сессия откатывается, а исключение возбуждается повторно.

Во всех остальных случаях, когда обработчик возвращает ответ 2xx или 3xx, мидлварь фиксирует сессию и освобождает соединение. Именно этот жизненный цикл объясняет, почему действие `publish`, показанное выше, не требует явных вызовов commit или close. Мидлварь сессий открывает сессию до выполнения вашего кода и впоследствии обрабатывает commit или rollback до того, как ответ покинет представление.

## Валидация Pydantic {#pydantic-validation}

Вы можете использовать обычные модели SQLAlchemy, но при этом хотеть валидировать данные формы по схеме Pydantic перед сохранением. В таком случае `starlette_admin.contrib.sqla.ext.pydantic.ModelView` принимает аргумент `pydantic_model`, чтобы выполнять валидацию по этой схеме, а не по типам столбцов SQLAlchemy:

```python
from sqlalchemy import ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///users.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip().split()) < 2:
            raise ValueError("Must include both first and last name (e.g. John Doe)")
        return v


admin = Admin(engine, title="Users Admin", secret_key="change-me")
admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

Отправка `full_name="Madonna"` (одно слово) приведёт к срабатыванию метода `validate_full_name`. После этого форма создания или редактирования будет отрисована заново с ошибкой, явно привязанной к полю `full_name`. У лежащего в основе столбца SQLAlchemy `String(100)` такого правила нет. Ограничение целиком resides в модели `UserIn` на Pydantic. Полный пример, включающий также вторичное представление (`PostIn`), подключённое к той же панели администрирования, см. в [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi).

## Полный рабочий пример


Вот полный пример использования SQLAlchemy со starlette-admin. Запускаемую версию см. в [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, позволяющий запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

Сохраните следующий код в файл `main.py`. Для наглядности этот скрипт использует локальную базу данных SQLite (`blog.db`), хотя Starlette-Admin поддерживает как синхронные, так и асинхронные движки для PostgreSQL, MySQL и SQLite.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import SlugField
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")


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
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
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

Теперь вы можете перейти по адресу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) в браузере, чтобы просмотреть панель администрирования и поработать с ней.

---

## Что читать дальше

* **[Представления](../user-guide/views.md)**: Изучите параметры конфигурации `BaseModelView`, независимые от бэкенда.
* [Фильтры](../user-guide/filters.md): Подробности о конструкторе фильтров и формате URL, работающем на основе реестра фильтров.
* [Представления](../user-guide/views.md): Полный перечень всех параметров конфигурации `ModelView` (не зависящих от бэкенда).
* [SQLModel](sqlmodel.md): Тонкая обёртка над этим бэкендом, добавляющая валидацию Pydantic к формам.
* [Beanie](beanie.md): Руководство по использованию того же API `ModelView` с базой данных MongoDB.
* [Tortoise ORM](tortoise.md): Другой реляционный бэкенд, встроенный в starlette-admin.
