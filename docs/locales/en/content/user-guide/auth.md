---
title: Authentication
description: Implement authentication in starlette-admin using AuthProvider or integrate with OAuth to secure your dashboard.
---

# Authentication

You protect the admin interface by implementing a single method:

```python
async def authenticate(request) -> AdminUser | None
```

Every protected admin request goes through this method. When it returns an `AdminUser`, the request is authenticated. When it returns `None`, the request is unauthenticated, and the sign-in or OAuth flow you configured takes over.

On success, the returned `AdminUser` lands on:

```python
request.state.admin_user
```

On failure, the request is marked anonymous:

```python
request.state.is_anonymous = True
```

Public and partially protected routes can then tell authenticated and unauthenticated requests apart without starting a sign-in flow.


## Choose an authentication provider

| Provider | When to use it | What you implement |
| --- | --- | --- |
| `AuthProvider` | You want the built-in sign-in page and you check credentials yourself. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | You want an OAuth2 or OIDC redirect flow, such as Auth0, Okta, or Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Both subclass `BaseAuthProvider` and share the same contract. `authenticate()` runs on every request. What it returns becomes `request.state.admin_user`, and when it returns `None`, the framework sets `request.state.is_anonymous = True`.

## `AuthProvider`: built-in sign-in page

Use this provider when you want the framework to render and handle the sign-in form while you verify the credentials. The framework owns the template, the POST handling, and the redirect.

Here's a complete example:

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

### Required methods

An `AuthProvider` implements three methods. `SessionMiddleware` is required here, because it persists the user's signed-in state between requests.

#### `login()`

This method handles the form submission. It receives the `username`, the `password`, a `remember_me` boolean, and the current `request`.

* **On success:** Write an identifier, such as a user ID or username, to `request.session`. Then return `None` to let the framework redirect to `next` or the admin index, or return a `Response` to redirect somewhere else.
* **On failure:** Raise `LoginFailed("message")` to show an error above the form, or raise `FormValidationError({"username": "..."})` to mark a specific field invalid.

#### `authenticate()`

This method runs on *every* request to a protected admin route. It receives the `request` object.

* Read the identifier you saved in `request.session` during `login()`.
* Look up the user in your database.
* Return an `AdminUser` instance when the user exists and is valid.
* Return `None` when the user doesn't exist or isn't signed in.

#### `logout()`

This method handles sign-out. It receives the `request` object, and you clear the user's data from `request.session` to revoke access. Return `None` for the default redirect to the admin index, or return a `Response` to redirect somewhere else.

## `OAuthProvider`: OAuth2/OIDC redirect flow


Use `OAuthProvider` when you delegate authentication to an external identity provider such as Auth0, Okta, Google, or Microsoft Entra ID.

`AuthProvider` handles a username and password form inside the admin. `OAuthProvider` instead uses a redirect-based flow:

1. Redirect the user to the identity provider.
2. The provider authenticates the user.
3. The provider redirects back to your application.
4. Your application exchanges the callback for the user's identity.
5. `authenticate()` restores the user from the session.

### Callback URL setup (required)

Before you implement `OAuthProvider`, register your application's callback URL in your identity provider's dashboard. For security, OAuth providers redirect only to preapproved URLs.

#### Example callback URL

```text
https://your-domain.com/admin/oauth/callback
```

#### Local development

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Your exact callback URL depends on your configuration. It's built from the `route_name` you use when you mount `Admin`, plus the provider's `callback_path`.

    The default setup uses:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    which produces this callback URL:

    ```text
    /admin/oauth/callback
    ```

    Deployed, it becomes:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    If you change the mount prefix or the provider callback path, the URL changes with it, and you have to update it in your OAuth provider configuration.

### Required methods

An `OAuthProvider` uses the same session-backed pattern as `AuthProvider`, but it splits sign-in into a redirect and a callback.

#### `redirect_to_provider()`

This method starts the OAuth flow. It receives the `request` and a generated `callback_url`, and it must return a `Response` that redirects the user's browser to your identity provider.

#### `handle_callback()`

This method runs when the browser comes back from the provider with an authorization code. It receives the `request`. Exchange the code for an access token, fetch the user's profile, and store their identity in `request.session`.

#### `authenticate()`

As with `AuthProvider`, this method reads back whatever `handle_callback()` stored in the session. Return an `AdminUser` when the session holds valid user data, or `None` when it doesn't.

#### `logout()`

Clear the session data. To sign the user out of the identity provider as well (OIDC RP-initiated logout), override this method and return a redirect `Response` that points to the provider's end-session endpoint instead of returning `None`.

Here's a complete example:

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

## Register the provider

After you implement an authentication provider, attach it to the `Admin` instance.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

That single line is the whole integration. `Admin` mounts the provider's `AuthMiddleware` ahead of every admin route and adds the provider's routes (sign-in, sign-out, and the callback for `OAuthProvider`) inside the admin prefix.

## Permission checks

Authentication answers "Who is this?" Permissions answer "What can they do?" Permissions belong to the view. Role-based access takes three steps:

1. Subclass `AdminUser`, a plain dataclass, to add a `roles` list.
2. Return that subclass from your provider's `authenticate()` method, populated from your user store.
3. Read `request.state.admin_user.roles` in the view's permission hooks.

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

    # Step 2: authenticate() looks up the roles for the signed-in user and
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
# populated only because authenticate() returned a MyAdminUser.
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

Register `MyAuthProvider` like any other provider, with `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. Every hook above then has access to `request.state.admin_user.roles`.

`is_accessible()`, available on every `BaseView`, hides the whole view, including its sidebar entry. `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import`, and `can_view_detail` gate individual operations on a `ModelView`. `can_access_field` hides specific fields, and `is_action_allowed` and `is_row_action_allowed` restrict bulk and row actions. When a row action depends on the record rather than the user, such as hiding `publish` on an article that's already published, override `is_row_action_allowed_for_obj(request, name, obj)` instead. It receives the row's underlying object and falls back to `is_row_action_allowed`.

For the complete API reference, see [Views](views.md) and [Actions](actions.md). A full working version with `can_export`, `can_import`, and a row action is in [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Some routes stay public even in an otherwise locked-down admin panel, such as a self-service registration form or a health check. Decorate the endpoint, and `AuthMiddleware` lets the request through without checking for a valid `authenticate()` result:

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

`@route` and `@login_not_required` both tag the function with an attribute and return it unchanged, so the order you stack them in doesn't matter.

## `allow_routes`

`allow_routes` gives you the same bypass at the route-name level instead of the function level. Use it when you don't own the endpoint definition, or when you want the bypass list in one place:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

The string is the route's name: either the method name, or the value you passed to the `name=` parameter in `@route`, such as `name="register"` above. `AuthMiddleware` always allows `"login"` and `"static"`, on top of the custom routes you list.

## `AdminUser`

Whatever `authenticate()` returns populates `request.state.admin_user`. The top bar reads two fields from it:

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (translatable) | The name shown in the top-bar user menu. |
| `photo_url` | `str | None` | `None` | The avatar image URL. Falls back to a placeholder icon when unset. |

`AdminUser` is a plain `@dataclass`, so subclassing it to carry roles, a tenant ID, or anything else your permission hooks need is the intended pattern. The `MyAdminUser` example above shows it in practice.

---

**What's next**

* [Security](security.md): CSRF, secret keys, and what the framework protects automatically.
* [Views](views.md): `can_create`, `can_edit`, `can_delete`, and the complete list of permission hooks.
* [Actions](actions.md): `is_action_allowed` and `is_row_action_allowed` for bulk and row actions.
