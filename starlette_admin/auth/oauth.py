from abc import abstractmethod

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates
from starlette_admin.auth.base import BaseAuthProvider, login_not_required
from starlette_admin.helpers import index_url, safe_redirect_url
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


class OAuthProvider(BaseAuthProvider):
    """
    Subclass to use an OAuth2/OIDC flow.

    Implement `redirect_to_provider`, `handle_callback`, and `authenticate`.
    `get_routes()` returns the login redirect, logout, and callback routes.
    The callback is automatically added to `allow_routes` so the middleware
    never blocks it.

    Requires `SessionMiddleware`: the OAuth client stores the state nonce in the
    session between the redirect and the callback.

    Examples:
        ```python
        from authlib.integrations.starlette_client import OAuth

        oauth = OAuth()
        oauth.register(
            "provider",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client_kwargs={"scope": "openid profile email"},
            server_metadata_url=SERVER_METADATA_URL,
        )


        class OIDCAuthProvider(OAuthProvider):
            async def redirect_to_provider(self, request: Request, callback_url: str) -> Response:
                client = oauth.create_client("provider")
                return await client.authorize_redirect(request, callback_url)

            async def handle_callback(self, request: Request) -> None:
                client = oauth.create_client("provider")
                token = await client.authorize_access_token(request)
                # Persist userinfo in the encrypted session cookie.
                request.session["user"] = dict(token["userinfo"])

            async def authenticate(self, request: Request) -> AdminUser | None:
                user = request.session.get("user")
                if user:
                    return AdminUser(
                        username=user.get("name") or user.get("email"),
                        photo_url=user.get("picture"),
                    )
                return None

            async def logout(self, request: Request) -> Response | None:
                request.session.clear()
                # Return a Response to redirect to the provider's end_session_endpoint,
                # or None to fall back to the default admin index redirect.
                return None
        ```
    """

    def __init__(
        self,
        login_path: str = "/login",
        logout_path: str = "/logout",
        callback_path: str = "/oauth/callback",
        allow_routes: list[str] | None = None,
    ) -> None:
        super().__init__(login_path, logout_path, allow_routes)
        self.callback_path = callback_path
        # The callback is always public: the OAuth provider redirects here from
        # outside the app, before a session exists.
        self.allow_routes.append("oauth_callback")

    @abstractmethod
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        """Return a redirect response to start the OAuth2 flow."""

    @abstractmethod
    async def handle_callback(self, request: Request) -> None:
        """Exchange the authorization code and write auth state (e.g. to session)."""

    async def logout(self, request: Request) -> Response | None:
        """Clear auth state on logout.

        Returns:
            A `Response` to redirect to a custom URL (e.g. the OIDC
            `end_session_endpoint`), or `None` to use the default index redirect.
        """
        return None

    async def render_login(self, request: Request) -> Response:
        """Redirect to the OAuth provider's authorization URL."""
        route_name = request.app.state.ROUTE_NAME
        callback_url = request.url_for(route_name + ":oauth_callback")
        if next_url := request.query_params.get("next"):
            callback_url = callback_url.include_query_params(next=next_url)
        return await self.redirect_to_provider(request, str(callback_url))

    async def render_logout(self, request: Request) -> Response:
        """Call `logout()`, then redirect to its result or to the admin index."""
        result = await self.logout(request)
        return (
            RedirectResponse(
                index_url(request),
                status_code=HTTP_303_SEE_OTHER,
            )
            if result is None
            else result
        )

    @login_not_required
    async def render_callback(self, request: Request) -> Response:
        """Handle the OAuth callback, then redirect to next or the admin index."""
        await self.handle_callback(request)
        await self._emit_after_login(request, await self.authenticate(request))
        fallback = index_url(request)
        next_url = safe_redirect_url(
            request.query_params.get("next") or fallback,
            request,
            fallback,
        )
        return RedirectResponse(next_url, status_code=HTTP_303_SEE_OTHER)

    def get_routes(self, templates: Jinja2Templates) -> list[Route]:
        return [
            Route(self.login_path, self.render_login, methods=["GET"], name="login"),
            Route(
                self.logout_path, self.render_logout, methods=["POST"], name="logout"
            ),
            Route(
                self.callback_path,
                self.render_callback,
                methods=["GET"],
                name="oauth_callback",
            ),
        ]
