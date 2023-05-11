from dataclasses import dataclass, field
from typing import Optional, Sequence
from urllib.parse import urlencode

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette.types import ASGIApp
from starlette_admin.exceptions import LoginFailed
from starlette_admin.i18n import lazy_gettext as _


@dataclass
class AdminUser:
    username: str = field(default_factory=lambda: _("Administrator"))
    photo_url: Optional[str] = None


class AuthProvider:
    """
    Base class for implementing the Authentication into your admin interface

    Args:
        login_path: The path for the login page.
        logout_path: The path for the logout page.
        allow_paths: A list of paths that are allowed without authentication.

    """

    def __init__(
        self,
        login_path: str = "/login",
        logout_path: str = "/logout",
        allow_paths: Optional[Sequence[str]] = None,
    ) -> None:
        self.login_path = login_path
        self.logout_path = logout_path
        self.allow_paths = allow_paths

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """
        This method will be called to validate user credentials

        Returns:
            response: return the response back

        Raises:
            FormValidationError: when form values is not valid
            LoginFailed: to display general error

        Examples:
            ```python
            async def login(
                self,
                username: str,
                password: str,
                remember_me: bool,
                request: Request,
                response: Response,
            ) -> Response:
                if len(username) < 3:
                    # Form data validation
                    raise FormValidationError(
                        {"username": "Ensure username has at least 03 characters"}
                    )

                if username in my_users_db and password == "password":
                    # Save username in session
                    request.session.update({"username": username})
                    return response

                raise LoginFailed("Invalid username or password")
            ```
        """
        raise LoginFailed("Not Implemented")

    async def is_authenticated(self, request: Request) -> bool:
        """
        This method will be called to validate each incoming request.
        You can also save the connected user information into the
        request state and use it later to restrict access to some part
        of your admin interface

        Returns:
            True: to accept the request
            False: to redirect to login page

        Examples:
            ```python
            async def is_authenticated(self, request: Request) -> bool:
                if request.session.get("username", None) in users:
                    # Save user object in state
                    request.state.user = my_users_db.get(request.session["username"])
                    return True
                return False
            ```
        """
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        """
        Override this method to display connected user `name` and/or `profile`

        Returns:
            AdminUser: The connected user info

        Examples:
            ```python
            def get_admin_user(self, request: Request) -> AdminUser:
                user = request.state.user  # Retrieve current user (previously save in state)
                return AdminUser(username=user["name"], photo_url=user["photo_url"])
            ```
        """
        return None  # pragma: no cover

    async def logout(self, request: Request, response: Response) -> Response:
        """
        Implement logout logic (clear sessions, cookies, ...) here
        and return the response back

        Returns:
            response: return the response back

        Examples:
            ```python
            async def logout(self, request: Request, response: Response) -> Response:
                request.session.clear()
                return response
            ```
        """
        raise NotImplementedError()


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        provider: AuthProvider,
        allow_paths: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(app)
        self.provider = provider
        self.allow_paths = list(allow_paths) if allow_paths is not None else []
        self.allow_paths.extend(
            [
                self.provider.login_path,
                "/statics/css/tabler.min.css",
                "/statics/css/fontawesome.min.css",
                "/statics/js/vendor/jquery.min.js",
                "/statics/js/vendor/tabler.min.js",
                "/statics/js/vendor/js.cookie.min.js",
            ]
        )  # Allow static files needed for the login page
        self.allow_paths.extend(
            self.provider.allow_paths if self.provider.allow_paths is not None else []
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.scope["path"] not in self.allow_paths and not (
            await self.provider.is_authenticated(request)
        ):
            return RedirectResponse(
                "{url}?{query_params}".format(
                    url=request.url_for(request.app.state.ROUTE_NAME + ":login"),
                    query_params=urlencode({"next": str(request.url)}),
                ),
                status_code=HTTP_303_SEE_OTHER,
            )
        return await call_next(request)
