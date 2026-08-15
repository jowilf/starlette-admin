# Authentication and permissions

There is no built-in user model. The contract is one method: `authenticate(request) -> AdminUser | None`, run on every protected request. An `AdminUser` return authenticates the request and populates `request.state.admin_user`; `None` marks it anonymous (`request.state.is_anonymous = True`) and triggers the login or OAuth flow.

| Provider | Use when | Implement |
| --- | --- | --- |
| `AuthProvider` | Built-in login page, you verify credentials | `login()`, `authenticate()`, `logout()` |
| `OAuthProvider` | Redirect flow to Auth0, Okta, Google, Azure AD | `redirect_to_provider()`, `handle_callback()`, `authenticate()`, `logout()` |

Both subclass `BaseAuthProvider`. Both persist login state in `request.session`, so the host app MUST add `SessionMiddleware`.

## AuthProvider (built-in login page)

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin

SECRET = "change-me-in-production"


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = lookup_user(username)
        if user and verify_password(password, user):
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = lookup_user(request.session.get("username"))
        return AdminUser(username=user.name) if user else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


app = Starlette(middleware=[Middleware(SessionMiddleware, secret_key=SECRET)])
admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)
admin.mount_to(app)
```

`login()` failure options: `raise LoginFailed("message")` for a banner above the form, or `raise FormValidationError({"username": "..."})` to flag a specific field.

## OAuthProvider (OAuth2/OIDC)

Redirect flow: `redirect_to_provider(request, callback_url)` returns a redirect `Response`; `handle_callback(request)` exchanges the code, fetches the profile, and stores identity in `request.session`; `authenticate()` reads it back. For provider-side logout, `logout()` may return a `RedirectResponse` to the end-session endpoint.

Register the callback URL in the provider dashboard: `{scheme}://{host}{base_url}/oauth/callback` (default `/admin/oauth/callback`; it follows `route_name` and the provider's `callback_path`).

```python
from authlib.integrations.starlette_client import OAuth
from starlette_admin.auth import AdminUser, OAuthProvider

oauth = OAuth()
oauth.register("auth0", client_id=..., client_secret=...,
               client_kwargs={"scope": "openid profile email"},
               server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration")


class Auth0Provider(OAuthProvider):
    async def redirect_to_provider(self, request, callback_url):
        return await oauth.create_client("auth0").authorize_redirect(request, callback_url)

    async def handle_callback(self, request) -> None:
        token = await oauth.create_client("auth0").authorize_access_token(request)
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            return AdminUser(username=user["name"], photo_url=user.get("picture"))
        return None

    async def logout(self, request) -> None:
        request.session.clear()
```

## Role-based permissions

`AdminUser` is a plain dataclass (`username`, `photo_url`). Subclassing it to carry roles or a tenant id is the intended pattern:

```python
from dataclasses import dataclass, field

@dataclass
class MyAdminUser(AdminUser):
    roles: list[str] = field(default_factory=list)
```

Return `MyAdminUser(username=..., roles=...)` from `authenticate()`, then read `request.state.admin_user.roles` in view hooks:

```python
class ArticleView(ModelView):
    def is_accessible(self, request) -> bool:          # hides the view entirely
        return "read" in request.state.admin_user.roles

    def can_create(self, request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_access_field(self, request, field) -> bool:  # hide specific fields
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field)

    async def is_action_allowed(self, request, name: str) -> bool:  # gate batch actions
        if name == "publish":
            return "publish" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)
```

Also available: `can_edit`, `can_delete`, `can_view_detail`, `can_export`, `can_import`, `is_row_action_allowed(request, name)`, and per-record `is_row_action_allowed_for_obj(request, name, obj)`. Always call `super()` for names an override does not handle; the built-in view/edit/delete row actions rely on it.

Runnable example: `examples/03-auth`.

## Public routes inside a locked admin

Two equivalent mechanisms:

```python
from starlette_admin import CustomView, route
from starlette_admin.auth import login_not_required


class AccountsView(CustomView):
    @route("/register", methods=["GET", "POST"], name="register")
    @login_not_required            # decorator order does not matter
    async def register(self, request): ...
```

Or at the provider level, by route name: `MyAuthProvider(allow_routes=["register"])`. `"login"` and `"static"` are always allowed.
