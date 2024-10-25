from typing import Optional

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette_admin import BaseAdmin
from starlette_admin.auth import (
    AdminConfig,
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
        response: Response,
    ) -> Response:
        if len(username) < 3:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )
        if username in users and password == "password":
            response.set_cookie(key="session", value=username)
            return response
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if "session" in request.cookies:
            username = request.cookies.get("session")
            user_roles = users.get(username)
            if user_roles is not None:
                """Save user roles in request state, can be use later,
                to restrict user actions in admin interface"""
                request.state.user = username
                request.state.user_roles = user_roles
                return True
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        return AdminUser(request.state.user)

    def get_admin_config(self, request: Request) -> Optional[AdminConfig]:
        return AdminConfig(app_title=f"Welcome {request.state.user}!")

    async def logout(self, request: Request, response: Response):
        response.delete_cookie("session")
        return response

    @login_not_required
    async def public_route_async(self, request: Request):
        return PlainTextResponse("async public route")

    @login_not_required
    def public_route_sync(self, request: Request):
        return PlainTextResponse("sync public route")

    def setup_admin(self, admin: "BaseAdmin"):
        super().setup_admin(admin)
        admin.routes.extend(
            [
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
        )
