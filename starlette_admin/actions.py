from typing import Any, Awaitable, Callable, Optional


def action(
    name: str,
    text: str,
    confirmation: Optional[str] = None,
    submit_btn_text: Optional[str] = "Proceed",
    submit_btn_class: Optional[str] = "btn-primary",
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


    !!! usage
        ```python
        class ArticleView(ModelView):
            actions = ['make_published']

            @action(
                name="make_published",
                text="Mark selected articles as published",
                confirmation="Are you sure you want to mark selected articles as published ?",
                submit_btn_text="Yes, proceed",
                submit_btn_class="btn-success",
            )
            async def make_published_action(self, request: Request, pks: List[Any]) -> str:
                # Write your logic here
                if ... :
                    # Display meaningfully error
                    raise ActionFailed("Sorry, We can't proceed this action now.")
                # Display successfully message
                return "{} articles were successfully marked as published".format(len(pks))
        ```
    """

    def wrap(f: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
        f._action = {  # type: ignore
            "name": name,
            "text": text,
            "confirmation": confirmation,
            "submit_btn_text": submit_btn_text,
            "submit_btn_class": submit_btn_class,
        }
        return f

    return wrap
