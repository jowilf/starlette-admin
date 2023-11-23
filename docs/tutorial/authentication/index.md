# Authentication & Authorization

To protect your admin interface from unwanted users, you can create an Authentication Provider by extending
the [AuthProvider][starlette_admin.auth.AuthProvider] class and set `auth_provider` when declaring your admin app

## Username and Password Authentication

By default, [AuthProvider][starlette_admin.auth.AuthProvider] provides a login form with `username` and `password`
fields for basic username and password authentication. To fully support this authentication method, you need to
implement the following methods in your custom Authentication Provider:

* [is_authenticated][starlette_admin.auth.BaseAuthProvider.is_authenticated]: This method will be called to validate
  each incoming request.
* [get_admin_user][starlette_admin.auth.BaseAuthProvider.get_admin_user]: Return connected user `name` and/or `avatar`
* [get_admin_config][starlette_admin.auth.BaseAuthProvider.get_admin_config]: Return `logo_url` or `app_title` according to connected user or any other condition.
* [login][starlette_admin.auth.AuthProvider.login]: will be called to validate user credentials.
* [logout][starlette_admin.auth.AuthProvider.logout]: Will be called to logout (clear sessions, cookies, ...)

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

users = {
    "admin": {
        "name": "Admin",
        "avatar": "admin.png",
        "company_logo_url": "admin.png",
        "roles": ["read", "create", "edit", "delete", "action_make_published"],
    },
    "johndoe": {
        "name": "John Doe",
        "avatar": None, # user avatar is optional
        "roles": ["read", "create", "edit", "action_make_published"],
    },
    "viewer": {"name": "Viewer", "avatar": "guest.png", "roles": ["read"]},
}


class UsernameAndPasswordProvider(AuthProvider):
    """
    This is only for demo purpose, it's not a better
    way to save and validate user credentials
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            """Form data validation"""
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )

        if username in users and password == "password":
            """Save `username` in session"""
            request.session.update({"username": username})
            return response

        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if request.session.get("username", None) in users:
            """
            Save current `user` object in the request state. Can be used later
            to restrict access to connected user.
            """
            request.state.user = users.get(request.session["username"])
            return True

        return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = request.state.user  # Retrieve current user
        # Update app title according to current_user
        custom_app_title = "Hello, " + user["name"] + "!"
        # Update logo url according to current_user
        custom_logo_url = None
        if user.get("company_logo_url", None):
            custom_logo_url = request.url_for("static", path=user["company_logo_url"])
        return AdminConfig(
            app_title=custom_app_title,
            logo_url=custom_logo_url,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Retrieve current user
        photo_url = None
        if user["avatar"] is not None:
            photo_url = request.url_for("static", path=user["avatar"])
        return AdminUser(username=user["name"], photo_url=photo_url)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response

```

For a working example, have a look
at [`https://github.com/jowilf/starlette-admin/tree/main/examples/auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/auth)

## Custom Authentication flow (OAuth2/OIDC, ...)

If you prefer to use a custom authentication flow, such as OAuth2 or OIDC, you can implement the following methods in
your custom Authentication Provider:

* [is_authenticated][starlette_admin.auth.BaseAuthProvider.is_authenticated]: This method will be called to validate each incoming request.
* [get_admin_user][starlette_admin.auth.BaseAuthProvider.get_admin_user]: Return connected user `name` and/or `profile`
* [render_login][starlette_admin.auth.AuthProvider.render_login]: Override the default behavior to render a custom login page.
* [render_logout][starlette_admin.auth.AuthProvider.render_logout]: Implement the custom logout logic.

Additionally, you can override these methods depending on your needs:

* [get_middleware][starlette_admin.auth.BaseAuthProvider.get_middleware]: To provide a custom authentication middleware
  for the admin interface
* [setup_admin][starlette_admin.auth.BaseAuthProvider.setup_admin]: This method is called during the setup process of
  the admin interface and allows for custom configuration and setup.

```python
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

```

For a working example, have a look
at [`https://github.com/jowilf/starlette-admin/tree/main/examples/authlib`](https://github.com/jowilf/starlette-admin/tree/main/examples/authlib)

The AuthProvider can be added at your admin interface as follows:

```python
admin = Admin(
    engine,
    title="Example: Authentication",
    auth_provider=MyAuthProvider(),
    middlewares=[Middleware(SessionMiddleware, secret_key=SECRET)],
)
```

## Authorization

### For all views

Each [view][starlette_admin.views.BaseView] implement [is_accessible][starlette_admin.views.BaseView.is_accessible] method which can be used to restrict access
to current user.

```python
from starlette_admin import CustomView
from starlette.requests import Request

class ReportView(CustomView):

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user["roles"]
```
!!! important
    When view is inaccessible, it does not appear in menu structure

### For [ModelView][starlette_admin.views.BaseModelView]

In [ModelView][starlette_admin.views.BaseModelView], you can override the following methods to restrict access to
the current connected user.

* `can_view_details`: Permission for viewing full details of Items
* `can_create`: Permission for creating new Items
* `can_edit`: Permission for editing Items
* `can_delete`: Permission for deleting Items
* `is_action_allowed`:  verify if the action with `name` is allowed.
* `is_row_action_allowed`:  verify if the row action with `name` is allowed.

```python
from starlette_admin.contrib.sqla import ModelView
from starlette.requests import Request
from starlette_admin import action, row_action

class ArticleView(ModelView):
    exclude_fields_from_list = [Article.body]

    def can_view_details(self, request: Request) -> bool:
        return "read" in request.state.user["roles"]

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.user["roles"]

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.user["roles"]

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.user["roles"]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "action_make_published" in request.state.user["roles"]
        return await super().is_action_allowed(request, name)

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "row_action_make_published" in request.state.user["roles"]
        return await super().is_row_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        ...
        return "{} articles were successfully marked as published".format(len(pks))


    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        ...
        return "The article was successfully marked as published"
```
