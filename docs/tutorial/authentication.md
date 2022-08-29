# Authentication & Authorization

By default, *Starlette Admin* does not enforce any authentication to your application, but provides an
optional [AuthProvider][starlette_admin.auth.AuthProvider] you can use.

## Authentication

To enable authentication in your admin interface, inherit the [AuthProvider][starlette_admin.auth.AuthProvider] class
and set `auth_provider` when declaring your admin app

The class [AuthProvider][starlette_admin.auth.AuthProvider] has three methods you need to override:

* [is_authenticated][starlette_admin.auth.AuthProvider.is_authenticated] : Will be called for validating each incoming
  request.
* [login][starlette_admin.auth.AuthProvider.login]: Will be called in the login page to validate username/password.
* [logout][starlette_admin.auth.AuthProvider.logout]: Will be called for the logout

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import BaseAdmin as Admin
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

users = {
    "admin": ["admin"],
    "john": ["post:list", "post:detail"],
    "terry": ["post:list", "post:create", "post:edit"],
    "doe": [""],
}


class MyAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )
        if username in users and password == "password":
            response.set_cookie(key="session", value=username)
            return response
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if "session" in request.cookies:
            user_roles = users.get(request.cookies.get("session"), None)
            if user_roles is not None:
                """Save user roles in request state, can be use later,
                to restrict user actions in admin interface"""
                request.state.user_roles = user_roles
                return True
        return False

    async def logout(self, request: Request, response: Response):
        response.delete_cookie("session")
        return response


admin = Admin(auth_provider=MyAuthProvider())

```

??? note
    Refer to demo app for full example with starlette SessionMiddleware

## Authorization

### For all views

Each [view][starlette_admin.views.BaseView] implement [is_accessible][starlette_admin.views.BaseView.is_accessible] method which can be used to restrict access
to current user.

```python
from starlette_admin import CustomView
from starlette.requests import Request

class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
```
!!! important
    When view is inaccessible, it will not appear in menu structure

### For [ModelView][starlette_admin.views.BaseModelView]
In [ModelView][starlette_admin.views.BaseModelView], there is four additional methods you can override
to restrict access to current user.

* `can_view_details`: Permission for viewing full details of Items
* `can_create`: Permission for creating new Items
* `can_edit`: Permission for editing Items
* `can_delete`: Permission for deleting Items

```python
from starlette_admin.contrib.sqla import ModelView
from starlette.requests import Request

class PostView(ModelView, model=Post):
    pass

    def is_accessible(self, request: Request) -> bool:
        return (
            "admin" in request.state.user_roles
            or "post:list" in request.state.user_roles
        )

    def can_view_details(self, request: Request) -> bool:
        return "post:detail" in request.state.user_roles

    def can_create(self, request: Request) -> bool:
        return "post:create" in request.state.user_roles

    def can_edit(self, request: Request) -> bool:
        return "post:edit" in request.state.user_roles

    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
```

