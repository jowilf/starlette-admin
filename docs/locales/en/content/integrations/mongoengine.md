---
title: MongoEngine Integration
description: Learn how to connect MongoEngine models with starlette-admin to manage your MongoDB data via an admin panel.
---

# MongoEngine Integration

MongoEngine models MongoDB documents as synchronous Python classes using a Django-style field API. The `starlette_admin.contrib.mongoengine` module provides specialized `Admin` and `ModelView` classes that build administrative views directly from your `mongoengine.Document` definitions.

**Key Features:**

* Automatic conversion of field types, relationships, and embedded documents.
* Out-of-the-box support for GridFS-backed `FileField` and `ImageField` uploads.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## Minimal example

You must establish the MongoDB connection before any request reaches the admin interface. Wrapping the connection logic inside your main application's `lifespan` context manager is the best approach to ensure this prerequisite is met.

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

The `ModelView` accepts the `mongoengine.Document` class directly. It automatically derives the field list, forms, and filters from the document's fields.

## Core classes: Admin and ModelView

### The `mongoengine.Admin` class

The `mongoengine.Admin` class extends the base `Admin` by adding a specialized route: `/api/file/{db}/{col}/{pk}`. This route streams a GridFS file directly back to the browser.

Since every `FileField` and `ImageField` upload on a MongoEngine model is stored in GridFS, this route is required to serve those files. Always use `mongoengine.Admin` instead of the base `Admin`.

### The `mongoengine.ModelView` class

Unlike the base class, the `mongoengine.ModelView` constructor takes a `document` positional argument instead of a declarative model class:

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

If you leave the `fields` attribute unset on your `ModelView` subclass, it defaults to including every field on the document in the order they are declared.

Attributes like `key`, `menu_label`, and `display_name` follow a strict fallback order:

1. The constructor argument.
2. A class-level attribute set on the subclass.
3. A value derived from the document's class name (`key` becomes the slugified name, `menu_label` becomes the pluralized prettified name, and `display_name` becomes the singular prettified name).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Filter registry

Every field type includes a fixed set of filters provided by the `MongoEngineFilterRegistry`. You can override these defaults per field using the `filters=[...]` argument.

| Field Type | Available Filters |
| --- | --- |
| `StringField` | contains, not contains, starts with, ends with, equals, not equals, is null, is not null |
| `TextAreaField` | contains, not contains, starts with, ends with, is null, is not null |
| `EnumField` | equals, not equals, in, not in, is null, is not null |
| `NumberField` | equals, not equals, greater than, less than, between, is null, is not null |
| `FloatField` | equals, not equals, greater than, less than, between, is null, is not null |
| `DateField` | equals, between, in the past, in the future, is null, is not null |
| `DateTimeField` | equals, between, in the past, in the future, is null, is not null |
| `BooleanField` | is true, is false, is null, is not null |
| `TagsField` | in, not in, is null, is not null |
| `RelationField` | is null, is not null |
| `ObjectIdField` | equals, not equals, in, not in, is null, is not null |

!!! note
    The `ObjectIdField` represents the document `id`.

Under the hood, every filter's `apply()` method returns a MongoEngine `Q` fragment for its specific condition. Nested `FilterGroup` trees then combine those fragments using bitwise operators (`&` or `|`) before executing the query. For more details, see the [Filters](../user-guide/filters.md) documentation.

## Embedded documents

MongoEngine's `EmbeddedDocumentField` converts into a `CollectionField`. This process recursively converts every field on the embedded document into its own sub-field:

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

In this example:

* The `address` field renders as a nested sub-form during creation and editing, and as a nested block on the detail page.
* The `comments` field (an `EmbeddedDocumentListField`) converts to a `ListField` of `CollectionField`. It renders as a repeatable group of sub-forms, displaying one per list entry.

## Full working example

This section provides a complete, runnable MongoEngine integration with `starlette-admin`.

### 1. Install dependencies

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

The `fastapi[standard]` package includes the FastAPI CLI, allowing you to start the development server by running `fastapi dev`.

### 2. Create the application

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


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
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


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

> **Advanced Example:** [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) in the repository contains a fully featured application. It includes inline views, events, and custom row and batch actions, GridFS image and file uploads.

---

## What to read next

* **[Views](../user-guide/views.md)**: Explore `BaseModelView` configuration options independent of the backend.
* **[Fields](../user-guide/fields.md):** Detailed guide to every field type and its attributes, including the `CollectionField`.
* **[Filters](../user-guide/filters.md):** Explore the filter builder UI and learn how to write a custom filter.
* **[Beanie](beanie.md):** Discover the async, Pydantic-based alternative for MongoDB.
