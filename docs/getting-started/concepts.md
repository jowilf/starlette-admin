# Core Concepts

Now that you have completed the Quickstart by writing a `PostView` and mounting an admin instance, let's explore the architectural design principles behind the framework. Understanding these core concepts will make the rest of the documentation intuitive.

## One Class per Resource

Every resource managed by the admin is exposed through a single, dedicated class. By subclassing `ModelView` and pointing it to a database model, you instantly generate paginated, sortable, and filterable views for list, detail, creation, editing, and deletion operations.

You do not need to write custom routes or HTML templates for standard CRUD operations. Everything governing how a resource looks, validates, and behaves lives within this single view class, providing a single source of truth.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## The Same View, Any Backend

Views interface with your data through a pluggable backend layer. Whether your application uses SQLAlchemy, SQLModel, Beanie, or MongoEngine, the configuration API remains completely identical.

Fields, filters, permissions, and lifecycle hooks work consistently regardless of where your data resides. What you learn on one backend transfers directly to the others. Swapping your underlying data source only requires changing your import statements.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## URL-Based List State

Sorting, filtering, pagination, and search criteria are fully synchronized with the URL query string. Because the server renders list states entirely from the parameters provided in the URL, every view state is inherently bookmarkable and shareable.

If you send a specific administrative link to a colleague, they will see the exact same filtered rows and sorting configuration that you do.

```
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Fields Know How to Render Themselves

Fields are self-rendering components. Each field type inherently manages its own display logic across three distinct contexts: a cell inside a list table, a row within a detail view, and an input element inside a form.

When building a view, you declare field instances or pass attribute-name strings that the backend automatically maps to fields. Choose the type that matches your data model, and rendering follows automatically:

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

## Declarative Form Layouts

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

## Filters Are Attached to Field Types

Filtering capabilities are mapped directly to data types, ensuring users only see relevant query options. A `StringField` provides contextual text options like *contains*, *starts with*, *equals*, and *is null*. An integer field provides numerical constraints like *greater than* or *between*.

You can restrict or override these defaults on an individual field using the `filters` parameter, or you can register custom filters for unique data types.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Bring Your Own Authentication

The framework remains entirely agnostic about your user schema by omitting a built-in user model. Authentication requires implementing a single method: `authenticate(request)`.

Connect this method to your existing authentication infrastructure, such as a local database table, an OAuth provider, or an upstream single sign-on (SSO) proxy header. Returning an `AdminUser` object permits access to the interface; returning `None` denies it.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Actions Run on Selected Rows

Batch actions operate on multiple rows selected from the top toolbar, while row actions execute inline on individual records. Decorating a view method with `@action` or `@row_action` automatically exposes it in the user interface without manual route registration.

Instead of returning a message string from the action method, trigger user notifications directly using the built-in `flash()` utility.

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

## Export and Import Are Built In

Every list page features a native export dialog that lets users pick the scope (selected rows or the current page), fields, format, and filename. Active filters and search terms are preserved: what you see in the interface matches what you export.

The framework provides built-in support for CSV, JSON, and PDF out of the box. For additional formats like Excel (`xlsx`), the framework integrates with `tablib` to support any compatible format. Formats are declared as plain extension strings: CSV and JSON are enabled by default, and adding `"xlsx"` or `"pdf"` expands your options. Access control is managed on a granular level using the `can_export` hook.

The import wizard safely ingests bulk data across these built-in and `tablib` formats. It validates the upload in a preview step first, highlighting errors row by row before committing any database writes, and it supports optional primary key upserts. Restrict access to this feature using the `can_import` hook.

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

## File Storage Is Pluggable

Media management through `FileField` and `ImageField` relies on an underlying `Storage` abstraction layer. Use `LocalStorage` for local disk writes, or install the optional S3 integration via `pip install starlette-admin[s3]`.

The field automatically coordinates file uploads, backend validation, and frontend rendering once pointed to your storage configuration.

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

## Custom Views and Dashboard Widgets

Pages not explicitly tied to a database model, such as metrics dashboards or custom reports, are built using `CustomView`. Content is populated via a `widget` parameter, which accepts either a static `BaseWidget` instance or a dynamic callable execution when content depends on the incoming request.

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

## Events and Method Hooks

The framework provides two distinct extension points to execute code during create, update, and delete cycles:

1. **Lifecycle Methods:** For logic isolated to a specific entity, override local methods like `before_create` directly on your view class.
2. **Event Listeners:** For cross-cutting concerns like audit logs, cache invalidation, or webhooks, subscribe globally to the `admin.events` system.

Both patterns trigger at identical execution points, allowing you to choose the approach that best fits your application architecture.

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

* [Views](../user-guide/views.md): every `ModelView` configuration option
* [Fields](../user-guide/fields.md): the full field type catalog
* [Form Layouts](../advanced/form-layout.md): arrange create/edit forms with rows, panels, and tabs
* [Actions](../user-guide/actions.md): batch and row actions in depth