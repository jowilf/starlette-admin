from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_303_SEE_OTHER, HTTP_400_BAD_REQUEST
from starlette.templating import Jinja2Templates
from starlette_admin.auth.base import AdminUser, BaseAuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from starlette_admin.helpers import (
    HTTP_422,
    index_url,
    safe_redirect_url,
    wrap_endpoint_with_kwargs,
)
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


class AuthProvider(BaseAuthProvider):
    """
    Subclass to use the built-in username/password login page.

    Implement `login`, `logout`, and `authenticate` only;
    the framework owns the form, rendering, and redirect.
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
    ) -> Response | None:
        """
        Validate credentials and persist auth state (e.g. write to request.session).

        Raise `LoginFailed` for wrong credentials, or `FormValidationError` to mark
        specific form fields invalid.

        Returns:
            A `Response` to redirect to a custom URL, or `None` to fall back to the
            default redirect (`next` query param, or the admin index).

        Examples:
            ```python
            async def login(self, username, password, remember_me, request):
                user = await db.get_user(username)
                if user and verify_password(password, user.hashed_password):
                    request.session["user_id"] = user.id
                    return
                raise LoginFailed("Invalid username or password")
            ```
        """
        raise LoginFailed("Not Implemented")

    async def logout(self, request: Request) -> Response | None:
        """
        Clear auth state (e.g. request.session.clear()).

        Returns:
            A `Response` to redirect to a custom URL, or `None` to fall back to the
            default redirect (the admin index).

        Examples:
            ```python
            async def logout(self, request):
                request.session.clear()
            ```
        """
        raise NotImplementedError()

    async def authenticate(self, request: Request) -> AdminUser | None:
        return None

    async def render_login(
        self, request: Request, templates: Jinja2Templates
    ) -> Response:
        """Render and handle the built-in username/password login page."""
        if getattr(request.state, "admin_user", None) is not None:
            fallback = index_url(request)
            next_url = safe_redirect_url(
                request.query_params.get("next") or fallback,
                request,
                fallback,
            )
            _log.debug(
                "login page: already authenticated, redirecting to %s",
                request.client.host if request.client else "unknown",
            )
            return RedirectResponse(
                next_url,
                status_code=HTTP_303_SEE_OTHER,
            )
        if request.method == "GET":
            _log.debug(
                "login page: GET %s from %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return templates.TemplateResponse(
                request=request,
                name="login.html",
            )

        form = await request.form()
        username = str(form.get("username") or "")
        remember_me = form.get("remember_me") == "on"
        fallback = index_url(request)
        next_url = safe_redirect_url(
            request.query_params.get("next") or fallback,
            request,
            fallback,
        )
        _log.info(
            "login attempt: username=%r remember_me=%s next=%r from %s",
            username,
            remember_me,
            next_url,
            request.client.host if request.client else "unknown",
        )
        try:
            result = await self.login(
                username,
                str(form.get("password") or ""),
                remember_me,
                request,
            )
            _log.info(
                "login success: username=%r redirect_to=%r from %s",
                username,
                next_url,
                request.client.host if request.client else "unknown",
            )
            await self._emit_after_login(request, await self.authenticate(request))
            return result or RedirectResponse(next_url, status_code=HTTP_303_SEE_OTHER)
        except FormValidationError as errors:
            _log.warning(
                "login form invalid: username=%r fields=%r from %s",
                username,
                list(errors.errors.keys()),
                request.client.host if request.client else "unknown",
            )
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"form_errors": errors},
                status_code=HTTP_422,
            )
        except LoginFailed as error:
            _log.warning(
                "login failed: username=%r reason=%r from %s",
                username,
                error.msg,
                request.client.host if request.client else "unknown",
            )
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"error": error.msg},
                status_code=HTTP_400_BAD_REQUEST,
            )

    async def render_logout(self, request: Request) -> Response:
        """Call `logout()`, then redirect to the admin index."""
        user = getattr(request.state, "user", None)
        _log.info(
            "logout initiated: user=%r from %s",
            user,
            request.client.host if request.client else "unknown",
        )
        result = await self.logout(request)
        _log.info(
            "logout complete: user=%r from %s",
            user,
            request.client.host if request.client else "unknown",
        )
        return result or RedirectResponse(
            index_url(request),
            status_code=HTTP_303_SEE_OTHER,
        )

    def get_routes(self, templates: Jinja2Templates) -> list[Route]:
        return [
            Route(
                self.login_path,
                wrap_endpoint_with_kwargs(self.render_login, templates=templates),
                methods=["GET", "POST"],
                name="login",
            ),
            Route(
                self.logout_path, self.render_logout, methods=["POST"], name="logout"
            ),
        ]
