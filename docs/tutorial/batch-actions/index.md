# Batch Actions

By default, to update an object, you must select it in the list page and update it. This works well for a majority of
use cases. However, if you need to make the same change to many objects at once, this workflow can be quite tedious.

In these cases, you can write a *custom batch action* to bulk update many objects at once.

!!! note
    *starlette-admin* add by default an action to delete many object at once

To add other batch actions to your [ModelView][starlette_admin.views.BaseModelView], besides the default delete action, you can define a
function that implements the desired logic and wrap it with the [@action][starlette_admin.actions.action] decorator (Heavily inspired by Flask-Admin).

## Example
```python
from typing import List, Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = ["make_published", "redirect", "delete"] # `delete` function is added by default

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
