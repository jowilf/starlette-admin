# Actions

In `starlette-admin`, actions provide an intuitive way to interact with your database records and perform operations like mass deletions, bulk updates, and sending emails.

## Understanding `ActionSelection`

A central component of the actions API is the `ActionSelection` object. Instead of passing a raw list of primary keys to your handler, `starlette-admin` provides an `ActionSelection` instance.

This object resolves lazily and behaves identically whether the user checked rows individually or used the "select all matching" feature. It also exposes the active list page filters directly to your handler.

### `ActionSelection` API Reference

| Method / Property         | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `await selection.rows()`  | Retrieves the target rows. This is fetched once and cached.       |
| `await selection.pks()`   | Retrieves the primary keys of the targeted rows.                  |
| `await selection.count()` | Returns the total number of rows the action targets.              |
| `selection.is_select_all` | A boolean indicating if the user triggered "select all matching". |
| `selection.filters`       | The active `FilterGroup` (identical to `ListParams.filters`).     |
| `selection.q`             | The active full-text search term, or `None` if inactive.          |

## Batch Actions

By default, updating an object requires selecting it on the list page and modifying it individually. To apply the same change to multiple objects simultaneously, you can add a custom **batch action**.

!!! note
    `starlette-admin` adds a `delete` batch action by default.

To add custom batch actions to your `ModelView`, define an asynchronous function with your logic and wrap it in the `@action` decorator.

!!! warning
    Batch action names must be unique within a `ModelView`.

### Batch Action Example

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
        submit_btn_class="btn-success",
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

## Global Actions

Standard batch actions require an active user selection. The **With selected** dropdown only appears when at least one row is checked. If you need an action to operate on the entire collection (like a full database sync), configure a **Global Action**.

Set `allow_empty_selection=True` in your `@action` decorator. Global actions render in an always-visible **Actions** dropdown and trigger without requiring row selection.

**Handler Behavior for Global Actions:**

- **Empty Selection:** The `selection` object may resolve to zero rows.
- **Incidental Selections:** If a user happens to have rows checked when triggering a global action, those rows are still passed to the handler. You should explicitly ignore `selection` if your logic targets the entire collection.

All other parameters (`confirmation`, `form`, `custom_response`, `is_action_allowed`) function exactly as they do for standard batch actions.

### Global Action Example

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

```

### The "Select All Matching" Feature

When a user checks every row on the current page while more rows match the filter elsewhere, the UI prompts them to select all matching rows.

Selecting this option sends `all=1` to the action API instead of a list of primary keys. Use `selection.is_select_all` to fork your logic, or simply rely on `selection.rows()` to resolve the data either way:

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

!!! note "Materialization Limits:"
`selection.rows()`, `pks()`, and `count()` are capped by `action_select_all_limit` (defaulting to 1000) when in select-all mode. Exceeding this limit raises an `ActionFailed` exception. Handlers that only read `selection.filters` and `selection.q` avoid materialization and bypass this cap entirely.

## Row Actions

Row actions allow users to perform operations on individual items directly from the list view. By default, `starlette-admin` includes three row actions: `view`, `edit`, and `delete`.

To add custom row actions, define your logic and apply the `@row_action` decorator. If the action simply navigates the user to a different URL, use the `@link_row_action` decorator instead. This embeds the link directly into the HTML `href` attribute, skipping the action API entirely.

!!! warning
    Row action names must be unique within a `ModelView`.

### Row Action Example

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
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
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

### Restricting Row Actions

Two specific hooks govern row action availability. Both default to allowing the action.

1. **`is_row_action_allowed(request, name)`**: Evaluated once per action name. Ideal for row-independent restrictions like role-based access control.
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: Evaluated once per row for actions that pass the first check. Ideal for data-dependent restrictions (e.g., hiding a "Publish" button on an already published article).

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
    Always call `super()` for action names your override does not explicitly handle. Failing to do so will silently disable the permission checks for built-in actions.

## UI Configuration for Row Actions

### Display Types

The `row_actions_display_type` parameter dictates how actions appear on the list page. Detail page actions always render as full buttons.

| Display Type   | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| `ICON_LIST`    | Renders a horizontal list of icon-only buttons.                       |
| `DROPDOWN`     | Groups actions into a labeled dropdown menu.                          |
| `KEBAB`        | Groups actions into a dropdown menu triggered by a `⋮` icon.          |
| `INLINE_LINKS` | Renders the action label beneath the icon, separated by a middle dot. |

### Column Positioning

By default, the actions column renders before your data columns. You can move it to the right side of the table using `RowActionsPosition`:

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## Dynamic Action Forms

The `form` parameter on both `@action` and `@row_action` decorators accepts a callable. This allows you to generate HTML dynamically at request time.

The callable can be synchronous or asynchronous and must return a string.

- **`@action` signature**: `(request) -> str`
- **`@row_action` signature**: `(request, obj) -> str`

This is highly recommended for pre-filling form inputs with a specific row's existing values.

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

!!! warning
    Row action form callables execute once per row on the list page. Design them to be fast and avoid database queries inside the callable. All necessary row data is already accessible via the `obj` parameter.
