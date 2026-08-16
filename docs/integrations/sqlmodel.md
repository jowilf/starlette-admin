---
title: SQLModel Integration
description: Build a comprehensive admin dashboard for your FastAPI SQLModel applications using starlette-admin.
---

# SQLModel Integration

[SQLModel](https://sqlmodel.tiangolo.com/) combines SQLAlchemy tables with Pydantic validation in a single model class. Because SQLModel models are SQLAlchemy models under the hood, the `starlette_admin.contrib.sqlmodel` module serves as a thin wrapper around the existing [SQLAlchemy backend](sqlalchemy.md).

Rather than implementing a separate system, this integration inherits all field auto-detection, primary key management, relationship handling, filtering, and session middleware directly from the core SQLAlchemy backend. It introduces a robust validation layer that runs submitted form data through your model's native Pydantic validators (such as `Field(min_length=...)` or custom `@field_validator` methods) before any database writes occur. Any resulting `ValidationError` exceptions are automatically translated into per-field form errors in the UI.

!!! note
    Everything documented on the [SQLAlchemy page](sqlalchemy.md) applies unchanged. This includes synchronous and asynchronous engines, `sessionmaker` providers, the one-commit-per-request session lifecycle, relationship fields, and the filter registry.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## Minimal example

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

The `ModelView` accepts the SQLModel table class directly and automatically derives the field list, forms, and filters from the model's schema.

## Core classes

### `sqlmodel.Admin`

The `sqlmodel.Admin` class is the `sqla.Admin` class re-exported. It uses the same constructor, accepting an `Engine`, `AsyncEngine`, `sessionmaker`, or `async_sessionmaker` as its required `session_provider` argument. It also inserts the same session middleware that populates `request.state.session` on every request.

### `sqlmodel.ModelView`

The `sqlmodel.ModelView` class inherits everything from `sqla.ModelView` and adds a validation layer. Its `validate()` method calls `self.model.model_validate(data)` before writing the record, ensuring form submissions are checked by the model's Pydantic validators instead of relying strictly on SQLAlchemy column constraints. File fields and relationship fields are intentionally excluded from this validation call because they fall outside the model's Pydantic validation surface.

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

Inline views allow users to edit related rows inside the parent form. The class inherits foreign key detection and session handling from the SQLAlchemy `InlineModelView` and applies the same Pydantic validation to each inline row.

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Pydantic validation

Constraints declared on the model apply automatically to the create and edit forms:

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

An input like a `full_name` shorter than two characters or an invalid email address will fail validation. These failures return as per-field form errors before any `INSERT` or `UPDATE` operation reaches the database.

!!! note
    The `EmailStr` type requires the `email-validator` package, which is installable via `pip install "pydantic[email]"`.

## Full working example

This section provides a complete and runnable SQLModel integration with `starlette-admin`.

### 1. Install dependencies

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

The `fastapi[standard]` package includes the FastAPI CLI, allowing you to start the development server by running `fastapi dev`.

### 2. Create the application

Save the following code in a file named `main.py`.

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

Submitting a `title` shorter than three characters or a `name` shorter than two characters re-renders the form with the error attached to the offending field.

### 3. Run the server

Start the FastAPI development server:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Navigate to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) in your browser to view and interact with the admin dashboard.

> **Advanced Example:** [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) in the repository contains a fully featured CMS example that includes relationships, inline views, actions, filters, events, and exports.

## What to read next

* **[SQLAlchemy](sqlalchemy.md):** The backend this integration builds on, covering engines, sessions, transactions, and the filter registry.
* **[Views](../user-guide/views.md):** Explore `BaseModelView` configuration options independent of the backend.
* **[Filters](../user-guide/filters.md):** Learn about the filter builder and how ORM-specific filters plug in.
