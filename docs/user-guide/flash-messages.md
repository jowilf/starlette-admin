---
title: Flash Messages
description: Send ephemeral success, warning, or error alerts to users after completing actions in starlette-admin.
---

# Flash Messages

Flash messages give users temporary, one-time feedback after they perform an action, such as "Post created successfully" or "Invalid file type". A message survives a single HTTP redirect, and the admin discards it after it's displayed.

`flash()` queues a message on the current request. The admin renders the message on the next page the user sees, then clears the queue. This pattern comes from Flask-Admin.


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash

class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Queue the message for the next page load
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")

```

## Message categories

Every flash message needs a category. The category sets the color of the banner in the default theme, so users can gauge severity at a glance.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

The `category` argument defaults to `"info"`. It must be exactly one of `success`, `info`, `warning`, or `error`. Any other value raises a `ValueError`.

## Built-in CRUD messages

You don't need to call `flash()` for standard CRUD operations. The admin flashes a `success` message automatically when these actions finish:

| Action | Default message |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "What `<repr>` resolves to"
    The automatic messages use the row representation that `view.repr()` defines, not the model's class name. For example, creating a post flashes *"The item 'My First Post' was added successfully"* rather than a generic *"Post was added successfully"*.

## Using flash messages in custom actions

Handlers for custom actions (`@action` and `@row_action`) return `None` by default. To give the user feedback, call `flash()` before the handler returns.

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash

class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Notify the user that the custom action succeeded
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **If you omit `flash()`:** The action still runs, but the user gets no visual confirmation after the page redirects.
* **If the action fails:** When your custom action raises `ActionFailed`, the admin intercepts the exception and displays the exception string as an error banner. Don't call `flash()` in an `ActionFailed` branch, because the request doesn't redirect.

## Rendering messages in custom templates

The admin's base template pops and renders flash messages for you. You only need to retrieve them yourself when you build a fully [custom view](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

Reading the flash queue is **destructive**. The first call to `get_flashed_messages(request)` pops and clears the queue. Later calls during the same request return an empty list, `[]`.

!!! important "Keep messages short"
    Flash messages live in a signed, `httponly` cookie named `admin_flash`, not in the server session. Browsers limit cookie size to roughly 4 KB, so use flash messages only for brief feedback. Avoid long strings and large data payloads. The cookie-based approach also means flash messages work without `SessionMiddleware`.

> See [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) for a runnable app that calls `flash()` from hooks and custom actions.

---

## What's next

* **[Actions](actions.md)**: Trigger business logic from bulk or row actions.
* **[Security](security.md)**: See how `secret_key` secures both the flash cookie and CSRF tokens.
* **[Templates](../advanced/templates.md)**: Render flash banners inside your own layouts.
