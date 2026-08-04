---
title: Beanie Integration
description: Integrate Beanie ODM with starlette-admin to create an extensible admin interface for your MongoDB collections in FastAPI.
---

# Beanie Integration

Beanie models MongoDB documents as asynchronous Pydantic models. The `starlette_admin.contrib.beanie` module provides specialized `Admin` and `ModelView` classes configured to interact with these documents directly.

**Key Features:**

- Native support for MongoDB query operators and filtering.
- Automatic translation of Pydantic validation errors into field-specific UI form errors.
- Built-in integration for MongoDB full-text search.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## Minimal example

You must initialize Beanie before any request reaches the administration interface. Wrapping the connection logic inside your main application's `lifespan` context manager is the best approach to ensure this prerequisite is met.

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

The `ModelView` accepts the Beanie `Document` class directly. It automatically derives the field list, forms, and filters from the document's fields.

## Core classes

### The `beanie.Admin` class

The `beanie.Admin` class inherits from `BaseAdmin` and requires no database-specific configuration during initialization. Connection setup occurs entirely within the application's lifespan. Always import `Admin` from `starlette_admin.contrib.beanie` to ensure compatibility with future backend-specific enhancements.

### The `beanie.ModelView` class

The `beanie.ModelView` class provides the integration layer between your database and the UI. It handles several operations automatically:

- **Field population:** Automatically generates fields from the document definition if you do not specify them explicitly.
- **Internal field filtering:** Excludes Beanie's internal `revision_id` field from lists and forms by default.
- **Relationship resolution:** Executes database reads with `fetch_links=True` and `nesting_depth=1`, ensuring that `Link` references resolve to their related objects rather than returning raw database references.
- **Error handling:** Translates Pydantic validation errors into field-specific form errors, pointing users directly to the incorrect input.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## The `BeanieObjectIdField`

Beanie uses `PydanticObjectId` for primary keys. The administration panel automatically represents these keys, and any raw ObjectId references, using a dedicated `BeanieObjectIdField`.

While it renders and validates exactly like a standard `StringField`, it maintains its own slot in the filter registry. This separation ensures that ObjectId-specific filters apply only to ObjectId fields, rather than to every standard text field in your application. These specialized filters safely parse strings into valid `PydanticObjectId` objects before querying the database.

## Filter registry

Every field type receives a default set of filters from the `BeanieFilterRegistry`.

- **String matching:** The equality filter uses case-insensitive regular expressions to maintain consistency with other text searches like "Contains" or "Starts with".
- **Array operations:** The registry provides built-in support for array-based filtering, allowing "Is one of" operations on list-valued fields (like `TagsField`) to work out of the box.
- **Primary keys:** The `id` field automatically remaps to MongoDB's native `_id` when building query fragments.

## Full-text search

When users interact with the search box on a list page, the administration panel checks the MongoDB collection for an existing text index and adjusts its query strategy accordingly:

- **Text index present:** The query utilizes MongoDB's native `$text` operator. This provides true full-text search capabilities, including tokenization, stemming, and relevance ranking.
- **No text index:** The system falls back to a case-insensitive regular expression search across all fields marked as `searchable`. While this requires no setup, it cannot rank results by relevance and cannot utilize standard indexes.

The administration panel detects existing text indexes but does not create them. You must define the index on your Beanie document to enable native text search. For example, you can achieve this by adding `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` to your model.

!!! note
If you enable a text index, you can set `full_text_override_order_by = True` on your `ModelView` subclass to sort search results by MongoDB's relevance score instead of the default column sort.

## Full working example

This section provides a complete, runnable Beanie integration with `starlette-admin`.

### 1. Install dependencies

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

The `fastapi[standard]` package includes the FastAPI CLI, allowing you to start the development server by running `fastapi dev`.

### 2. Create the application

Save the following code in a file named `main.py`.

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

> **Advanced Example:** [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) in the repository contains a fully featured example that includes inline views, events, and custom batch actions.

## What to read next

- **[Views](../user-guide/views.md)**: Explore `BaseModelView` configuration options independent of the backend.
- **[Filters](../user-guide/filters.md):** The filter builder and how ORM-specific filters plug in.
- **[MongoEngine](mongoengine.md):** Another MongoDB backend built into starlette-admin.
- **[SQLAlchemy](sqlalchemy.md):** The relational backend built into starlette-admin.
