---
title: Интеграция с SQLAlchemy
description: Узнайте, как интегрировать starlette-admin с SQLAlchemy. Создайте дашборд
  администрирования для моделей вашей реляционной базы данных в FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

Бэкенд SQLAlchemy служит эталонной реализацией `BaseModelView`. Он тестировался только с моделями на основе `DeclarativeBase` из SQLAlchemy 2. Остальные бэкенды (такие как Beanie, MongoEngine, Tortoise ORM или ваша собственная реализация) выполняют тот же контракт применительно к своим хранилищам данных.

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

Если вы не хотите использовать SQLite, замените `aiosqlite` на `asyncpg` (PostgreSQL) или `aiomysql`/`asyncmy` (MySQL). Драйвер базы данных имеет значение только для асинхронных движков. Синхронный движок использует стандартный DBAPI-драйвер, требуемый обычным SQLAlchemy (например, `psycopg2` или `pymysql`), и не требует дополнительных пакетов от `starlette-admin`.

## Асинхронные и синхронные движки

`Admin` принимает либо `Engine`, либо `AsyncEngine`. Передайте тот экземпляр, который вы уже настроили:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` проверяет движок один раз при обработке запроса и открывает соответствующий тип сессии: `AsyncSession` для `AsyncEngine` или обычную `Session` для синхронного `Engine`. Внутри `ModelView` выполняет ветвление по условию `isinstance(session, AsyncSession)`. Для синхронных сессий блокирующий вызов направляется через `anyio.to_thread.run_sync`, чтобы не блокировать цикл событий.

## Передача `sessionmaker` вместо движка

Параметр `session_provider` также принимает `sessionmaker` или `async_sessionmaker`. Используйте фабрику сессий вместо «голого» движка, когда необходимо настроить сессию напрямую.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
Middleware сессии вызывает `session_maker()`, чтобы создавать новую сессию для каждого запроса, вместо того чтобы конструировать её самостоятельно.

## `sqla.Admin` и `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` принимает те же аргументы, что и `starlette_admin.BaseAdmin`, плюс один обязательный позиционный аргумент: `session_provider`. Этот провайдер может быть `Engine`, `AsyncEngine`, `sessionmaker` или `async_sessionmaker`. При инициализации панель администрирования настраивает middleware сессии, привязанное к выбранному провайдеру, и вставляет его в начало стека middleware. Этот механизм гарантирует, что `request.state.session` будет автоматически заполнен при каждом запросе ещё до выполнения кода вашего представления.

`sqla.ModelView` требует модель SQLAlchemy. При инициализации он анализирует модель, чтобы автоматически определить поля, управлять первичными ключами и настроить реестр фильтров непосредственно по метаданным.

## Объявление модели

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

Если вы не зададите `fields` у представления, `ModelView` использует все атрибуты, объявленные в модели, в порядке их следования. Первичный ключ определяется автоматически и исключается из форм создания и редактирования. Все остальные столбцы и связи автоматически преобразуются в соответствующие типы полей (например, `IntegerField`, `StringField`, `EnumField`, `HasOne` или `HasMany`).

## Автоматически определяемые значения по умолчанию

Значение, заданное через `default=` на стороне Python, подставляется автоматически при первом открытии формы создания. Повторять это определение в самом поле не требуется:

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

Скалярное значение по умолчанию (`default=0`) копируется точно так, как определено. Вызываемое значение (`default=datetime.utcnow` или `default=uuid.uuid4`) вычисляется один раз при отрисовке формы, поэтому пользователь видит реальное значение, а не `repr` функции.

!!! important
    Столбцы первичного ключа никогда не получают предзаполненное значение по умолчанию, даже если оно определено. Предполагается, что они генерируются на стороне сервера (через `autoincrement` или последовательность), и они полностью исключаются из форм создания и редактирования. Значения по умолчанию в виде SQL-выражений (например, `server_default=func.now()` или `DEFAULT` на стороне базы данных) также пропускаются, поскольку на уровне Python нет значения для отображения. База данных сама заполняет эти значения при вставке.

## Поля связей

`relationship()` в модели SQLAlchemy автоматически преобразуется в `HasOne` (связь «многие к одному» или «один к одному») либо в `HasMany` («один ко многим» или «многие ко многим») в зависимости от атрибута `RelationshipProperty.direction`. Явно указывать тип поля не нужно:

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

При значении `PostView.fields = ["id", "title", "author"]` поле `author` отображается как выпадающий список Select2. Этот список заполняется через AJAX из эндпоинта `/_api/{key}/relation-lookup` связанного представления (где `{key}` — это `author`, ключ `AuthorView`). Приложение никогда не загружает всю таблицу авторов на страницу целиком. Такое ленивое поведение критически важно для производительности, когда связанная таблица содержит тысячи строк. Аналогично, при значении `AuthorView.fields = ["id", "name", "posts"]` поле `posts` отображается как элемент множественного выбора, использующий тот же эндпоинт поиска.

## Составные первичные ключи

Модели с несколькими столбцами `primary_key=True`, образующими составной первичный ключ, поддерживаются «из коробки» без какой-либо дополнительной настройки. Это касается и сценариев, где каждый столбец первичного ключа одновременно является внешним ключом, например объект ассоциации для связи «многие ко многим».

Полностью работающий пример см. в [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks).

## Реестр фильтров {#filter-registry}

Каждый тип поля получает набор фильтров по умолчанию из `SqlaFilterRegistry`. Они разрешаются путём обхода иерархии классов поля, как описано в документации [Фильтры](../user-guide/filters.md). Важная деталь, специфичная для SQLAlchemy, — то, как каждый фильтр преобразуется во фрагмент запроса. Каждый метод `apply()` в этом модуле возвращает самостоятельное логическое выражение SQLAlchemy (например, `column == value` или `column.between(a, b)`).

!!! note
    Фильтр `Is null` для связи вычисляет `~column.has()` (для связей «многие к одному») или `~column.any()` (для связей «один ко многим» и «многие ко многим») вместо `column.is_(None)`. Атрибут связи — это не обычный столбец, содержащий значение `NULL`, поэтому его «пустота» полностью зависит от наличия связанных строк.

!!! note
    В отличие от Beanie и MongoEngine, бэкенд SQLAlchemy не предоставляет `ArrayInFilter` и `ArrayNotInFilter` (фильтры «is one of» для столбцов со списочными значениями). Если вам нужна фильтрация «is one of» по JSON- или ARRAY-столбцу на основе `TagsField`, напишите собственную логику `apply()`. Подробнее см. документацию [Пользовательские фильтры](../advanced/custom-filters.md).

## Сессии и транзакции

Middleware сессии открывает ровно одну сессию на запрос и надёжно сохраняет её в `request.state.session`. Это будет `AsyncSession` при использовании асинхронного движка (или `async_sessionmaker`) и обычная `Session` в остальных случаях. Все компоненты, затронутые запросом, используют эту единственную сессию. Запрос списка, поиск связей внутри форм и любая пользовательская логика в хуке, действии или эндпоинте работают в рамках одной и той же транзакции. Получить сессию можно единообразно независимо от типа движка:

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

При использовании синхронного движка `request.state.session` возвращает обычную `Session`, а `session.flush()` вызывается без `await`. Остальной код примера остаётся без изменений. Импортировать отдельную зависимость `get_session()` не требуется. Сессия привязывается к запросу до выполнения вашего хука или действия, потому что middleware сессии устанавливает соединение до вызова обработчика маршрута.

**Один коммит на запрос.** Никогда не вызывайте `session.commit()` вручную. Достаточно вызвать `flush()` (или вообще ничего не делать при запросах только для чтения). Middleware сессии выполняет коммит ровно один раз после возврата из обработчика маршрута, если ответ указывает на успех. При возникновении ошибки middleware автоматически откатывает всю транзакцию:

* Если обработчик выбрасывает исключение, сессия откатывается, а приложение повторно возбуждает исключение.
* Если обработчик возвращает ответ с `status_code >= 400` (например, при ошибке валидации формы), сессия откатывается, а сервер возвращает ответ без изменений. Этот откат крайне важен, потому что к этому моменту транзакция может содержать неудачный flush — его коммит мог бы случайно сохранить частично записанную запись.
* Если сам коммит выбрасывает исключение (например, нарушение ограничения базы данных, обнаруженное при flush), сессия откатывается, а исключение возбуждается повторно.

Во всех остальных случаях, когда обработчик возвращает ответ 2xx или 3xx, middleware выполняет коммит сессии и освобождает соединение. Именно этот жизненный цикл объясняет, почему действие `publish` из примера выше не требует явных вызовов commit или close. Middleware сессии открывает сессию до выполнения вашего кода, а затем обрабатывает коммит или откат до того, как ответ покинет представление.

## Валидация Pydantic {#pydantic-validation}

Возможно, вы используете обычные модели SQLAlchemy, но хотите валидировать данные формы по схеме Pydantic перед сохранением. В этом случае `starlette_admin.contrib.sqla.ext.pydantic.ModelView` принимает аргумент `pydantic_model`, чтобы выполнять валидацию по этой схеме, а не по типам столбцов SQLAlchemy:

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

Отправка значения `full_name="Madonna"` (одно слово) приведёт к срабатыванию метода `validate_full_name`. После этого форма создания или редактирования перерисуется с ошибкой, явно привязанной к полю `full_name`. Сам столбец SQLAlchemy `String(100)` такого правила не имеет — ограничение целиком находится в Pydantic-модели `UserIn`. Полный пример см. в [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi); он также включает второе представление (`PostIn`), подключённое к той же панели администрирования.

## Полный рабочий пример

Вот полный пример использования SQLAlchemy со starlette-admin. Работающую версию см. в [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, что позволяет запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

Сохраните следующий код в файл `main.py`. Для наглядности скрипт использует локальную базу данных SQLite (`blog.db`), хотя Starlette-Admin поддерживает как синхронные, так и асинхронные движки для PostgreSQL, MySQL и SQLite.

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

Теперь откройте в браузере страницу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть дашборд администрирования и поработать с ним.

---

## Что читать дальше

* **[Представления](../user-guide/views.md)**: параметры конфигурации `BaseModelView`, независимые от бэкенда.
* [Фильтры](../user-guide/filters.md): подробности о конструкторе фильтров и URL-формате, реализованном на основе реестра фильтров.
* [Представления](../user-guide/views.md): полный список всех параметров конфигурации `ModelView` (независимо от бэкенда).
* [SQLModel](sqlmodel.md): тонкая обёртка над этим бэкендом, добавляющая валидацию Pydantic к формам.
* [Beanie](beanie.md): руководство по использованию того же API `ModelView` с базой данных MongoDB.
* [Tortoise ORM](tortoise.md): другой реляционный бэкенд, встроенный в starlette-admin.
