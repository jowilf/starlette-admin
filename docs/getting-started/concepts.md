---
title: Core Concepts
description: Understand the architectural design principles of starlette-admin, including declarative views, URL-based state, and backend-agnostic models.
---

# Core Concepts

After you complete the Quickstart by writing a `PostView` and mounting an admin instance, learn the architectural design principles of the framework. These core concepts provide the foundation for the rest of the documentation.

## One class per resource

Every resource that the admin manages is exposed through a single, dedicated class. When you subclass `ModelView` and point it to a database model, you automatically generate paginated, sortable, and filterable views for all standard CRUD operations (list, detail, create, edit, and delete).

This eliminates the need to write custom routes or HTML templates. Everything that governs how a resource looks, validates, and behaves lives within this single view class.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## The same view, any backend

Views interface with your data through an adaptable backend layer. Whether your application uses SQLAlchemy, SQLModel, Beanie, MongoEngine, or Tortoise ORM, the configuration API remains exactly the same.

Fields, filters, permissions, and lifecycle hooks work consistently regardless of where your data resides. The knowledge you gain on one backend transfers directly to the others. Swapping your underlying data source only requires an update to your import statements.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## URL-based list state

Sorting, filtering, pagination, and search criteria synchronize directly with the URL query string. Because the server renders list states entirely from these URL parameters, every view state is inherently bookmarkable and shareable.

If you send a specific administrative link to a colleague, they see the exact same filtered rows and sorting configuration that you see.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Fields know how to render themselves

Fields are self-rendering components. Each field type manages its own display logic across three distinct contexts: a cell inside a list table, a row within a detail view, and an input element inside a form.

When you build a view, you declare field instances or pass attribute names that the backend automatically maps to fields. Choose the type that matches your data model, and the framework handles the rendering:

* `StringField` for text strings
* `IntegerField` for numerical data
* `ImageField` for file uploads

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Declarative form layouts

By default, the `fields` attribute renders your create and edit forms as a flat, vertical list. To reorganize the user interface without altering your underlying data definitions, use the `form_layout` attribute.

### The tuple shorthand

For basic grid layouts, group field names into a tuple to render them side by side in a single row. This avoids the need to import complex widget classes.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Advanced layout widgets

As your forms grow in complexity, you can structure them by using layout widgets. The tuple shorthand works natively inside these components:

* **`PanelWidget` or `FieldsetWidget`:** Use these components to group related fields under a clear heading or to make sections collapsible.
* **`TabsWidget`:** Use this component when a resource has distinct categories of data (like shipping versus SEO metadata) that do not need to be visible simultaneously.

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

## Filters are attached to field types

Filtering capabilities map directly to data types, ensuring users only see relevant query options. A `StringField` provides contextual text options like *contains*, *starts with*, *equals*, and *is null*. An integer field provides numerical constraints like *greater than* or *between*.

You can restrict or override these defaults on an individual field by using the `filters` parameter, or you can register custom filters for unique data types.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Bring your own authentication

The framework remains entirely agnostic about your user schema by omitting a built-in user model. Authentication requires implementing a single method: `authenticate(request)`.

Connect this method to your existing authentication infrastructure, such as a local database table, an OAuth provider, or an upstream single sign-on (SSO) proxy header. Returning an `AdminUser` object grants access to the interface. Returning `None` denies access.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Actions run on selected rows

Batch actions operate on multiple rows selected from the top toolbar, and row actions execute inline on individual records. Decorating a view method with `@action` or `@row_action` automatically exposes the method in the user interface without manual route registration.

Instead of returning a message string from the action method, trigger user notifications directly by using the built-in `flash()` utility.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Native data export and import

Every list page features an export dialog that lets users select the scope (selected rows or the current page), fields, format, and filename. Active filters and search terms are preserved, which means the exported file matches exactly what appears on screen.

The framework natively supports CSV, JSON, and PDF formats. For additional formats like Excel (`xlsx`), the framework integrates with `tablib` to support any compatible file type. Formats are declared as plain extension strings. Access control is managed on a granular level by using the `can_export` hook.

The import wizard safely ingests bulk data across these same formats. The wizard validates the upload in a preview step first, highlighting errors row by row before it commits any database writes, and supports optional primary key upserts. You can restrict access to this feature by using the `can_import` hook.

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Flexible file storage

Media management through `FileField` and `ImageField` relies on an underlying `Storage` abstraction layer. Use `LocalStorage` for local disk writes, or install the optional S3 integration by running `pip install starlette-admin[s3]`.

The field automatically coordinates file uploads, backend validation, and frontend rendering after you point it to your chosen storage configuration.

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Custom views and dashboard widgets

Pages that are not explicitly tied to a database model, such as metrics dashboards or custom reports, are built by using `CustomView`. Content is populated by using a `widget` parameter. This parameter accepts either a static `BaseWidget` instance or a dynamic callable execution when the content depends on the incoming request.

You can compose complex user interfaces by arranging layout primitives and data visualization widgets into a clean hierarchy.

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## Events and method hooks

The framework provides two distinct extension points to execute code during create, update, and delete cycles:

1. **Lifecycle methods:** For logic isolated to a specific entity, override local methods like `before_create` directly on your view class.
2. **Event listeners:** For global concerns like audit logs, cache invalidation, or webhooks, subscribe to the `admin.events` system.

Both patterns trigger at identical execution points, which allows you to choose the approach that best fits your application architecture.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**What's next**

* **[Views](../user-guide/views.md):** Every `ModelView` configuration option.
* **[Fields](../user-guide/fields.md):** The full field type catalog.
* **[Form Layouts](../advanced/form-layout.md):** Arrange create and edit forms with rows, panels, and tabs.
* **[Actions](../user-guide/actions.md):** Batch and row actions in depth.
