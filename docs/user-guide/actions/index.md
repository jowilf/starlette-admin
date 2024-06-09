# Actions

In starlette-admin, actions provide an easy way to interact with your database records and
perform various operations such as mass delete, special mass updates, sending emails, etc.

## Batch Actions

By default, to update an object, you must select it in the list page and update it. This works well for a majority of
use cases. However, if you need to make the same change to many objects at once, this workflow can be quite tedious.

In these cases, you can write a *custom batch action* to bulk update many objects at once.

!!! note

    *starlette-admin* add by default an action named `delete` to delete many object at once

To add other batch actions to your [ModelView][starlette_admin.views.BaseModelView], besides the default delete action,
you can define a
function that implements the desired logic and wrap it with the [@action][starlette_admin.actions.action] decorator (
Heavily inspired by Flask-Admin).

!!! warning

    The batch action name should be unique within a ModelView.

### Example

```python
from typing import List, Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = ["make_published", "redirect", "delete"]  # `delete` function is added by default

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
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
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        # Write your logic here

        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        if ...:
            # Display meaningfully error
            raise ActionFailed("Sorry, We can't proceed this action now.")
        # Display successfully message
        return "{} articles were successfully marked as published".format(len(pks))

    # For custom response
    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form='''
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        '''
    )
    async def redirect_action(self, request: Request, pks: List[Any]) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")
```

## Row actions

Row actions allow you to perform actions on individual items within a list view.

!!! note

    By default, starlette-admin includes three (03) row actions

    - `view`: redirects to the item's detail page
    - `edit`: redirects to the item's edit page
    - `delete`: deletes the selected item

To add other row actions to your [ModelView][starlette_admin.views.BaseModelView], besides the default ones, you can
define a function that implements the desired logic and wrap it with
the [@row_action][starlette_admin.actions.row_action] decorator

For cases where a row action should simply navigate users to a website or internal page, it is preferable to
use the [@link_row_action][starlette_admin.actions.link_row_action] decorator. The key difference is
that `link_row_action`
eliminates the need to call the action API. Instead, the link is included directly in the href attribute of the
generated html element (e.g. `<a href='https://example.com/?pk=4' ...>`).

!!! warning

    The row actions (both [@row_action][starlette_admin.actions.row_action]
    and [@link_row_action][starlette_admin.actions.link_row_action]) name should be unique within a ModelView.

### Example

```python
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin._types import RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    ...
    row_actions = ["view", "edit", "go_to_example", "make_published",
                   "delete"]  # edit, view and delete are provided by default
    row_actions_display_type = RowActionsDisplayType.ICON_LIST  # RowActionsDisplayType.DROPDOWN

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
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
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        # Write your logic here

        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        if ...:
            # Display meaningfully error
            raise ActionFailed("Sorry, We can't proceed this action now.")
        # Display successfully message
        return "The article was successfully marked as published"

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### List rendering

The `RowActionsDisplayType` enum provides options for customizing how row actions are displayed in the list view.

#### RowActionsDisplayType.ICON_LIST

```python hl_lines="5"
from starlette_admin._types import RowActionsDisplayType


class ArticleView(ModelView):
    row_actions_display_type = RowActionsDisplayType.ICON_LIST
```

<img width="1262" alt="Screenshot 2023-10-21 at 4 39 58 PM" src="https://github.com/jowilf/starlette-admin/assets/31705179/670371b1-7c28-4106-964f-b7136e7268ea">

#### RowActionsDisplayType.DROPDOWN

```python hl_lines="5"
from starlette_admin._types import RowActionsDisplayType


class ArticleView(ModelView):
    row_actions_display_type = RowActionsDisplayType.DROPDOWN
```

<img width="1262" alt="Screenshot 2023-10-21 at 4 48 06 PM" src="https://github.com/jowilf/starlette-admin/assets/31705179/cf58efff-2744-4e4f-8e67-fc24fec8746b">
