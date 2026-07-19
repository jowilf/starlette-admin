# Add an Admin Panel to FastAPI in 5 Minutes with starlette-admin

_2026-07-13_

You shipped the API. Now, someone on your team needs to edit the data behind it: fix a typo in a record, unpublish a post, or check what a user actually submitted. The standard options are usually costly:

| Option                   | The Drawback                                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Custom CRUD Frontend** | Takes weeks of developer time to build and maintain.                                                       |
| **Raw Database Access**  | Creates a massive security and data integrity liability.                                                   |
| **Django Admin / Flask Admin**         | Forces a framework rewrite or relies on synchronous WSGI, which blocks your asynchronous ASGI application. |
| **starlette-admin**      | **Mounts to your app instantly with zero frontend code.**                                                  |

`starlette-admin` works with any Starlette-based application, which is exactly what FastAPI is.

This guide takes you from an empty file to a working back office in five minutes. You will build paginated lists, search functionality, sortable columns, create and edit forms validated by your existing Pydantic schemas, deletion confirmations, and CSV exports, all generated directly from a SQLAlchemy model.

The full runnable code is available at [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Minute 1: Install

You need three packages: the admin framework, the ORM, and FastAPI itself.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic ships with FastAPI, which becomes important later: the admin panel can reuse the exact same schemas your API uses for validation.

## Minutes 2 and 3: The Complete App

Create `main.py`. This is the entire application:

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

Notice what is missing. There are no templates, route handlers for the admin pages, serializers, or field configurations. `starlette-admin` reads the SQLAlchemy column metadata and derives the entire interface automatically: bounded text inputs for the two `String` columns, a textarea for the `Text` content, and a datetime picker for `published_at`.

The three highlighted lines are your only integration points. `Admin` binds the database engine, `add_view` registers the model in the sidebar, and `mount_to` attaches everything to your existing FastAPI app under the `/admin` path. Your API routes remain untouched; the admin panel simply operates as a mounted sub-application.

## Minute 4: Run It

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Open [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) and click **Post** in the sidebar. Out of the box, you get:

- A paginated, sortable list view of all posts.
- Create and edit forms equipped with the correct input widget per column type.
- A detailed view page for each record.
- Batch deletion capabilities with a confirmation dialog.
- CSV and Excel exports for the current list.

Your API continues to serve traffic normally. Check [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to verify everything is intact.

## Minute 5: Make It Feel Hand-Built

The default view provides a complete CRUD interface, but a real back office deserves tailoring: your field order, your form layout, and your search behavior. Subclassing `ModelView` is where `starlette-admin` unlocks its full potential. Replace the `add_view` call with a configured view:

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

Four powerful upgrades occur in this single class:

- **`SlugField(populate_from="title")`**: Generates the slug automatically as the operator types the title, requiring zero custom JavaScript on your end.
- **`ComputedField`**: Renders a value that does not exist in the database. The word count computes via a plain Python callable at render time.
- **`form_layout`**: Arranges the form into logical rows: title and slug side by side, content at full width, and the publication date below.
- **`search_auto_submit`**: Filters the list dynamically as the operator types across all columns defined in `searchable_fields`.

## Rejecting Bad Data: Use the Schema You Already Have

Operators make mistakes, meaning the admin needs to enforce your rules on the server side. The advantage is that you already wrote those rules. Every FastAPI project validates its request bodies with Pydantic models, so somewhere in your codebase, there is a schema that looks like this:

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

Instead of writing validation logic twice, hand the admin your existing model. The `ext.pydantic` extension provides a `ModelView` that processes every form submission through a Pydantic model before it reaches the database. Point your `ModelView` import to the extension, keep `Admin` as is, and pass the schema:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

The body of `PostView` remains exactly the same; only its base class changes through the new import.

The integration is seamless. Every constraint fires during creation and editing: the length bounds, the slug regex, and the custom `field_validator`. Each Pydantic error maps directly back to its corresponding form field and renders inline, mirroring a hand-built form perfectly. Be sure to keep `id` optional in the schema so that create forms, which lack an ID initially, can still validate.

This establishes a single source of truth. When your API schema receives a new rule, the admin enforces it on the next request without requiring any admin-side code changes.

## One Spare Minute? Give Posts an Author

Real data relies on relationships, and the admin handles them using the same zero-configuration approach. Add a `User` model and link it to `Post`:

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

Register the user model using the same schema-driven pattern. `EmailStr` and `HttpUrl` provide format validation automatically, and `email-validator` is already included with `fastapi[standard]`:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Because there is nothing to configure this time, the extension `ModelView` is used directly without subclassing.

Finally, make the author mandatory by adding two lines to `PostIn`:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` lacks a default value, meaning a post without an author is rejected just like any other validation error. The type is the SQLAlchemy `User` class itself because the admin resolves the selected ID to an ORM instance before validation runs. This is exactly why `arbitrary_types_allowed` is required (`ConfigDict` is imported from `pydantic`).

Next, add `"user"` to `PostView.fields` and `form_layout` so the author appears in the post form. This field is not a standard dropdown. It is a select input featuring server-side autocomplete that searches your users as the operator types, and the user detail page links back to every related post.

!!! note
`create_all` does not alter existing tables, so you will need to delete `blog.db` before restarting to pick up the new `user_id` column.

## Before You Deploy

!!! warning
The `secret_key` parameter signs the session cookie used for CSRF protection and flash messages. Replace the placeholder with a long, random value from your settings before deployment, and ensure you load it from your environment variables rather than hardcoding it into the source code.

!!! note
`Base.metadata.create_all(engine)` in the lifespan is a convenience for the quickstart. In a production project, your tables are managed by migrations (like Alembic). Drop that call and point the `Admin` directly at your existing engine. `starlette-admin` never modifies your schema; it only reads and writes rows.

## This Scales Past the Demo

Everything above utilizes two models, but these exact `ModelView` mechanics can support a massive back office. You can easily implement file and image uploads, [authentication with role-based access](../../user-guide/auth.md), [custom filters](../../user-guide/filters.md), [row and batch actions](../../user-guide/actions.md), and comprehensive [i18n](../../user-guide/i18n.md). Whenever the built-in behavior falls short, every query and lifecycle step offers an override hook. This flexibility is exactly how patterns like [soft deletes with a trash view](soft-deletes-trash-view.md) are built.

---

## What's Next

- **[Concepts](../../getting-started/concepts.md):** The vocabulary behind what you just built, ensuring the rest of the documentation reads fluently.
- **[Views](../../user-guide/views.md):** A deep dive into every `ModelView` option including and permission hooks.
- **[Soft Deletes and a Trash View in FastAPI](soft-deletes-trash-view.md):** The first advanced recipe, built directly on the override hooks introduced here.
