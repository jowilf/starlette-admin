# Authentication & Authorization

*starlette-admin* provides an optional [AuthProvider][starlette_admin.auth.AuthProvider] class for helping you to protect your admin interface from unwanted users.


## Authentication

To enable authentication in your admin interface, inherit the [AuthProvider][starlette_admin.auth.AuthProvider] class
and set `auth_provider` when declaring your admin app

The class [AuthProvider][starlette_admin.auth.AuthProvider] has sevarals methods you need to override:

* [is_authenticated][starlette_admin.auth.AuthProvider.is_authenticated]: This method will be called to validate each incoming request.
* [get_admin_user][starlette_admin.auth.AuthProvider.get_admin_user]: Return connected user `name` and/or `profile`
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
        "avatar": "avatar.png",
        "roles": ["read", "create", "edit", "delete", "action_make_published"],
    },
    "johndoe": {
        "name": "John Doe",
        "avatar": None, # user avatar is optional
        "roles": ["read", "create", "edit", "action_make_published"],
    },
    "viewer": {"name": "Viewer", "avatar": "guest.png", "roles": ["read"]},
}


class MyAuthProvider(AuthProvider):
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

??? note
    Refer to [demo app](https://github.com/jowilf/starlette-admin-demo) for full example with starlette SessionMiddleware

## Authorization

### For all views

Each [view][starlette_admin.views.BaseView] implement [is_accessible][starlette_admin.views.BaseView.is_accessible] method which can be used to restrict access
to current user.

```python
from starlette_admin import CustomView
from starlette.requests import Request

class ReportView(CustomView):

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
```
!!! important
    When view is inaccessible, it does not appear in menu structure

### For [ModelView][starlette_admin.views.BaseModelView]
In [ModelView][starlette_admin.views.BaseModelView], there is four additional methods you can override
to restrict access to current user.

* `can_view_details`: Permission for viewing full details of Items
* `can_create`: Permission for creating new Items
* `can_edit`: Permission for editing Items
* `can_delete`: Permission for deleting Items
* `is_action_allowed`:  verify if action with `name` is allowed.

```python
from starlette_admin.contrib.sqla import ModelView
from starlette.requests import Request

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
```

## Example

For a working example, have a look at [https://github.com/jowilf/starlette-admin/tree/main/examples/auth](https://github.com/jowilf/starlette-admin/tree/main/examples/auth)
