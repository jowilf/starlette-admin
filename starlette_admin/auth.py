from dataclasses import dataclass
from typing import Optional, Sequence
from urllib.parse import urlencode

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette.types import ASGIApp
from starlette_admin.exceptions import LoginFailed


@dataclass
class AdminUser:
    username: str = "admin"
    photo_url: Optional[str] = None


class AuthProvider:
    """
    Base class for implementing the Authentication into your admin interface.
    You need to inherit this class and override the methods:
    `login`, `logout` and `is_authenticated`.
    """

    def __init__(
        self, login_path: str = "/login", logout_path: str = "/logout"
    ) -> None:
        self.login_path = login_path
        self.logout_path = logout_path

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """
        Implement login logic here and return the response back
        Raises:
            FormValidationError
            LoginFailed
        """
        raise LoginFailed("Not Implemented")

    async def is_authenticated(self, request: Request) -> bool:
        """Implement authentication logic here.
        This method will be called for each incoming request
        to validate the session.
        """
        return False

    def get_admin_user(self, request: Request) -> AdminUser:
        """
        Return the connected user info
        """
        return AdminUser()

    async def logout(self, request: Request, response: Response) -> Response:
        """Implement logout logic here and return the response back"""
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
            ]
        )  # Allow static files needed for the login page

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
        else:
            return await call_next(request)
