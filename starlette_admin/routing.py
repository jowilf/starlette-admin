from collections.abc import Callable


def route(
    path: str,
    methods: list[str] | None = None,
    name: str | None = None,
) -> Callable:
    """Decorator to expose additional routes on a
    [CustomView][starlette_admin.views.CustomView].

    Example:
        ```python
        class AnalyticsDashboard(CustomView):
            menu_label = "Analytics"
            path = "/analytics"

            @route("/data", methods=["GET"])
            async def chart_data(self, request: Request) -> Response:
                return JSONResponse({"revenue": 42})

            @route("/run-report", methods=["POST"])
            async def run_report(self, request: Request) -> Response:
                return JSONResponse({"status": "ok"})
        ```

    Args:
        path: URL path relative to the view's ``path``. E.g. ``"/data"``
            on a view with ``path="/analytics"`` registers ``/analytics/data``.
        methods: HTTP methods this route responds to. Defaults to ``["GET"]``.
        name: Optional route name (used by Starlette URL building).
            If not provided, the method's ``__name__`` is used.
    """

    def wrap(fn: Callable) -> Callable:
        fn._route_path = path  # ty: ignore[unresolved-attribute]
        fn._route_methods = methods or ["GET"]  # ty: ignore[unresolved-attribute]
        fn._route_name = name  # ty: ignore[unresolved-attribute]
        return fn

    return wrap
