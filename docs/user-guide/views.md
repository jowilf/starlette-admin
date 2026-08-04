---
title: Views
description: Learn how to configure list and detail views in starlette-admin, including search, sorting, and pagination.
---

# Views

`starlette-admin` builds its sidebar from three kinds of view: `ModelView` exposes a database model, `CustomView` renders a standalone page, and `Link` adds a hyperlink.

## ModelView

A `ModelView` subclass is how you expose a database model in the admin. Class attributes and method overrides on that view define how the resource looks, behaves, and handles data.

Every example in this section uses the following SQLAlchemy setup:

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Basic usage

To expose the `Post` model, subclass `ModelView` and configure its attributes.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

A view class does nothing until you register it with an `Admin` instance:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

See [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) for a runnable admin built the same way, on a `Post` model.

Registering a view generates paginated, sortable, and searchable interfaces for listing, viewing, creating, editing, and deleting records. You write no routes and no templates.

!!! note
    You import `ModelView` from your backend's contrib package, such as `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel`, or `.tortoise`. **Every attribute described below is identical across backends**, so you can swap a SQLAlchemy model for a MongoEngine document later without changing your view logic.

### Core configuration

#### Naming and routing

By default, the admin derives URL routing and UI labels from the model's class name. For the `Post` model, it uses:

* **Key:** `post` (URL: `/admin/post/list`)
* **Menu label:** `Posts` (sidebar entry)
* **Display name:** `Post` (UI buttons such as **New Post**)

When the derived values are wrong, override them at registration or in the constructor.

| Attribute | Description | Example override | Resulting UI or URL |
| --- | --- | --- | --- |
| **`key`** | The internal slug and base URL route. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | The plural noun used in the sidebar. | `menu_label="Blog Posts"` | **Sidebar:** Blog Posts |
| **`display_name`** | The singular noun used in actions and forms. | `display_name="Article"` | **Buttons:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Field selection and customization

The `fields` list sets which model attributes appear on the list view, the detail page, and the forms. Omit it to expose every model attribute.

Mix string names and explicit `BaseField` instances to control widgets, validation, and labels:

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    The admin detects the primary key for you. Define `pk_attr` only when detection fails, such as on a custom backend without a single-field primary key.

#### Contextual field visibility

Fields often belong on the list or detail page but not on a create form, such as timestamps and system-managed statuses. Use the `exclude_fields_from_*` attributes to hide a field from specific surfaces:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

The available exclusion attributes end in `_create`, `_edit`, `_list`, `_detail`, `_export`, and `_import`.

!!! important
    To let users set the primary key when they create a record, which is off by default, set `show_pk_in_forms = True`.

#### Form layout

By default, `fields` renders your create and edit forms as a flat, vertical list. To reorganize the interface without touching your data definitions, use the `form_layout` attribute.

**The tuple shorthand**

For a basic grid, you don't need to import widget classes. Group field names into a tuple to render them side by side in one row.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Advanced layout widgets**

As your forms grow, structure them with layout widgets. The tuple shorthand works inside them:

* **`PanelWidget` or `FieldsetWidget`:** Group related fields under a heading, or make a section collapsible.
* **`TabsWidget`:** Separate distinct categories of data, such as shipping details and SEO metadata, that don't need to be visible at the same time.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

See [Form Layouts](../advanced/form-layout.md) for multi-column rows with explicit widths, tabs, static content, and access-control behavior.

### Data table features

#### Search and sort

Control how users find and order data with `searchable_fields` and `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**: Turns on the filter builder and the global search box. Global search runs a full-text query against these fields.
* **`sortable_fields`**: Restricts which column headers users can sort by. A sort query for another field, passed through URL parameters, is ignored.
* **`fields_default_sort`**: Sets the initial table state. Pass a bare string to sort ascending, a tuple with `True` to sort descending, or a tuple with `False` to sort ascending explicitly. Chain several items for a multi-column sort.

#### Pagination and UI controls

Fine-tune the list page layout with these attributes:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` and `page_size_options`**: The default pagination limit and the dropdown choices.
* **`show_goto_page`**: Adds a "go to page" input for large datasets.
* **`search_auto_submit`**: Filters as the user types.
* **`show_detail_search`**: Adds a search box on the detail page to filter inline relationship tables.
* **`row_click_navigate`**: Opens the detail page when the user selects anywhere on a table row. It's on by default. Set it to `False` to keep rows inert, so users navigate through the row actions instead. Rows are never clickable for users whose `can_view_detail` check fails.

#### Inline editing

You can let users change specific fields straight from the list view, without opening the full edit form.

Use the `inline_editable_fields` attribute to declare which columns support it. Selecting an enabled cell then opens a popover for a quick update.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Security and access"
    Inline editing is off by default. When you turn it on, the view's existing `can_edit` permission still gates it.

For configuration details, validation behavior, and the full matrix of supported field types, see the [Inline Edit](inline-edit.md) guide.

### Relational data

The admin handles data relationships for you. For the many-to-one setup between `Post` and `Author`, add the relationship attribute to your `fields` list. As long as both models have registered views, the UI renders the right widgets.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Manual relationship declaration

