from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import BaseAdmin as Admin
from starlette_admin import CustomView
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


class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
