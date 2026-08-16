# 05: Events

A blog admin that demonstrates five ways to hook into the starlette-admin lifecycle, with a live audit log that records every create, update, and delete.

## What it shows

- **Pattern 1: Hook overrides** (`PostView`, `CommentView`): override `before_create` to auto-stamp `created_at` and `before_edit` to stamp `updated_at` before each save.
- **Pattern 2: `AdminEventSubscriber`** (`AuditSubscriber`): subclass `AdminEventSubscriber`, decorate methods with `@on(AdminEvent.*)`, and call `admin.events.subscribe()`. Each handler receives a typed context object (`AfterCreateContext`, `AfterEditContext`, `AfterDeleteContext`) after the database operation completes. Registered on `admin.events`, so it fires for **all** views.
- **Pattern 3: Direct handler registration (admin-wide)**: pass a coroutine to `admin.events.on()` to handle a single event type across all views without creating a subscriber class (`warn_before_delete` logs a warning before every deletion).
- **Pattern 4: View-scoped handler** (`post_view.events.on()`): register a coroutine directly on an individual view's `EventBus`. The handler only fires for that view: `log_post_before_update` runs only when a `Post` is about to be updated, never for `Comment` or `AuditLog`.
- **Pattern 5: View-scoped subscriber** (`comment_view.events.subscribe()`): same as Pattern 2 but subscribed on a single view's `EventBus`. `CommentModerationSubscriber` receives `AFTER_CREATE` and `AFTER_EDIT` events only for the `Comment` view.

The `AuditLog` view is read-only (`can_create / can_edit / can_delete` return `False`) and shows the entries written by `AuditSubscriber`.

## Run

```bash
cd examples/05-events
uv run app.py
```

Then open <http://localhost:8000/admin/>.

Create, edit, or delete a Post or Comment; the Audit Logs list updates after each operation. A `WARNING` line for `BEFORE_DELETE` appears in the terminal on every deletion, and `BEFORE_EDIT` on Post edits logs the changed fields. Comment events are additionally logged by `CommentModerationSubscriber`.
