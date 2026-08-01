---
title: Authentication
description: Implement authentication in starlette-admin using AuthProvider or integrate with OAuth to secure your dashboard.
---

# Authentication

You protect the admin interface by implementing a single method:

```python
async def authenticate(request) -> AdminUser | None
```

Every protected admin request is processed through this method. If it returns an `AdminUser`, the request is treated as authenticated. If it returns `None`, the request is treated as unauthenticated and handled by the configured login or OAuth flow.

When authentication succeeds, the returned `AdminUser` is stored on:

```python
request.state.admin_user
```

When authentication fails, the request is marked as anonymous:

```python
request.state.is_anonymous = True
```

This allows public or partially protected routes to distinguish between authenticated and unauthenticated requests without triggering a login flow.


## Choose an Authentication Provider

| Provider | When to Use | What You Implement |
| --- | --- | --- |
| `AuthProvider` | You want the built-in login page and to check credentials yourself. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | You want an OAuth2/OIDC redirect flow (Auth0, Okta, Google, etc.). | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Both subclass `BaseAuthProvider` and share the same contract. The `authenticate()` method runs on every request. Whatever it returns becomes `request.state.admin_user`, or if it returns `None`, the framework sets `request.state.is_anonymous = True`.

## `AuthProvider`: Built-In Login Page

Use this provider when you want the framework to render and handle the login form while you handle the credential verification. The framework owns the template, the POST handling, and the redirect.

Here is a complete example:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin

SECRET = "change-me-in-production"

# Demo user store: replace with a real lookup against your database
USERS = {"admin": {"name": "Administrator", "password": "password"}}


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return AdminUser(username=user["name"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


engine = create_engine("sqlite:///admin.sqlite")
app = Starlette(middleware=[Middleware(SessionMiddleware, secret_key=SECRET)])
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key=SECRET
)
admin.mount_to(app)
```

### Required Methods

To build your `AuthProvider`, you must implement three specific methods. `SessionMiddleware` is strictly required here so you can persist the user's logged-in state between requests.

#### `login()`

This method processes the form submission. It receives the `username`, `password`, a `remember_me` boolean, and the current `request`.

* **On success:** Write an identifier (like a user ID or username) to `request.session`, then either return `None` to let the framework redirect to `next` (or the admin index), or return a `Response` yourself to redirect somewhere custom.
* **On failure:** Raise `LoginFailed("message")` to display an error natively above the form, or raise `FormValidationError({"username": "..."})` to mark a specific field as invalid.

#### `authenticate()`

This method runs on *every single request* to a protected admin route. It receives the `request` object.

* Read the identifier you saved in `request.session` during the `login()` step.
* Look up the user in your database.
* If the user exists and is valid, return an instance of `AdminUser`.
* If the user does not exist or is not logged in, return `None`.

#### `logout()`

This method handles the logout sequence. It receives the `request` object. You should clear the user's data from `request.session` to revoke their access. Return `None` to fall back to the default redirect to the admin index, or return a `Response` to redirect somewhere custom.

## `OAuthProvider`: OAuth2/OIDC Redirect Flow


`OAuthProvider` is used when authentication is delegated to an external identity provider such as Auth0, Okta, Google, or Azure AD.

Unlike `AuthProvider`, which handles a username/password form inside the admin, `OAuthProvider` uses a redirect-based flow:

1. Redirect the user to the identity provider
2. The provider authenticates the user
3. The provider redirects back to your application
4. The application exchanges the callback for user identity
5. `authenticate()` restores the user from the session

### Callback URL Setup (Required)

Before implementing `OAuthProvider`, you must register your application’s callback URL in your identity provider dashboard.

OAuth providers only redirect to pre-approved URLs for security reasons.

#### Example callback URL

```text
https://your-domain.com/admin/oauth/callback
```

#### Local development

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    The exact callback URL depends on your configuration. It is constructed from the `route_name` used when mounting `Admin`, combined with the provider’s `callback_path`.

    For example, the default setup uses:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    This results in a callback URL like:

    ```text
    /admin/oauth/callback
    ```

    When deployed, this becomes:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    If you change either the mount prefix or the provider callback path, the resulting URL will change accordingly and must be updated in your OAuth provider configuration.

### Required Methods

Building an `OAuthProvider` relies on the same session-backed pattern as `AuthProvider`, but splits the login process into a redirect and a callback.

#### `redirect_to_provider()`

This method initiates the OAuth flow. It receives the `request` and a dynamically generated `callback_url`. You must return a `Response` that redirects the user's browser to your authentication provider.

#### `handle_callback()`

This method executes when the browser returns from the provider with an authorization code. It receives the `request`. Exchange the code for an access token, fetch the user's profile information, and store their identity in `request.session`.

#### `authenticate()`

Just like with `AuthProvider`, this method reads back whatever `handle_callback()` stored in the session. Return an `AdminUser` if the session contains valid user data, or return `None` if it does not.

#### `logout()`

Clear the session data. If you need to log the user out of the central identity provider entirely (OIDC RP-initiated logout), override this method to return a redirect `Response` pointing to the provider's end-session endpoint instead of returning `None`.

Here is a complete example:

```python
import os

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin.auth import AdminUser, OAuthProvider

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")

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


class Auth0Provider(OAuthProvider):
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        client = oauth.create_client("auth0")
        return await client.authorize_redirect(request, callback_url)

    async def handle_callback(self, request: Request) -> None:
        client = oauth.create_client("auth0")
        token = await client.authorize_access_token(request)
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            return AdminUser(username=user["name"], photo_url=user.get("picture"))
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()
        client = oauth.create_client("auth0")
        metadata = await client.load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = str(
                URL(end_session_endpoint).include_query_params(
                    post_logout_redirect_uri="https://www.google.com/",
                    client_id=AUTH0_CLIENT_ID,
                )
            )
            return RedirectResponse(logout_url, status_code=HTTP_303_SEE_OTHER)
        return None


SECRET_KEY = "change-me"
engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
# required because Auth0Provider's handle_callback/authenticate methods use request.session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = Admin(
    engine, title="My Admin", auth_provider=Auth0Provider(), secret_key=SECRET_KEY
)
admin.mount_to(app)
```

## Register the Provider

Once you have implemented an authentication provider, you must attach it to the Admin instance.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

That single initialization is the entire integration. `Admin` mounts the provider's `AuthMiddleware` ahead of every admin route and adds the provider's routes (login, logout, and the callback for `OAuthProvider`) inside the admin prefix.

## Permission Checks

Authentication answers "Who is this?", while permissions answer "What can they do?". Handling permissions is entirely the responsibility of the view. Building role-based access requires three steps:

1. Subclass `AdminUser` (which is a plain dataclass) to include a `roles` list.
2. Return that subclass from your provider's `authenticate()` method, populated from your user store.
3. Read `request.state.admin_user.roles` back inside the view's permission hooks.

```python
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette_admin import action, row_action
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField
from starlette_admin.types import RequestAction