Declare `HasOne` or `HasMany` fields yourself only when the target view is registered under a custom `key`.

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Object representation

When the admin needs to show a record as a single value, it falls back to the primary key. A `Post` linked to `Author #3` then renders as "3" in relationship columns, which tells the user almost nothing. Two optional methods, defined on the **model** rather than the view, replace that default with something meaningful. Both accept the current `Request` and can be synchronous or asynchronous.

#### `__admin_repr__`

Returns a plain string, used wherever the record appears as text: relationship columns on the list and detail pages, breadcrumbs, and action confirmation messages.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

With this method in place, a post's author renders as "Gabriel Garcia Marquez" instead of "3".

#### `__admin_select2_repr__`

Returns an HTML snippet that renders the options in the `select2` dropdowns used by relationship form fields, so you can enrich choices with images, badges, or secondary text. Without this method, the admin falls back to the escaped output of `__admin_repr__`. Without either method, it falls back to a generated summary of the record's non-relation fields.

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    The returned value must be valid HTML.

!!! warning
    Escape database values to prevent cross-site scripting (XSS) attacks. Render the snippet with Jinja2 and `autoescape=True`, as shown above, or escape each value yourself with `html.escape`. For more information, see the [OWASP documentation](https://owasp.org/www-community/attacks/xss/).

### Security and authorization

Restrict access by overriding permission methods on your `ModelView`. Each returns a boolean, and the base implementations all return `True`.

This pattern plugs straight into your `AuthProvider`. In the example below, each check reads a `roles` list from the session's `admin_user`:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

For more on configuring your `AuthProvider` and populating the `admin_user` object, see [Authentication](auth.md).

!!! note
    Override only the methods you want to restrict. The ones you leave alone keep allowing access.

### Lifecycle hooks

Use lifecycle hooks to run side effects or mutate data right before or after a database transaction.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

The available hooks are `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete`, and `after_delete_committed`.

#### Committed hooks

`after_create_committed`, `after_edit_committed`, and `after_delete_committed` run only after the database transaction commits. Use them for side effects that must not happen when a write rolls back, such as sending email or queuing background jobs:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    By the time these hooks run, the request session is committed and closed. Don't write to the database through `request.state.session` inside them. Use external I/O, or open a new database session.

!!! important
    In `after_delete_committed`, `obj` is detached from any session. Attributes loaded before the delete stay readable, but reading one that was never loaded fails, because the row is gone.

!!! note "Backend support"
    Only backends that defer the commit to the end of the request emit these hooks. Today that's the SQLAlchemy backend.

!!! tip
    For logic that spans several views, such as an audit log, use [Events](../advanced/events.md) instead.

### UI customization

#### Sidebar organization

Group related views into a collapsible folder with `DropDown`. A folder can mix `ModelView`, `CustomView`, and `Link` entries.

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Exporters and importers

The `exporters` and `importers` attributes set which formats are available for data transfer. See the [Export & Import](export-import.md) guide for the built-in options and for writing your own.

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Actions, inline forms, and templates

`ModelView` has three more feature sets for complex cases, each with its own guide:

* **Actions and row actions:** The `actions` and `row_actions` attributes add custom batch and per-row operations beyond CRUD. See [Actions](actions.md).
* **Inline forms:** The `inlines` attribute nests a related model's create and edit forms inside the parent view. See [Inline Forms](inline-forms.md).
* **Templates and assets:** Replace the default pages with your own Jinja templates through `list_template`, `detail_template`, `create_template`, or `edit_template`. See [Templates](../advanced/templates.md).

## CustomView

Not every admin page maps to a database model. `CustomView` creates a standalone sidebar page built from widgets, custom templates, or custom routes.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

See [Custom Views](custom-views.md) for the full widget catalog, dashboard instructions, and custom routes.

## Link

`Link` adds a hyperlink to the sidebar, pointing users to a live site, external documentation, or another internal tool.

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** and **`icon`**: The sidebar entry text and icon.
* **`url`** and **`target`**: The destination and the anchor target attribute.

`admin.add_link(link)` is a thin wrapper around `admin.add_view(link)`. Use whichever reads better in your codebase. You can also nest a `Link` inside a `DropDown`, as shown in [Sidebar organization](#sidebar-organization).

---

## What's next

* **[Fields](fields.md)**: The complete field type catalog.
* **[Form Layouts](../advanced/form-layout.md)**: Arrange create and edit forms with rows, panels, fieldsets, and tabs.
* **[Custom Views](custom-views.md)**: Build dashboards and standalone pages with widgets, templates, and custom routes.
* **[Actions & Row Actions](actions.md)**: Add batch and per-row operations beyond CRUD.
* **[Inline Edit](inline-edit.md)**: Let users edit a single field of a row from the list page.
* **[Inline Forms](inline-forms.md)**: Nest a related model's create and edit forms inside a parent view.
* **[Templates](../advanced/templates.md)**: Swap in your own Jinja templates and inject custom assets.
