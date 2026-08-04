from typing import Any

from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette_admin.auth import (
    AdminUser,
    AuthProvider,
    login_not_required,
)
from starlette_admin.exceptions import FormValidationError, LoginFailed

users = {
    "super-admin": ["admin", "super-admin"],
    "admin": ["admin"],
    "john": ["post:list", "post:detail"],
    "terry": ["post:list", "post:create", "post:edit"],
    "doe": [""],
}


class MyAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
    ) -> None:
        if len(username) < 3:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )
        # WARNING: Plaintext comparison is intentional for this test fixture only.
        # Production `AuthProvider` implementations must hash passwords (e.g., using bcrypt or argon2).
        if username in users and password == "password":
            # Signals `render_login` to set a raw cookie for this test provider.
            request.state._auth_user = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        if "session" in request.cookies:
            username = request.cookies.get("session")
            user_roles = users.get(username)
            if user_roles is not None:
                request.state.user_roles = user_roles
                return AdminUser(username=username)
        return None

    async def logout(self, request: Request) -> None:
        pass  # Cookie deletion is handled in the `render_logout` override.

    async def render_login(
        self, request: Request, templates: Jinja2Templates
    ) -> Response:
        response = await super().render_login(request, templates)
        # After a successful login, set the raw cookie used by `authenticate`.
        if isinstance(response, RedirectResponse):
            user = getattr(request.state, "_auth_user", None)
            if user:
                response.set_cookie("session", user)
        return response

    async def render_logout(self, request: Request) -> Response:
        response = await super().render_logout(request)
        response.delete_cookie("session")
        return response

    @login_not_required
    async def public_route_async(self, request: Request) -> Response:
        return PlainTextResponse("async public route")

    @login_not_required
    def public_route_sync(self, request: Request) -> Response:
        return PlainTextResponse("sync public route")

    def get_routes(self, templates: Any) -> list[Route]:
        return [
            *super().get_routes(templates),
            Route(
                "/public_sync",
                self.public_route_sync,
                methods=["GET"],
                name="public_sync",
            ),
            Route(
                "/public_async",
                self.public_route_async,
                methods=["GET"],
                name="public_async",
            ),
        ]
