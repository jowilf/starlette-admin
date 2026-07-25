# Flash Messages

Flash messages provide temporary, one-time feedback to users after they perform an action (e.g., "Post created successfully" or "Invalid file type"). These messages persist across a single HTTP redirect and are automatically discarded once displayed.

`flash()` queues a message on the current request. The admin interface renders it on the next page the user sees, then clears the queue. This messaging pattern is directly inspired by Flask-Admin.


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

## Message Categories

Every flash message requires a category, which dictates the color of the banner in the default theme so users can gauge severity at a glance.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

The `category` argument defaults to `"info"`. It must be exactly one of `success`, `info`, `warning`, or `error`. Passing any other value raises a `ValueError`.

## Built-in CRUD Messages

You do not need to manually call `flash()` for standard CRUD operations. The admin automatically flashes a `success` message upon completion of the following actions:

| Action | Default Message |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (Single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (Bulk)** | `%(count)d items were successfully deleted.` |

!!! note "**Note on `<repr>`:**"
    The automatic messages use the object's row representation defined by `view.repr()`, not the model's class name. For example, creating a post will flash *“The item ‘My First Post’ was added successfully,”* rather than a generic *“Post was added successfully.”*

## Using Flash Messages in Custom Actions

Handlers for custom actions (`@action` and `@row_action`) return `None` by default. To provide user feedback, you must call `flash()` directly before the handler returns.

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

* **Missing `flash()` calls:** If omitted, the action executes normally, but the user receives no visual confirmation after the page redirects.
* **Handling Errors:** If your custom action raises an `ActionFailed` exception, the admin automatically intercepts it and displays the exception string as an error banner. **Do not** call `flash()` in an `ActionFailed` branch, as the request will not redirect.

## Rendering Messages in Custom Templates

The admin's base template automatically handles popping and rendering flash messages. You only need to retrieve them manually when building fully [custom views](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

Reading the flash queue is **destructive**. The first call to `get_flashed_messages(request)` pops and clears the queue. Any subsequent calls during the same request will return an empty list `[]`.

!!! info "Implementation Details"
    Flash messages are stored in a signed, `httponly` cookie named `admin_flash`, not in the server session. **Because browsers strictly limit cookie sizes (typically around 4KB), you should only use flash messages for brief feedback, avoiding long strings or large data payloads.** This cookie-based approach allows them to work seamlessly without requiring `SessionMiddleware`.

> See [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) for a runnable app that calls `flash()` from hooks and custom actions.

---

## What's Next

* **[Actions](actions.md)**: Learn how to trigger business logic via bulk or row actions.
* **[Security](security.md)**: Understand how `secret_key` secures both the flash cookie and CSRF tokens.
* **[Templates](../advanced/templates.md)**: Discover how to render flash banners inside your own custom layouts.
