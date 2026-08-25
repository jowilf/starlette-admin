---
title: Events
description: Subscribe to global lifecycle events like AFTER_CREATE to build audit logs, webhooks, and asynchronous workflows.
---

# Events

A method hook like `before_create` only runs for the view that defines it. The event system lets code outside that view react to what happens inside it, meaning an audit log, a webhook, or a cache invalidation can live in one place instead of being copy-pasted into every `ModelView` you write.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Register this once next to your `admin` instance and every view's create endpoint calls it, including views you add later.

## View vs. admin level

Every view has an `events` attribute you can subscribe to directly, scoped to that view alone. The `Admin` instance has one too, which reaches every view registered on it, or a subset if you pass `keys=`.

* **`view.events.on(...)`**: Fires only for that view.
* **`admin.events.on(...)`**: Fires for every current and future view, unless you restrict it with `keys=`.

You can register on `admin.events` before or after you call `admin.add_view(...)`. Order doesn't matter: a handler registered first still attaches to the view once you add it.

## Method hooks vs. event subscriptions

Both fire at the same point in the request lifecycle. They differ in where the code lives and how many views it reaches.

| Feature | Method hook (`before_create`, ...) | Event subscription (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Where the code lives** | Inside the view class | Anywhere, for example a module-level function or a subscriber class |
| **Scope** | That specific view | One view (`view.events`) or every view (`admin.events`) |
| **Good for** | Logic specific to that resource (slugify a title, stamp a timestamp) | Cross-cutting concerns (audit logs, notifications, plugins) |
| **Multiples allowed?** | No, one method per view | Yes, any number of handlers per event, ordered by priority |

Use a method hook when the logic is intrinsic to the model. Use an event subscription when it doesn't belong to any single view, or when you're shipping it as a reusable piece across several admins.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## AdminEvent values

`AdminEvent` is a string enum. These are the members actively emitted by the view lifecycle:

| Event | Fired when | Context class |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Record created | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Create transaction committed | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Record updated | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Edit transaction committed | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Record deleted | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Delete transaction committed | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Batch or row action run | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Export triggered | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Import triggered | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Login succeeds | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED`, and `AFTER_DELETE_COMMITTED` only fire for backends that defer the commit to the end of the request, which today means the SQLAlchemy backend. See [Views](../user-guide/views.md#lifecycle-hooks) for the `after_create_committed`, `after_edit_committed`, and `after_delete_committed` hook methods that emit them.

For `AFTER_DELETE_COMMITTED`, `ctx.obj` is a detached instance: its already-loaded attributes stay readable, but reading an attribute that wasn't loaded before the delete raises, because the row behind it is gone.

Every context is a dataclass that inherits from `EventContext`, which carries fields common to all events:

| Attribute | Type | Description |
| --- | --- | --- |
| `event` | `AdminEvent` or `str` | The event that fired |
| `request` | `Request` | The request in flight |
| `view_key` | `str` | The view's `key` |
| `extra` | `dict` | Empty by default, free for you to stash data in a custom handler chain |

Each subclass adds the fields relevant to that event.

Edit events fired by an [inline edit](../user-guide/inline-edit.md) from the list page carry `extra["inline"] = True`, and their `data` / `old_data` payloads contain only the edited field. Everything else is identical to a regular edit, so existing handlers need no changes.

## Subscribing with a decorator

`view.events.on()` works as either a decorator or a direct function call:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

Registered this way, `log_deletion` fires for `order_view` only, not for other views on the admin. The `on()` method also accepts the handler directly, without the decorator form:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: grouping handlers

When one concern reacts to several events, `AdminEventSubscriber` keeps them in a single class instead of scattering module-level functions. Decorate the methods with `@on(AdminEvent.X)`, the module-level `on` from `starlette_admin.events` rather than the bus method, then call `subscribe()` once:

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` is available on both `view.events` and `admin.events`. Call it on `view.events` to scope the subscriber to a single view instead.

One method can handle several events: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` registers the same method for both.

## admin.events: delegating to views

`admin.events.on()` takes the same arguments as `view.events.on()`, plus `keys=`, a list of view keys to restrict the subscription to. Leave it unset (`None`, the default) and every current and future model view gets the handler:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Only the view registered with `key="order"`, or whose default key resolves to `"order"`, calls this handler. An `AFTER_CREATE` on any other view won't trigger it.

`admin.events.subscribe()` accepts `keys=` too, so you can scope an `AdminEventSubscriber` to a subset of views the same way:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` only affects the view-lifecycle events in the table above: create, edit, delete, action, export, and import. That's how `admin.events` decides which views a handler applies to. `AFTER_LOGIN` is admin-level and isn't tied to any view, so `keys=` does nothing for it.

## Priority

`on()` takes a `priority` keyword, an integer that defaults to `0`. Handlers for the same event run in descending priority order, so a higher number fires first:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

Handlers with the same priority run in registration order. `AdminEventSubscriber` methods take a priority through `@on(AdminEvent.X, priority=10)`, which is forwarded the same way.

!!! warning
    A `BEFORE_DELETE` handler, or any `BEFORE_*` handler, that raises an exception stops the operation, and later handlers for that event don't run. An `AFTER_*` handler that raises turns an already-committed change into a failed request. If a failure shouldn't surface as an admin error, wrap risky logic such as network calls or third-party APIs in its own `try`/`except` block inside the handler.

## Extended example

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) runs every pattern on this page together: hook overrides on `PostView`, an `AuditSubscriber` registered on `admin.events` for every view, direct handler registration for delete, export, and import warnings, a handler scoped to `post_view.events`, and a `CommentModerationSubscriber` scoped to `comment_view.events`. Run it to watch priority and scope interact in one app.

---

## What's next

* **[Views](../user-guide/views.md)**: The `before_*` and `after_*` method hooks this page builds on.
* **[Actions](../user-guide/actions.md)**: Batch and row actions, which emit `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Inline Forms](../user-guide/inline-forms.md)**: Nested records created alongside a parent.
