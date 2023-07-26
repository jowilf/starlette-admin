from typing import Optional

from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import BaseAdmin
from starlette_admin.auth import AdminUser, AuthMiddleware, AuthProvider

from authlib.integrations.starlette_client import OAuth

from .config import AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_DOMAIN

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)


class MyAuthProvider(AuthProvider):
    async def is_authenticated(self, request: Request) -> bool:
        if request.session.get("user", None) is not None:
            request.state.user = request.session.get("user")
            return True
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        user = request.state.user
        return AdminUser(
            username=user["name"],
            photo_url=user["picture"],
        )

    async def render_login(self, request: Request, admin: BaseAdmin):
        """Override the default login behavior to implement custom logic."""
        auth0 = oauth.create_client("auth0")
        redirect_uri = request.url_for(
            admin.route_name + ":authorize_auth0"
        ).include_query_params(next=request.query_params.get("next"))
        return await auth0.authorize_redirect(request, str(redirect_uri))

    async def render_logout(self, request: Request, admin: BaseAdmin) -> Response:
        """Override the default logout to implement custom logic"""
        request.session.clear()
        return RedirectResponse(
            url=URL(f"https://{AUTH0_DOMAIN}/v2/logout").include_query_params(
                returnTo=request.url_for(admin.route_name + ":index"),
                client_id=AUTH0_CLIENT_ID,
            )
        )

    async def handle_auth_callback(self, request: Request):
        auth0 = oauth.create_client("auth0")
        token = await auth0.authorize_access_token(request)
        request.session.update({"user": token["userinfo"]})
        return RedirectResponse(request.query_params.get("next"))

    def setup_admin(self, admin: "BaseAdmin"):
        super().setup_admin(admin)
        """add custom authentication callback route"""
        admin.routes.append(
            Route(
                "/auth0/authorize",
                self.handle_auth_callback,
                methods=["GET"],
                name="authorize_auth0",
            )
        )

    def get_middleware(self, admin: "BaseAdmin") -> Middleware:
        return Middleware(
            AuthMiddleware, provider=self, allow_paths=["/auth0/authorize"]
        )
