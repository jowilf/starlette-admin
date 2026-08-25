---
title: Tortoise ORM Integration
description: Easily create an admin interface for your Tortoise ORM models in FastAPI using starlette-admin.
---

# Tortoise ORM Integration

Tortoise ORM is an asyncio-native object-relational mapper inspired by Django. The `starlette_admin.contrib.tortoise` module provides specialized `Admin`, `ModelView`, and `InlineModelView` classes that are pre-configured to integrate directly with your Tortoise models.

**Key Features:**

* **Automatic field conversion:** Maps Tortoise model fields directly to UI components. This includes full support for enums, JSON, dates, and automatic timestamps.
* **Relational mapping:** Converts foreign key and one-to-one relations into `HasOne` fields, and many-to-many relations into `HasMany` fields. Backward relations are automatically rendered as read-only.
* **Advanced filtering:** Leverages Tortoise `Q` expressions for the filter builder and enables case-insensitive full-text search across string fields.
* **Error translation:** Maps Tortoise validation errors directly to field-specific form errors in the UI.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Minimal example

Tortoise connects to the database inside your application's `lifespan` context manager. Because admin views are typically instantiated at import time (before `Tortoise.init()` executes), you must resolve relations early.

Call `Tortoise.init_models()` immediately after defining your models to ensure relations are available when the admin views are built.

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


# Resolve relations at import time before the admin views are built.
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

The `ModelView` accepts the Tortoise `Model` class directly and automatically derives the field list, forms, and filters from the model's schema.

## Core classes

### `tortoise.Admin`

The `tortoise.Admin` class inherits from `BaseAdmin` and requires no database-specific configuration during initialization. Connection setup occurs entirely within the application's lifespan. Always import `Admin` from `starlette_admin.contrib.tortoise` to ensure compatibility with future backend-specific enhancements.

### `tortoise.ModelView`

The `tortoise.ModelView` class provides the integration layer between your database and the user interface. It handles the following operations automatically:

* **Field population:** Generates fields from the model definition if you do not specify them explicitly. The raw key columns backing to-one relations (like `author_id` for a relation named `author`) and backward relations are omitted by default.
* **Relation resolution:** Prefetches every relation shown by the view. This ensures that lists and detail pages never trigger lazy loads.
* **Auto timestamps:** Columns using `DatetimeField(auto_now=...)` or `DatetimeField(auto_now_add=...)` are rendered read-only and are never marked as required.
* **Error handling:** Translates Tortoise validation errors (`"<field>: <detail>"`) into field-specific form errors that point users directly to the incorrect input.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Inline views allow users to edit related rows inside the parent form. The foreign key is auto-detected when the child model has exactly one relation pointing to the parent model. If multiple relations exist, you must set `fk_attr` explicitly using either the relation name or its raw key column.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Handling relations

The integration maps database relations to admin fields based on the field type. You must register a `ModelView` for every related model so relation fields can successfully resolve their foreign views.

| Relation Type | Tortoise Configuration | Admin Behavior |
| --- | --- | --- |
| **Forward (To-One)** | `ForeignKeyField`, `OneToOneField` | Converts to `HasOne`. |
| **Forward (To-Many)** | `ManyToManyField` | Converts to `HasMany`. |
| **Backward** | `related_name` properties | Renders read-only. Must be added to `fields` explicitly to display. |

**Filtering and Sorting on Relations:**
To-one relations offer "Is null" and "Is not null" filters targeting the raw key column. To expose a relation in the filter builder, add the relation name to `searchable_fields`. To enable sorting by the raw key column, add the relation name to `sortable_fields`.

## Search and filtering

### Filter registry

Every field type receives a default set of filters from the `TortoiseFilterRegistry`, implemented using Tortoise `Q` expressions:

* **String matching:** Contains, starts/ends with, and equality filters use case-insensitive lookups (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enums:** Raw filter values are coerced back to enum members before querying for both `CharEnumField` and `IntEnumField` columns.
* **Time columns:** `TimeField` columns offer only null checks. This limitation exists because time-typed parameters cannot be bound portably across all database backends.

### Full-text search

The list page's search box builds a case-insensitive `contains` match (`OR`-combined `Q` expressions) across all searchable string-like fields. You can customize this behavior by overriding the `get_search_query()` method on your view.

## Full working example

This section provides a complete, runnable Tortoise ORM integration with `starlette-admin`.

### 1. Install dependencies

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

The `fastapi[standard]` package includes the FastAPI CLI, allowing you to start the development server by running `fastapi dev`.

### 2. Create the application

Save the following code in a file named `main.py`.

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


# Resolve relations at import time before the admin views are built.
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

Because `created_at` uses `auto_now_add`, the admin renders it read-only automatically. No `exclude_fields_from_create` or `exclude_fields_from_edit` configuration is needed.

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

> **Advanced Example:** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) in the repository contains a fully featured example that includes relations, inline views, enums, and JSON fields backed by SQLite.

## What to read next

* **[Views](../user-guide/views.md):** Explore `BaseModelView` configuration options independent of the backend.
* **[Filters](../user-guide/filters.md):** Learn about the filter builder and how ORM-specific filters plug in.
* **[SQLAlchemy](sqlalchemy.md):** Documentation for the other relational backend built into starlette-admin.
