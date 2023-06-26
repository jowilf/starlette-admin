from typing import Any, Awaitable, Callable, Optional

from starlette_admin.i18n import lazy_gettext as _


def action(
    name: str,
    text: str,
    confirmation: Optional[str] = None,
    submit_btn_text: Optional[str] = _("Yes, Proceed"),
    submit_btn_class: Optional[str] = "btn-primary",
    form: Optional[str] = None,
    custom_response: Optional[bool] = False,
) -> Callable[[Callable[..., Awaitable[str]]], Any]:
    """
    Use this decorator to add custom actions to your [ModelView][starlette_admin.views.BaseModelView]

    Args:
        name: unique action name for your ModelView
        text: Action text
        confirmation: Confirmation text. If not provided, action will be executed
                      unconditionally.
        submit_btn_text: Submit button text
        submit_btn_class: Submit button variant (ex. `button-primary`, `button-ghost-info`,
                `btn-outline-danger`, ...)
        form: Custom form to collect data from user
        custom_response: Set to True when you want to return a custom Starlette response
            from your action instead of a string.


    !!! usage
        ```python
        class ArticleView(ModelView):
            actions = ['make_published', 'redirect']

            @action(
                name="make_published",
                text="Mark selected articles as published",
                confirmation="Are you sure you want to mark selected articles as published ?",
                submit_btn_text="Yes, proceed",
                submit_btn_class="btn-success",
                form='''
                <form>
                    <div class="mt-3">
                        <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
                    </div>
                </form>
                '''
            )
            async def make_published_action(self, request: Request, pks: List[Any]) -> str:
                # Write your logic here

                data: FormData =  await request.form()
                user_input = data.get("example-text-input")

                if ... :
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
    """

    def wrap(f: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
        f._action = {  # type: ignore
            "name": name,
            "text": text,
            "confirmation": confirmation,
            "submit_btn_text": submit_btn_text,
            "submit_btn_class": submit_btn_class,
            "form": form if form is not None else "",
            "custom_response": custom_response,
        }
        return f

    return wrap
