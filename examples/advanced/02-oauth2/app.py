"""
02-oauth2: OAuth2 / OIDC sign-in with Authlib.

Set OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, and OAUTH_SERVER_METADATA_URL
(see README), run the app, and click "Login". You will be redirected to your
OIDC provider; on success you land back in the admin with your name and avatar
pulled from the token's userinfo claim.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from authlib.integrations.starlette_client import OAuth
from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.datastructures import URL
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin.auth import AdminUser, OAuthProvider
from starlette_admin.contrib.sqla import Admin, ModelView

# ── Configuration ──────────────────────────────────────────────────────────────

CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")
# OIDC discovery URL, Auth0: https://{your-domain}.auth0.com/.well-known/openid-configuration
SERVER_METADATA_URL = os.environ.get(
    "OAUTH_SERVER_METADATA_URL",
    "",
)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

DATABASE_FILE = "advanced_02_oauth2.sqlite"

# ── OAuth2 client ──────────────────────────────────────────────────────────────

_oauth = OAuth()
_oauth.register(
    "provider",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=SERVER_METADATA_URL,
)

# ── Database ───────────────────────────────────────────────────────────────────

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


# ── Auth provider ──────────────────────────────────────────────────────────────


class OIDCAuthProvider(OAuthProvider):
    """
    Wires the OAuthProvider hooks to Authlib's starlette client.

    Three methods do all the work:
      redirect_to_provider : returns a redirect response to the provider's
                             authorization URL to start the OAuth2 flow.
      handle_callback      : called when the browser returns with the auth code;
                             exchanges it for tokens and stores userinfo in the
                             encrypted session cookie.
      authenticate         : called on every request; reads the session to decide
                             whether the request is authenticated.
    """

    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        client = _oauth.create_client("provider")
        return await client.authorize_redirect(request, callback_url)

    async def handle_callback(self, request: Request) -> None:
        client = _oauth.create_client("provider")
        token = await client.authorize_access_token(request)
        # Persist userinfo in the encrypted session cookie.
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            name = user.get("name") or user.get("email") or "Authenticated User"
            return AdminUser(username=name, photo_url=user.get("picture"))
        return None

    async def logout(self, request: Request) -> Response | None:
        request.session.clear()
        client = _oauth.create_client("provider")
        metadata = await client.load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = str(
                URL(end_session_endpoint).include_query_params(
                    post_logout_redirect_uri="https://www.google.com/",
                    client_id=CLIENT_ID,
                )
            )
            return RedirectResponse(logout_url, status_code=HTTP_303_SEE_OTHER)
        return None


# ── Admin views ────────────────────────────────────────────────────────────────


class PostView(ModelView):
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    fields_default_sort = [("created_at", True)]


# ── App setup ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    first_run = not os.path.exists(DATABASE_FILE)
    Base.metadata.create_all(engine)
    if first_run:
        from seed import seed

        with Session(engine) as session:
            seed(session)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>OAuth2 example</h2>"
                "<p>Sign in via your OIDC provider to access the admin.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

# SessionMiddleware is required: Authlib uses the session to store the OAuth
# state nonce between the redirect and the callback, and we use it to persist
# the userinfo after a successful login.
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = Admin(
    engine,
    title="Example: OAuth2",
    auth_provider=OIDCAuthProvider(),
    secret_key=SECRET_KEY,
)

admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../../.."])
