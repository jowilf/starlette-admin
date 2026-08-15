from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Match, Mount, Route, WebSocketRoute
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp
from starlette_admin.events import AdminEvent, AdminEventBus, AfterLoginContext
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


def login_not_required(endpoint: Callable[..., Any]) -> Callable[..., Any]:
    """Mark an endpoint as exempt from the authentication check.

    Apply this decorator to a route handler to let unauthenticated requests reach it.
    `AuthMiddleware` checks for the `_login_not_required` attribute set here before
    redirecting to the login page.
    """
    endpoint._login_not_required = True  # ty: ignore[unresolved-attribute]
    return endpoint


@dataclass
class AdminUser:
    username: str = field(default_factory=lambda: _("Administrator"))
    photo_url: str | None = None


class BaseAuthProvider(ABC):
    """
    Minimal contract every auth provider must satisfy.

    Args:
        login_path: Path for the login page/redirect.
        logout_path: Path for the logout endpoint.
        allow_routes: Route names that bypass the auth check.
    """

    def __init__(
        self,
        login_path: str = "/login",
        logout_path: str = "/logout",
        allow_routes: Sequence[str] | None = None,
    ) -> None:
        self.login_path = login_path
        self.logout_path = logout_path
        self.allow_routes: list[str] = (
            list(allow_routes) if allow_routes is not None else []
        )
        # Set by `BaseAdmin._init_auth`, used to emit `AFTER_LOGIN`.
        self.events: AdminEventBus | None = None
        _log.debug(
            "auth provider init: %s login_path=%r logout_path=%r allow_routes=%r",
            type(self).__name__,
            login_path,
            logout_path,
            self.allow_routes,
        )

    @abstractmethod
    async def authenticate(self, request: Request) -> AdminUser | None:
        """Authenticate the current request.

        Returns:
            An `AdminUser` if the request is authenticated, or `None` to deny access.
            `AuthMiddleware` stores the result on `request.state.admin_user` and sets
            `request.state.is_anonymous` accordingly.
        """

    def get_routes(self, templates: Jinja2Templates) -> list[Route]:
        """Return the routes this provider mounts inside the admin prefix."""
        return []

    def get_middleware(self) -> Middleware:
        return Middleware(AuthMiddleware, provider=self)

    async def _emit_after_login(self, request: Request, user: AdminUser | None) -> None:
        """Emits `AFTER_LOGIN` on the admin's event bus, once login succeeds."""
        if self.events is None:
            return
        ctx = AfterLoginContext(
            event=AdminEvent.AFTER_LOGIN,
            request=request,
            view_key="",
            user=user,
        )
        await self.events.emit(ctx)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, provider: "BaseAuthProvider") -> None:
        super().__init__(app)
        self.provider = provider
        self.allow_routes: list[str] = ["login", "static", *provider.allow_routes]
        _log.debug(
            "AuthMiddleware init: provider=%s allow_routes=%r",
            type(provider).__name__,
            self.allow_routes,
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Enforce authentication for every request that passes through this middleware.

        Allows the request through when one of the following holds: the provider
        authenticates the user (`authenticate()` returns an `AdminUser`), the matched
        route name is in `allow_routes`, or the endpoint is decorated with
        `@login_not_required`. Otherwise, redirects to the login page.
        """
        _admin_app: Starlette = request.scope["app"]
        current_route: Route | Mount | WebSocketRoute | None = None
        for route in _admin_app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                if not isinstance(
                    route, (Route, Mount, WebSocketRoute)
                ):  # pragma: no cover
                    raise TypeError(f"Unexpected route type {type(route).__name__}")
                current_route = route
                break

        route_name = getattr(current_route, "name", None)
        route_path = getattr(current_route, "path", None)
        _log.debug(
            "auth check: %s %s  route=%r path=%r from %s",
            request.method,
            request.url.path,
            route_name,
            route_path,
            request.client.host if request.client else "unknown",
        )

        user = await self.provider.authenticate(request)

        if user is not None:
            if not isinstance(user, AdminUser):
                raise TypeError(
                    f"authenticate() must return an AdminUser instance, "
                    f"got {type(user).__name__}"
                )
            request.state.admin_user = user
            request.state.is_anonymous = False
            _log.debug(
                "auth: authenticated user=%r route=%r %s %s",
                user,
                route_name,
                request.method,
                request.url.path,
            )
            return await call_next(request)

        request.state.is_anonymous = True

        if current_route is not None and current_route.name in self.allow_routes:
            _log.debug(
                "auth: allowed (route in allow_routes) route=%r",
                route_name,
            )
            return await call_next(request)

        if (
            current_route is not None
            and hasattr(current_route, "endpoint")
            and getattr(current_route.endpoint, "_login_not_required", False)
        ):
            _log.debug(
                "auth: allowed (@login_not_required) route=%r",
                route_name,
            )
            return await call_next(request)

        login_url = "{url}?{query_params}".format(
            url=request.url_for(request.app.state.ROUTE_NAME + ":login"),
            query_params=urlencode({"next": str(request.url)}),
        )
        _log.warning(
            "auth: unauthenticated, redirecting to login: %s %s -> %s from %s",
            request.method,
            request.url.path,
            login_url,
            request.client.host if request.client else "unknown",
        )
        return RedirectResponse(login_url, status_code=HTTP_303_SEE_OTHER)
