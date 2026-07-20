# Actions, events, and flash messages

## Batch actions

Operate on rows selected on the list page. `delete` is provided by default. Decorate a view method with `@action` and list its name in `actions`. Names must be unique per view.

```python
from starlette_admin import ActionSelection, action, flash
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = ["make_published", "delete"]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Publish selected articles?",   # optional confirm dialog
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        form='<form><input type="text" class="form-control" name="note"></form>',
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data = await request.form()                  # values from the optional form
        for article in await selection.rows():
            article.status = "published"
        flash(request, f"{await selection.count()} article(s) published.", "success")
```

The handler always receives an `ActionSelection`, never a raw `pks` list. It covers both selection modes on the list page: rows checked one by one, or "select all matching" against the current filter/search.

- `await selection.rows()` — the target objects, fetched once and cached.
- `await selection.pks()` — just the primary keys, without loading full rows.
- `await selection.count()` — how many rows are targeted. In select-all mode this runs a `count()` query and enforces `action_select_all_limit` (default 1000), raising `ActionFailed` if the current filter matches too many rows.
- `selection.is_select_all`, `selection.filters`, `selection.q` — reason about *how* rows were selected, for example to push the operation down as one bulk query instead of materializing rows via `selection.rows()`.
- `allow_empty_selection=True` on `@action` marks actions that operate on the whole collection rather than a selection, such as a full sync. They render in a separate, always-visible "Actions" dropdown and can run with zero rows selected. Without it, `handle_action` rejects an empty selection before the handler runs.

Success feedback: call `flash()`. Returning a value is not how feedback works.
Failure: `raise ActionFailed("message")`; the UI shows it as an error banner. Do not also call `flash()` in that branch.
Custom response (redirect, file download): pass `custom_response=True` and return a `Response`.

## Row actions

Per-record actions on the list and detail pages. Built-ins: `view`, `edit`, `delete`.

```python
from starlette_admin.actions import link_row_action, row_action


class ArticleView(ModelView):
    row_actions = ["view", "edit", "go_to_example", "make_published", "delete"]

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish this article?",
        icon_class="fas fa-check-circle",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        article = await self.find_by_pk(request, pk)
        article.status = "published"
        flash(request, "Published.", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"   # plain href, no API round trip
```

Display options: `row_actions_display_type = RowActionsDisplayType.ICON_LIST | DROPDOWN | KEBAB | INLINE_LINKS` (list page only; the detail page always shows full buttons) and `row_actions_position = RowActionsPosition.BEFORE_COLUMNS | AFTER_COLUMNS` (both enums in `starlette_admin.types`).

Restricting: `is_row_action_allowed(request, name)` gates by name (role checks); `is_row_action_allowed_for_obj(request, name, obj)` gates per record (for example hide `make_published` when `obj.is_published`). Always defer to `super()` for other names.

## Dynamic action forms

`form=` also accepts a callable so the HTML is built at request time: `(request) -> str` for `@action`, `(request, obj) -> str` for `@row_action` (use it to pre-fill inputs from the row). Row-action form callables run once per row on the list page: keep them fast, no per-call queries.

## Flash messages

```python
from starlette_admin import flash  # also starlette_admin.flash.flash

flash(request, "Report generated.", "success")   # categories: success, info, warning, error
```

- Category defaults to `"info"`; anything else raises `ValueError`. `message` must be a non-empty string.
- Standard CRUD already flashes success messages automatically; do not duplicate them.
- Stored in a signed httponly cookie (about 4 KB limit, keep messages short) that expires after 5 minutes. A message queued but not rendered within that window (for example a redirect chain that stalls) is silently dropped.
- In custom templates, `get_flashed_messages(request)` pops the queue destructively (second call returns `[]`); the built-in layout renders them for you.

## Events (cross-view hooks)

Method hooks live inside one view; events let external code react to any view. Both fire at the same lifecycle points.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])   # keys=None reaches every view
async def notify_new_order(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} pk={ctx.pk}")
```

- `view.events.on(...)` scopes to one view; `admin.events.on(...)` reaches every current and future view (registration order relative to `add_view` does not matter). Both work as decorator or direct call.
- Events: `BEFORE_/AFTER_CREATE`, `BEFORE_/AFTER_EDIT`, `BEFORE_/AFTER_DELETE`, `AFTER_*_COMMITTED` (SQLAlchemy only), `BEFORE_/AFTER_EXPORT`, `BEFORE_/AFTER_IMPORT`. Context dataclasses carry `event`, `request`, `view_key`, `extra`, plus event-specific fields like `pk` and `obj`.
- `priority=` (int, default 0): higher fires first; ties run in registration order.
- A raising `BEFORE_*` handler aborts the operation and skips later handlers. A raising `AFTER_*` handler turns a committed change into a failed request, so wrap risky I/O in try/except.

Group related handlers in a class:

```python
from starlette_admin.events import AdminEventSubscriber, on


class AuditSubscriber(AdminEventSubscriber):
    @on(AdminEvent.AFTER_CREATE)                       # module-level `on`, stackable,
    async def record_create(self, ctx): ...            # accepts several events at once

    @on(AdminEvent.AFTER_EDIT, AdminEvent.AFTER_DELETE)
    async def record_change(self, ctx): ...


admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

Runnable examples: `examples/09-actions` (all action variants) and `examples/05-events` (hooks, subscribers, priority, scoping).
