---
title: SQLAlchemy Integration
description: Learn how to integrate starlette-admin with SQLAlchemy. Create an admin dashboard for your relational database models in FastAPI.
---

# SQLAlchemy

The SQLAlchemy backend serves as the reference implementation for `BaseModelView`. It has only been tested against SQLAlchemy 2 `DeclarativeBase` models. Other backends (such as Beanie, MongoEngine, Tortoise ORM, or your custom implementation) fulfill this identical contract against their respective data stores.

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

## Install

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

Swap `aiosqlite` for `asyncpg` (PostgreSQL) or `aiomysql`/`asyncmy` (MySQL) if you prefer not to use SQLite. The database driver is only relevant for asynchronous engines. A synchronous engine uses the standard DBAPI driver required by plain SQLAlchemy (like `psycopg2` or `pymysql`) and requires no additional packages from `starlette-admin`.

## Async vs. sync engines

`Admin` accepts either an `Engine` or an `AsyncEngine`. Pass whichever instance you have configured:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` inspects the engine once at request time and opens the matching session type: an `AsyncSession` for an `AsyncEngine` or a plain `Session` for a sync `Engine`. Internally, `ModelView` branches on `isinstance(session, AsyncSession)`. For synchronous sessions, it routes the blocking call through `anyio.to_thread.run_sync` to avoid blocking the event loop.

## Passing a `sessionmaker` instead of an engine

The `session_provider` parameter also accepts a `sessionmaker` or `async_sessionmaker`. Provide a session maker instead of a bare engine when you must configure the session directly.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
The session middleware invokes `session_maker()` to generate a new session for each request rather than constructing one internally.

## `sqla.Admin` and `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` accepts the same arguments as `starlette_admin.BaseAdmin` alongside one required positional argument: `session_provider`. This provider can be an `Engine`, `AsyncEngine`, `sessionmaker`, or `async_sessionmaker`. During initialization, the administration panel configures a session middleware bound to your chosen provider and inserts it at the front of the middleware stack. This mechanism guarantees that `request.state.session` is populated automatically on every request before your view code executes.

`sqla.ModelView` requires a SQLAlchemy model. At initialization, it inspects the model to automatically detect fields, manage primary keys, and configure the filter registry directly from the metadata.

## Model declaration

Define your models using standard SQLAlchemy declarative classes:

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

If you do not set `fields` on the view, `ModelView` uses every attribute declared on the model in the order they appear. The primary key is automatically detected and excluded from create and edit forms. Every other column and relationship converts to an appropriate field type (like `IntegerField`, `StringField`, `EnumField`, `HasOne`, or `HasMany`) automatically.

## Auto-detected defaults

A column's Python-side `default=` configuration populates automatically the first time you open the creation form. You are not required to repeat this definition on the field itself:

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

A scalar default (`default=0`) copies exactly as defined. A callable default (`default=datetime.utcnow` or `default=uuid.uuid4`) triggers once when rendering the form, allowing the reader to see a real value rather than the function's `repr` format.

!!! important
    Primary key columns never receive a pre-filled default even if one is defined. They are assumed to be server-generated (via `autoincrement` or a sequence) and are excluded entirely from create and edit forms. SQL-expression defaults (such as `server_default=func.now()` or a database-side `DEFAULT`) are also skipped because there is no Python-level value to display. The database handles populating these values upon insertion.

## Relationship fields

A SQLAlchemy `relationship()` on the model automatically converts to `HasOne` (many-to-one or one-to-one) or `HasMany` (one-to-many or many-to-many) based on the `RelationshipProperty.direction` attribute. You do not need to explicitly declare the field type:

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

Setting `PostView.fields = ["id", "title", "author"]` renders `author` as a Select2 dropdown. This dropdown is populated via AJAX from the related view's `/_api/{key}/relation-lookup` endpoint (where `{key}` represents `author`, the key of `AuthorView`). The application never loads the entire table of authors into the page at once. This lazy-loading behavior is critical for performance when the related table contains thousands of rows. Similarly, setting `AuthorView.fields = ["id", "name", "posts"]` renders `posts` as a multi-select control utilizing the same lookup endpoint.

## Composite primary keys

Models utilizing multiple `primary_key=True` columns for composite primary keys are supported out of the box without any extra configuration. This includes scenarios where every primary-key column also serves as a foreign key, such as a many-to-many association object.

Please refer to [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks) for a fully runnable example.

## Filter registry

Every field type receives a default set of filters from `SqlaFilterRegistry`. These are resolved by traversing the field's class hierarchy as detailed in the [Filters](../user-guide/filters.md) documentation. A crucial SQLAlchemy-specific detail is how each filter translates into a query fragment. Every `apply()` method in this module returns a standalone SQLAlchemy boolean clause (such as `column == value` or `column.between(a, b)`).

!!! note
    The `Is null` filter on a relationship evaluates `~column.has()` (for many-to-one relations) or `~column.any()` (for one-to-many and many-to-many relations) instead of `column.is_(None)`. Because a relationship attribute is not a standard column containing a `NULL` value, its nullability depends entirely on whether any related rows exist.

!!! note
    The SQLAlchemy backend does not provide `ArrayInFilter` or `ArrayNotInFilter` (the "is one of" filters for list-valued columns) as Beanie and MongoEngine do. You must write your own `apply()` logic if you require "is one of" filtering on a `TagsField`-backed JSON or ARRAY column. Consult the [Custom Filters](../advanced/custom-filters.md) documentation for more details.

## Sessions and transactions

The session middleware opens exactly one session per request and stores it securely on `request.state.session`. This object will be an `AsyncSession` when using an asynchronous engine (or `async_sessionmaker`) and a standard `Session` otherwise. Every component touched by the request shares this single session. The list query, the relationship lookups within forms, and any custom logic running in a hook, action, or endpoint will all operate inside the exact same transaction. You retrieve it uniformly regardless of the underlying engine type:

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

When using a synchronous engine, `request.state.session` evaluates to a standard `Session` and `session.flush()` is called without an `await`. The remainder of the preceding code snippet remains identical. You do not need to import a separate `get_session()` dependency. The session attaches to the request before your hook or action executes because the session middleware establishes the connection prior to invoking the route handler.

**One commit per request.** You should never invoke `session.commit()` manually. Calling `flush()` (or doing nothing if performing read-only queries) is sufficient. The session middleware commits the session exactly once after the route handler returns, provided the response indicates success. If an error occurs, the middleware rolls back the entire transaction automatically:

* If the handler raises an exception, the session rolls back and the application re-raises the exception.
* If the handler returns a response with a `status_code >= 400` (such as a form validation failure), the session rolls back and the server returns the response unmodified. This rollback is crucial because the transaction might contain a failed flush at that stage. Committing it could inadvertently persist a partially written record.
* If the commit operation itself raises an exception (such as a database constraint violation caught at flush time), the session rolls back and re-raises the exception.

In all other scenarios where the handler yields a 2xx or 3xx response, the middleware commits the session and releases the connection. This lifecycle explains why the `publish` action demonstrated above does not require explicit commit or close statements. The session middleware opens the session before your code executes and subsequently handles the commit or rollback operations before the response leaves the view.

## Pydantic validation

You might use plain SQLAlchemy models but still want to validate form data against a Pydantic schema before saving. In this case, `starlette_admin.contrib.sqla.ext.pydantic.ModelView` accepts a `pydantic_model` argument to execute validation against that schema rather than the underlying SQLAlchemy column types:

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

Submitting `full_name="Madonna"` (a single word) fails the `validate_full_name` method. The create or edit form then re-renders with the error explicitly attached to the `full_name` field. The underlying SQLAlchemy `String(100)` column has no such rule. The constraint resides entirely within the `UserIn` Pydantic model. Refer to [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi) for the complete example, which also includes a secondary view (`PostIn`) attached to the same administration panel.

## Full working example


Here is a full SQLAlchemy example with starlette-admin. See [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) for the runnable version.

### 1. Install dependencies

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

The `fastapi[standard]` package includes the FastAPI CLI, allowing you to start the development server by running `fastapi dev`.

### 2. Create the Application

Save the following code as `main.py`. This script uses a local SQLite database (`blog.db`) for demonstration purposes, though Starlette-Admin supports both synchronous and asynchronous engines for PostgreSQL, MySQL, and SQLite.

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

### 3. Run the Server

Start the FastAPI development server:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

You can now navigate to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) in your browser to view and interact with the admin dashboard.

---

## What to Read Next

* **[Views](../user-guide/views.md)**: Explore `BaseModelView` configuration options independent of the backend.
* [Filters](../user-guide/filters.md): Details on the filter builder and URL format powered by the filter registry.
* [Views](../user-guide/views.md): A comprehensive list of every `ModelView` configuration option (backend-agnostic).
* [SQLModel](sqlmodel.md): A thin wrapper around this backend that adds Pydantic validation to forms.
* [Beanie](beanie.md): A guide to using the identical `ModelView` API against a MongoDB database.
* [Tortoise ORM](tortoise.md): The other relational backend built into starlette-admin.
