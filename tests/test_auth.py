import json
from dataclasses import dataclass

import pytest
from async_asgi_testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import BaseAdmin, IntegerField, StringField, TextAreaField
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from starlette_admin.views import CustomView

from tests.dummy_model_view import DummyBaseModel, DummyModelView

users = {
    "admin": ["admin"],
    "john": ["post:list", "post:detail"],
    "terry": ["post:list", "post:create", "post:edit"],
    "doe": [""],
}


@dataclass
class Post(DummyBaseModel):
    title: str
    content: str
    views: int


class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles


class PostView(DummyModelView):
    page_size = 2
    identity = "post"
    label = "Post"
    model = Post
    fields = (
        IntegerField("id"),
        StringField("title"),
        TextAreaField("content"),
        IntegerField("views"),
    )
    searchable_fields = ("title", "content")
    sortable_fields = ("id", "title", "content", "views")
    db = {}
    seq = 1

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


class TestAuth:
    @pytest.mark.asyncio
    async def test_auth_route(self):
        admin = BaseAdmin(auth_provider=AuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        assert app.url_path_for("admin:logout") == "/admin/logout"
        client = TestClient(app)
        response = await client.get("/admin/login")
        assert response.status_code == 200
        response = await client.get("/admin/", allow_redirects=False)
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == "http://localhost/admin/login?next=http%3A%2F%2Flocalhost%2Fadmin%2F"
        )

    @pytest.mark.asyncio
    async def test_not_implemented_login(self):
        admin = BaseAdmin(auth_provider=AuthProvider())
        app = Starlette()
        admin.mount_to(app)
        client = TestClient(app)
        response = await client.post(
            "/admin/login",
            allow_redirects=False,
            form={"username": "admin", "password": "password", "remember_me": "on"},
        )
        assert "Not Implemented" in response.text

    @pytest.mark.asyncio
    async def test_custom_login_path(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider(login_path="/custom-login"))
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/custom-login"
        client = TestClient(app)
        response = await client.get("/admin/", allow_redirects=False)
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == "http://localhost/admin/custom-login?next=http%3A%2F%2Flocalhost%2Fadmin%2F"
        )

    @pytest.mark.asyncio
    async def test_invalid_login(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        client = TestClient(app)
        form = {"username": "ad", "password": "invalid-password", "remember_me": "on"}
        response = await client.post("/admin/login", allow_redirects=False, form=form)
        assert "Ensure username has at least 03 characters" in response.text
        form["username"] = "admin"
        response = await client.post("/admin/login", allow_redirects=False, form=form)
        assert "Invalid username or password" in response.text

    @pytest.mark.asyncio
    async def test_valid_login(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        client = TestClient(app)
        response = await client.post(
            "/admin/login",
            form={"username": "admin", "password": "password", "remember_me": "on"},
            allow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://localhost/admin/"
        assert "session" in response.cookies
        assert response.cookies.get("session") == "admin"
        response = await client.get(
            "/admin/logout", allow_redirects=False, cookies={"session": "admin"}
        )
        assert response.status_code == 303
        assert "session" not in response.cookies


class TestAccess:
    def setup(self):
        PostView.db.clear()
        for post in json.load(open("./tests/data/posts.json")):
            del post["tags"]
            PostView.db[post["id"]] = Post(**post)
        PostView.seq = len(PostView.db.keys()) + 1

    @pytest.fixture
    def client(self):
        admin = BaseAdmin(
            auth_provider=MyAuthProvider(), templates_dir="tests/templates"
        )
        app = Starlette()
        admin.add_view(ReportView)
        admin.add_view(PostView)
        admin.mount_to(app)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_access_custom_view(self, client):
        response = await client.get("/admin/report", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/report", cookies={"session": "admin"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_list(self, client):
        response = await client.get("/admin/post/list", cookies={"session": "doe"})
        assert response.status_code == 403
        response = await client.get("/admin/api/post", cookies={"session": "doe"})
        assert response.status_code == 403
        response = await client.get("/admin/post/list", cookies={"session": "john"})
        assert response.status_code == 200
        response = await client.get("/admin/api/post", cookies={"session": "john"})
        assert response.status_code == 200
        assert '<span class="nav-link-title">Report</span>' not in response.text

    @pytest.mark.asyncio
    async def test_access_model_view_detail(self, client):
        response = await client.get("/admin/post/detail/1", cookies={"session": "john"})
        assert response.status_code == 200
        response = await client.get(
            "/admin/post/detail/1", cookies={"session": "terry"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_access_model_view_create(self, client):
        response = await client.get("/admin/post/create", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.post("/admin/post/create", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/post/create", cookies={"session": "terry"})
        assert response.status_code == 200
        response = await client.post("/admin/post/create", cookies={"session": "terry"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_edit(self, client):
        response = await client.get("/admin/post/edit/1", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.post("/admin/post/edit/1", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/post/edit/1", cookies={"session": "terry"})
        assert response.status_code == 200
        response = await client.post("/admin/post/edit/1", cookies={"session": "terry"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_delete(self, client):
        response = await client.delete(
            "/admin/api/post?pks=[1,2]", cookies={"session": "doe"}
        )
        assert response.status_code == 403
        response = await client.delete(
            "/admin/api/post?pks=[1,2]", cookies={"session": "john"}
        )
        assert response.status_code == 403
        response = await client.delete(
            "/admin/api/post?pks=[1,2]", cookies={"session": "terry"}
        )
        assert response.status_code == 403
        response = await client.delete(
            "/admin/api/post",
            query_string={"pks": [1, 2]},
            cookies={"session": "admin"},
        )
        assert response.status_code == 204
