---
title: Actions
description: Execute batch and row-level operations with custom confirmations and forms directly from the list view.
---

# Actions

Actions give you a direct way to work with your database records from the admin UI, so users can run operations like mass deletions, bulk updates, and email sends.

## Understanding `ActionSelection`

`ActionSelection` is the central object in the actions API. Instead of a raw list of primary keys, your handler receives an `ActionSelection` instance.

The object resolves lazily and behaves the same whether the user checked rows one by one or used "select all matching". It also exposes the active list page filters to your handler.

### `ActionSelection` API reference

| Method or property        | Description                                                           |
| ------------------------- | --------------------------------------------------------------------- |
| `await selection.rows()`  | Retrieves the target rows. Fetched once, then cached.                 |
| `await selection.pks()`   | Retrieves the primary keys of the target rows.                        |
| `await selection.count()` | Returns the total number of rows the action targets.                  |
| `selection.is_select_all` | A boolean that tells you whether the user chose "select all matching". |
| `selection.filters`       | The active `FilterGroup`, identical to `ListParams.filters`.          |
| `selection.q`             | The active full-text search term, or `None` when search is inactive.  |

## Batch actions

By default, users update an object by selecting it on the list page and editing it on its own. To apply the same change to many objects at once, add a custom **batch action**.

!!! note
    `starlette-admin` adds a `delete` batch action by default.

To add a custom batch action to your `ModelView`, write an async function with your logic and wrap it in the `@action` decorator.

!!! important
    Batch action names must be unique within a `ModelView`.

### Batch action example

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

```

## Global actions

A standard batch action needs an active selection: the **With selected** dropdown appears only when at least one row is checked. When an action targets the whole collection instead, such as a full database sync, make it a global action.

Set `allow_empty_selection=True` in the `@action` decorator. Global actions render in an always-visible **Actions** dropdown and run without a row selection.

**How the handler behaves for global actions:**

- **Empty selection:** The `selection` object can resolve to zero rows.
- **Incidental selections:** If the user has rows checked when they trigger a global action, the handler still receives those rows. Ignore `selection` explicitly when your logic targets the entire collection.

Every other parameter (`confirmation`, `form`, `custom_response`, and `is_action_allowed`) works exactly as it does for a standard batch action.

**Dedicated toolbar buttons:** Add `dedicated_button=True` to render a global action as its own toolbar button instead of an entry in the **Actions** dropdown. The built-in export action uses this option. Combining `dedicated_button=True` with a selection-only action raises an error at startup.

### Global action example

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

```

### The "select all matching" feature

When a user checks every row on the current page and more rows match the filter elsewhere, the UI offers to select all matching rows.

That option sends `all=1` to the action API instead of a list of primary keys. Use `selection.is_select_all` to branch your logic, or let `selection.rows()` resolve the data either way:

```python
    @action(name="archive", text="Archive")
    async def archive_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        if selection.is_select_all:
            await self.bulk_archive_where(request, selection.filters, selection.q)
        else:
            await self.bulk_archive_pks(request, await selection.pks())

```

!!! important "Materialization limits"
    In select-all mode, `selection.rows()`, `pks()`, and `count()` are capped by `action_select_all_limit`, which defaults to 1000. Going over the limit raises an `ActionFailed` exception. A handler that reads only `selection.filters` and `selection.q` materializes nothing, so the cap doesn't apply.

## Row actions

Row actions let users operate on a single item straight from the list view. `starlette-admin` includes three row actions by default: `view`, `edit`, and `delete`.

To add a custom row action, write your logic and apply the `@row_action` decorator. When the action only sends the user to a different URL, use the `@link_row_action` decorator instead. It embeds the link in the HTML `href` attribute and skips the action API.

!!! important
    Row action names must be unique within a `ModelView`.

### Row action example

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### Restricting row actions

Two hooks govern whether a row action is available. Both allow the action by default.

1. **`is_row_action_allowed(request, name)`**: Runs once per action name. Use it for restrictions that don't depend on the row, such as role-based access control.
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: Runs once per row, for the actions that passed the first check. Use it for data-dependent restrictions, such as hiding a **Publish** button on an article that's already published.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView

class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)

```

!!! warning
    Always call `super()` for action names your override doesn't handle. If you don't, you silently disable the permission checks for the built-in actions.

## UI configuration for row actions

### Display types

The `row_actions_display_type` parameter sets how actions appear on the list page. Detail page actions always render as full buttons.

| Display type   | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| `ICON_LIST`    | Renders a horizontal list of icon-only buttons.                       |
| `DROPDOWN`     | Groups actions into a labeled dropdown menu.                          |
| `KEBAB`        | Groups actions into a dropdown menu opened by a `⋮` icon.             |
| `INLINE_LINKS` | Renders the action label beneath the icon, separated by a middle dot. |

### Column positioning

By default, the actions column renders before your data columns. To move it to the right side of the table, use `RowActionsPosition`:

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## Dynamic action forms

The `form` parameter on both the `@action` and `@row_action` decorators accepts a callable, so you can generate the HTML at request time.

The callable can be synchronous or asynchronous, and it must return a string.

- **`@action` signature**: `(request) -> str`
- **`@row_action` signature**: `(request, obj) -> str`

Use a callable when you want to prefill form inputs with a row's current values.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]

```

!!! important
    A row action form callable runs once per row on the list page. Keep it fast and avoid database queries inside it. The row data you need is already available through the `obj` parameter.
