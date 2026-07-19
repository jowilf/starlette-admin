# Views

Starlette Admin builds its sidebar using three types of views: `ModelView` to expose database models, `CustomView` to render standalone pages, and `Link` to add simple hyperlinks.

## ModelView

A `ModelView` subclass is the primary component used to expose a database model in the admin interface. You define how a resource looks, behaves, and processes data using class attributes and method overrides on this view.

Every example on this section uses the following standard SQLAlchemy setup:

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

### Basic Usage

To expose the `Post` model to the admin interface, subclass `ModelView` and configure its attributes.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

A view class remains dormant until registered with an `Admin` instance:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

See [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) for a runnable admin built the same way, on a `Post` model.

Registering a view instantly generates paginated, sortable, and searchable interfaces for listing, viewing, creating, editing, and deleting records. No custom routes or templates are required.

!!! note
    `ModelView` is imported from your specific backend's contrib package (e.g., `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, or `.sqlmodel`). However, **every attribute described below is identical across backends**. You can swap a SQLAlchemy model for a MongoEngine document later without changing your view logic.

### Core Configuration

#### Naming & Routing

Starlette Admin dynamically derives URL routing and UI labels from the model's class name by default. For the `Post` model, it assumes:

* **Key:** `post` (URL: `/admin/post/list`)
* **Menu label:** `Posts` (Sidebar entry)
* **Display name:** `Post` (UI buttons like "New Post")

If the derived values are incorrect, you can override them during registration or within the constructor.

| Attribute | Description | Example Override | Resulting UI / URL |
| --- | --- | --- | --- |
| **`key`** | The internal slug and base URL route. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | The plural noun used for the sidebar navigation. | `menu_label="Blog Posts"` | **Sidebar:** Blog Posts |
| **`display_name`** | The singular noun used for actions and forms. | `display_name="Article"` | **Buttons:** "New Article" |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Field Selection & Customization

The `fields` list dictates which model attributes appear across the list view, detail page, and forms. Omitting this attribute exposes all model attributes by default.

You can mix string names and explicit `BaseField` instances for granular control over widgets, validation, and labeling:

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
    The primary key is auto-detected. You only need to explicitly define `pk_attr` if auto-detection fails, such as when using a custom backend without a standard single-field primary key.

#### Contextual Field Visibility

Fields often need to be visible on the list or detail page but hidden from creation forms, such as timestamps or system-managed statuses. Use the `exclude_fields_from_*` attributes to selectively hide fields from specific UI surfaces:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Available exclusion attributes include `_create`, `_edit`, `_list`, `_detail`, `_export`, and `_import`.

!!! important
    If you must allow edits to the primary key during creation (which is disabled by default), set `show_pk_in_forms = True`.

#### Form Layout

By default, the `fields` attribute renders your create and edit forms as a flat, vertical list. To reorganize the user interface without altering your underlying data definitions, use the `form_layout` attribute.

**The Tuple Shorthand**

For basic grid layouts, you do not need to import complex widget classes. Simply group field names into a tuple to render them side-by-side in a single row.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Advanced Layout Widgets**

As your forms grow in complexity, you can structure them using layout widgets. The tuple shorthand works seamlessly inside these components:

* **`PanelWidget` or `FieldsetWidget`:** Use these to group related fields under a clear heading or to make sections collapsible.
* **`TabsWidget`:** Use this when a resource has distinct categories of data (like shipping versus SEO metadata) that do not need to be visible all at once.

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

### Data Table Features

#### Search & Sort

Control how users find and order data using `searchable_fields` and `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**: Enables the advanced filter builder and the global search box. Global search executes a full-text query against these fields.
* **`sortable_fields`**: Restricts which column headers are clickable for sorting. Unauthorized sort queries via URL parameters are silently ignored.
* **`fields_default_sort`**: Determines the initial table load state. Provide a bare string to sort ascending, a tuple with `True` to sort descending, or a tuple with `False` to explicitly sort ascending. You can also chain multiple items to define a multi-column sort order.

#### Pagination & UI Controls

Fine-tune the list page layout and interactivity using the following attributes:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` / `page_size_options`**: Set the default pagination limit and dropdown choices.
* **`show_goto_page`**: Appends a "go to page" input for navigating large datasets.
* **`search_auto_submit`**: Triggers filtering as the user types.
* **`show_detail_search`**: Injects a search box on the detail page to filter inline relationship tables.
* **`row_click_navigate`**: Opens the detail page when the user clicks anywhere on a table row. Enabled by default; set it to `False` to keep rows inert so users navigate only through the row actions. Rows are never clickable for users whose `can_view_detail` check fails.

#### Inline Editing

To accelerate data management, you can allow users to modify specific fields directly from the list view without opening the full edit form.

Use the `inline_editable_fields` attribute to define which columns support this capability. When configured, clicking an enabled cell opens a contextual popover for rapid updates.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

> **Security & Access:** This feature is disabled by default. When enabled, it remains securely gated by the view's existing `can_edit` permission.

For advanced configuration, validation behaviors, and a complete matrix of supported field types, refer to the [Inline Edit](inline-edit.md) guide.

### Relational Data

Starlette Admin automatically manages complex data relationships. For the Many-to-One setup between `Post` and `Author`, include the relationship attribute in your `fields` list. The UI renders the appropriate widgets automatically as long as both models have registered views.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Manual Relationship Declaration

