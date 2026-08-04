---
title: Quickstart
description: Build a fully functional CRUD admin interface for FastAPI and Starlette in minutes with our comprehensive quickstart guide.
---

# Quickstart

Build a fully functional CRUD admin interface for a blog in minutes, with automatically generated forms, lists, search, import, and export powered directly from your data models.

## Installation

Install the necessary packages using your preferred package manager:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    The `fastapi[standard]` package includes the FastAPI CLI, which allows you to start the development server by running `fastapi dev`.

## The complete example

Create a file named `main.py` and add the following code:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## Run the application

Start the development server:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Open a browser and go to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

In the sidebar, select **Posts**, and then select **Create**. You can now access paginated list, detail, create, edit, and delete pages. The system automatically generates all these interfaces from your model definition.

## How it works

The following sections explain the core components of the application.

### The model

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

This code uses standard SQLAlchemy 2.0. The starlette-admin package reads the column metadata mapped to these attributes to determine the exact HTML input to generate. For example, it creates a text input for `str`, a checkbox for `bool`, and a datetime picker for `datetime`.

### The view

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` serves as the central object for this resource. The `fields` attribute controls which columns appear in the list and form, while `searchable_fields` enables the search bar. All configurations for how `Post` looks and behaves in the admin dashboard reside within this single class.

!!! note
    The example imports `ModelView` from `starlette_admin.contrib.sqla` because it relies on SQLAlchemy. If you use a different backend, such as Beanie, MongoEngine, or Tortoise ORM, you must import `ModelView` from the corresponding contrib package. The configuration API remains consistent across all supported backends.

### The admin

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

The `Admin` class connects the database engine to the user interface.

* `add_view` registers your view with the sidebar. The optional `icon` parameter accepts any valid [Font Awesome](https://fontawesome.com/icons) class.
* `mount_to` attaches the admin application to your FastAPI or Starlette application at the `/admin` path.

!!! warning
    The `secret_key` parameter signs cookies for session data, including flash messages and CSRF protection. In production environments, you must replace the example value with a long, random, and securely generated string. Never use a placeholder value in a live deployment.

## Add a second model

You can register an unlimited number of models. For example, to add a `Tag` model and its corresponding view, define the classes and call `add_view` again:

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

Refresh the browser window to see both **Posts** and **Tags** appear in the sidebar. Each resource now features its own fully functional list, create, edit, and delete pages.

---

## Next steps

* **[Concepts](concepts.md):** Learn the terminology for the concepts introduced here to better navigate the User Guide.
* **[Admin](../user-guide/admin.md):** Discover all `Admin(...)` options, including branding, theming, authentication, security, and internationalization.
* **[Views](../user-guide/views.md):** Explore every `ModelView` configuration option available for customizing your data presentation.
