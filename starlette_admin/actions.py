from typing import Any, Callable, Optional


def action(
    name: str,
    text: str,
    confirmation: Optional[str] = None,
    submit_btn_text: Optional[str] = "Proceed",
    submit_btn_class: Optional[str] = "btn-primary",
) -> Callable[[Callable], Any]:
    def wrap(f: Callable) -> Callable:
        f._action = {  # type: ignore
            "name": name,
            "text": text,
            "confirmation": confirmation,
            "submit_btn_text": submit_btn_text,
            "submit_btn_class": submit_btn_class,
        }
        return f

    return wrap