You only need to manually declare `HasOne` or `HasMany` fields when the target view is registered under a custom `key`.

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

### Object Representation

Whenever the admin needs to display a record as a single value, it falls back to the primary key by default. A `Post` linked to `Author #3` therefore renders as "3" in relationship columns, which tells the user very little. Two optional methods, defined on the **model** rather than the view, replace this default with a meaningful representation. Both methods accept the current `Request` and can be either synchronous or asynchronous.

#### `__admin_repr__`

Returns a plain string used wherever the record appears as text: relationship columns on the list and detail pages, breadcrumbs, and action confirmation messages.

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

Returns an HTML snippet used to render options in the `select2` dropdowns that relationship form fields use. This lets you enrich choices with images, badges, or secondary text. When this method is missing, the admin falls back to the escaped output of `__admin_repr__`, or to a generated summary of the record's non-relation fields when neither method is defined.

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

!!! danger
    Escape database values to prevent Cross-Site Scripting (XSS) attacks. Render the snippet with Jinja2 and `autoescape=True` as shown above, or escape each value manually with `html.escape`. For more information, refer to the [OWASP documentation](https://owasp.org/www-community/attacks/xss/).

### Security & Authorization

Restrict user access by overriding permission methods on your `ModelView`. These methods expect a boolean return value. Base implementations always return `True`.

This pattern integrates directly with your `AuthProvider`. In this example, permissions are checked against a `roles` list stored on the session's `admin_user`:

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

For a deeper dive into configuring your `AuthProvider` and populating the `admin_user` object, refer to the [Authentication](auth.md) documentation.

!!! note
    You only need to override the restricted methods. Unmodified methods will continue to allow access.

### Lifecycle Hooks

Use lifecycle hooks to execute side effects or mutate data immediately before or after a database transaction.

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

#### Committed Hooks

The `after_create_committed`, `after_edit_committed`, and `after_delete_committed` hooks execute only after the database transaction successfully commits. Use these for side effects that must be skipped if a write operation rolls back, such as sending emails or enqueueing background jobs:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    When these hooks execute, the request session is already committed and closed. Do not perform database writes using `request.state.session` within these methods. Instead, use external I/O or instantiate a new database session.

!!! warning
    In `after_delete_committed`, `obj` is detached from any session: attributes already loaded before the delete remain readable, but accessing one that was never loaded will fail, since the row is gone.

!!! note "Backend Support"
    These hooks are emitted exclusively by backends that defer the commit until the end of the request. Currently, this functionality is limited to the SQLAlchemy backend.

!!! tip
    For global logic that spans multiple views, such as a comprehensive audit log, utilize [Events](../advanced/events.md) instead.

### UI Customization

#### Sidebar Organization

Group related views into a collapsible folder using `DropDown`. Folders can mix `ModelView`, `CustomView`, and `Link` entries.

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

#### Exporters & Importers

The `exporters` and `importers` attributes specify the exact formats available for data transfer. Refer to the [Export & Import](export-import.md) guide for details on built-in options and custom implementations.

```python
from starlette_admin.export import CsvExporter, ExcelExporter
from starlette_admin.importers import JsonImporter


class PostView(ModelView):
    exporters = [CsvExporter(), ExcelExporter()]
    importers = [JsonImporter()]
```

### Actions, Inline Forms, and Templates

`ModelView` includes three additional feature sets for complex use cases. Each has a dedicated guide:

* **Actions & Row Actions:** The `actions` and `row_actions` attributes enable custom batch and per-row operations beyond standard CRUD capabilities. See [Actions](actions.md).
* **Inline Forms:** The `inlines` attribute nests a related model's creation and editing forms directly within the parent view. See [Inline Forms](inline-forms.md).
* **Templates & Assets:** Replace default pages with custom Jinja templates using `list_template`, `detail_template`, `create_template`, or `edit_template`. See [Templates](../advanced/templates.md).

## CustomView

Administrative pages do not always map to a database model. `CustomView` creates a standalone sidebar page built from widgets, custom templates, or custom routes.

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

See [Custom Views](custom-views.md) for the full widget catalog, dashboard instructions, and custom route integration.

## Link

`Link` adds a simple hyperlink to the sidebar to point users toward a live site, external documentation, or another internal tool.

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

* **`label`** / **`icon`**: The sidebar entry text and icon.
* **`url`** / **`target`**: The destination and the anchor target attribute.

The `admin.add_link(link)` method is a thin wrapper around `admin.add_view(link)`. Use whichever reads better in your codebase. A `Link` can also be nested inside a `DropDown` as demonstrated in the Sidebar Organization section.

---

## What's Next

* **[Fields](fields.md)**: Explore the complete field type catalog.
* **[Form Layouts](../advanced/form-layout.md)**: Arrange create/edit forms with rows, panels, fieldsets, and tabs.
* **[Custom Views](custom-views.md)**: Build dashboards and standalone pages with widgets, templates, and custom routes.
* **[Actions & Row Actions](actions.md)**: Enable batch and per-row operations beyond standard CRUD capabilities.
* **[Inline Edit](inline-edit.md)**: Let users edit a single field of a row directly from the list page.
* **[Inline Forms](inline-forms.md)**: Learn how to nest a related model's create and edit forms directly within a parent view.
* **[Templates](../advanced/templates.md)**: Swap in your own Jinja templates and inject custom assets.
