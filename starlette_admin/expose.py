from typing import Any, Awaitable, Callable, List, Optional, Sequence

from starlette.middleware import Middleware
from starlette.routing import get_name


def expose(
    path: Optional[str] = "/",
    *,
    methods: Optional[List[str]] = None,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    middleware: Optional[Sequence[Middleware]] = None,
) -> Callable[[Callable[..., Awaitable[str]]], Any]:
    """
        Use this decorator to expose views in your view classes.

        path: Route path
        methods: HTTP methods
        name: Route name
        include_in_schema: Include in schema
        middleware: Starlette middlewares
    !!! usage

        ```python
        class ArticleView(ModelView):
            actions = ['make_published', 'redirect']

        ```
    """

    def wrap(f: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
        f._route = {
            "path": path,
            "methods": methods,
            "name": get_name(f) if name is None else name,
            "include_in_schema": include_in_schema,
            "middleware": middleware,
        }
        return f

    return wrap
