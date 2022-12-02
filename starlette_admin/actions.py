from typing import Any, Awaitable, Callable, Optional, Sequence, no_type_check

from starlette.requests import Request


def action(
    name: str,
    text: str,
    confirmation: Optional[str] = None,
    theme: Optional[str] = "primary",
) -> Callable[[Request, Sequence[Any]], Awaitable]:
    @no_type_check
    def wrap(f):
        f._action = (name, text, confirmation, theme)
        return f

    return wrap