# Demo user store: replace with a real lookup against your database
USERS = {
    "admin": {
        "name": "Administrator",
        "password": "password",
        "roles": ["read", "create", "edit", "delete", "read_body", "publish"],
    },
    "editor": {
        "name": "Editor",
        "password": "password",
        "roles": ["read", "create", "edit", "read_body", "publish"],
    },
    "viewer": {"name": "Viewer", "password": "password", "roles": ["read"]},
}


# Step 1: AdminUser is a plain dataclass, so subclassing it to add `roles` is
# the intended pattern rather than a workaround.
@dataclass
class MyAdminUser(AdminUser):
    roles: list[str] = field(default_factory=list)


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    # Step 2: authenticate() looks up the roles for the logged-in user and
    # returns them on a MyAdminUser instead of a plain AdminUser.
    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return MyAdminUser(username=user["name"], roles=user["roles"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# Step 3: Every hook below reads request.state.admin_user.roles, which is
# populated strictly because authenticate() returned a MyAdminUser.
class ArticleView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return "read" in request.state.admin_user.roles  # Hides the view entirely

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.admin_user.roles

    def can_access_field(
        self, request: Request, field: BaseField, action: RequestAction | None = None
    ) -> bool:
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field, action)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "publish":
            return "publish" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)
```

Wire `MyAuthProvider` up exactly like any other provider using `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. Every hook mentioned above will then have access to `request.state.admin_user.roles` for verification.

The `is_accessible()` method (available on every `BaseView`) hides the entire view, including its entry in the sidebar. Methods like `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import`, and `can_view_detail` gate individual actions on a `ModelView`. Furthermore, `can_access_field` hides specific fields, while `is_action_allowed` and `is_row_action_allowed` restrict bulk and row actions. For row actions that must be allowed or denied per record rather than globally, for example hiding `publish` once an article is already published, override `is_row_action_allowed_for_obj(request, name, obj)` instead; it receives the row's underlying object and defaults to `is_row_action_allowed`.

See [Views](views.md) and [Actions](actions.md) for the complete API reference. A full working version containing `can_export`, `can_import`, and a row action is available in [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Some routes need to remain public even behind an otherwise locked-down admin panel, such as a self-service registration form or a health check. Decorate the specific endpoint, and `AuthMiddleware` will let the request through without verifying a valid `authenticate()` result:

```python
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import CustomView, route
from starlette_admin.auth import login_not_required


class AccountsView(CustomView):
    menu_label = "Accounts"
    path = "/accounts"

    @route("/register", methods=["GET", "POST"], name="register")
    @login_not_required
    async def register(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                request=request, name="register.html", context={}
            )
        form = await request.form()
        # Create the user account before granting access to the panel
        await create_user(email=form["email"], password=form["password"])
        return RedirectResponse(request.url_for("admin:login"), status_code=302)
```

Both `@route` and `@login_not_required` tag the function with an attribute and return it unchanged. Consequently, the stacking order of these decorators does not matter.

## `allow_routes`

Using `allow_routes` on any provider achieves the exact same bypass logic at the route-name level instead of the function level. This is highly useful when you do not own the endpoint definition or prefer to keep your bypass list visible in one central location:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

The string passed corresponds to the route's name: either the method name, or the value you passed to the `name=` parameter in `@route`, as in `name="register"` in the example above. `AuthMiddleware` will always allow `"login"` and `"static"` in addition to whatever custom routes you list here.

## `AdminUser`

Whatever object `authenticate()` returns ultimately populates `request.state.admin_user`. The application's top bar reads two fields off it directly:

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (translatable) | The name displayed in the top-bar user menu. |
| `photo_url` | `str | None` | `None` | The avatar image URL. This falls back to a placeholder icon when unset. |

Because `AdminUser` is a plain `@dataclass`, subclassing it to carry roles, a tenant ID, or anything else your permission hooks require is the intended pattern. The `MyAdminUser` implementation above demonstrates this approach natively.

---

**What's Next**

* [Security](security.md): CSRF, secret keys, and what the framework protects automatically.
* [Views](views.md): `can_create`, `can_edit`, `can_delete`, and the complete list of permission hooks.
* [Actions](actions.md): `is_action_allowed` and `is_row_action_allowed` for bulk and row action management.
