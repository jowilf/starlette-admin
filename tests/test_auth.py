import json
from typing import Optional, Sequence

import pytest
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import (
    BaseAdmin,
    BaseField,
    IntegerField,
    RequestAction,
    StringField,
    TinyMCEEditorField,
)
from starlette_admin.auth import AuthProvider
from starlette_admin.views import CustomView

from tests.auth_provider import MyAuthProvider
from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Post(DummyBaseModel):
    title: str
    content: str
    views: Optional[int] = 0
    super_admin_only_field: Optional[int] = 0


class ReportView(CustomView):
    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles


@pytest.fixture()
def report_view() -> ReportView:
    return ReportView(
        "Report",
        icon="fa fa-report",
        path="/report",
        template_path="report.html",
        name="report",
    )


class PostView(DummyModelView):
    page_size = 2
    model = Post
    fields = (
        IntegerField("id"),
        StringField("title"),
        TinyMCEEditorField("content"),
        IntegerField("views"),
        IntegerField("super_admin_only_field"),
    )
    searchable_fields = ("title", "content")
    sortable_fields = ("id", "title", "content", "views")
    db = {}
    seq = 1

    def get_fields_list(
        self,
        request: Request,
        action: RequestAction = RequestAction.LIST,
    ) -> Sequence[BaseField]:
        fields = super().get_fields_list(request, action)
        if "super-admin" not in request.state.user_roles:
            fields = [f for f in fields if f.name != "super_admin_only_field"]
        return fields

    def is_accessible(self, request: Request) -> bool:
        return (
            "admin" in request.state.user_roles
            or "post:list" in request.state.user_roles
        )

    def can_view_details(self, request: Request) -> bool:
        return (
            "super-admin" in request.state.user_roles
            or "post:detail" in request.state.user_roles
        )

    def can_create(self, request: Request) -> bool:
        return (
            "super-admin" in request.state.user_roles
            or "post:create" in request.state.user_roles
        )

    def can_edit(self, request: Request) -> bool:
        return (
            "super-admin" in request.state.user_roles
            or "post:edit" in request.state.user_roles
        )

    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.user_roles


class TestAuth:
    @pytest.mark.asyncio
    async def test_auth_route(self):
        admin = BaseAdmin(auth_provider=AuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        assert app.url_path_for("admin:logout") == "/admin/logout"
        client = AsyncClient(app=app, base_url="http://testserver")
        response = await client.get("/admin/login")
        assert response.status_code == 200
        response = await client.get("/admin/", follow_redirects=False)
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == "http://testserver/admin/login?next=http%3A%2F%2Ftestserver%2Fadmin%2F"
        )

    @pytest.mark.asyncio
    async def test_not_implemented_login(self):
        admin = BaseAdmin(auth_provider=AuthProvider())
        app = Starlette()
        admin.mount_to(app)
        client = AsyncClient(app=app, base_url="http://testserver")
        response = await client.post(
            "/admin/login",
            follow_redirects=False,
            data={"username": "admin", "password": "password", "remember_me": "on"},
        )
        assert "Not Implemented" in response.text

    @pytest.mark.asyncio
    async def test_custom_login_path(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider(login_path="/custom-login"))
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/custom-login"
        client = AsyncClient(app=app, base_url="http://testserver")
        response = await client.get("/admin/", follow_redirects=False)
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == "http://testserver/admin/custom-login?next=http%3A%2F%2Ftestserver%2Fadmin%2F"
        )

    @pytest.mark.asyncio
    async def test_invalid_login(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        client = AsyncClient(app=app, base_url="http://testserver")
        data = {"username": "ad", "password": "invalid-password", "remember_me": "on"}
        response = await client.post("/admin/login", follow_redirects=False, data=data)
        assert "Ensure username has at least 03 characters" in response.text
        data["username"] = "admin"
        response = await client.post("/admin/login", follow_redirects=False, data=data)
        assert "Invalid username or password" in response.text

    @pytest.mark.asyncio
    async def test_valid_login(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        assert app.url_path_for("admin:login") == "/admin/login"
        client = AsyncClient(app=app, base_url="http://testserver")
        response = await client.post(
            "/admin/login",
            data={"username": "admin", "password": "password", "remember_me": "on"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/"
        assert "session" in response.cookies
        assert response.cookies.get("session") == "admin"
        response = await client.get(
            "/admin/logout", follow_redirects=False, cookies={"session": "admin"}
        )
        assert response.status_code == 303
        assert "session" not in response.cookies


class TestViewAccess:
    def setup_method(self, method):
        PostView.db.clear()
        with open("./tests/data/posts.json") as f:
            for post in json.load(f):
                del post["tags"]
                PostView.db[post["id"]] = Post(**post)
        PostView.seq = len(PostView.db.keys()) + 1

    @pytest.fixture
    def client(self, report_view):
        admin = BaseAdmin(
            auth_provider=MyAuthProvider(), templates_dir="tests/templates"
        )
        app = Starlette()
        admin.add_view(report_view)
        admin.add_view(PostView)
        admin.mount_to(app)
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_access_custom_view(self, client: AsyncClient):
        response = await client.get("/admin/report", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/report", cookies={"session": "admin"})
        assert response.status_code == 200
        assert 'Welcome admin!' in response.text

    @pytest.mark.asyncio
    async def test_access_model_view_list(self, client: AsyncClient):
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
    async def test_access_model_view_detail(self, client: AsyncClient):
        response = await client.get("/admin/post/detail/1", cookies={"session": "john"})
        assert response.status_code == 200
        response = await client.get(
            "/admin/post/detail/1", cookies={"session": "terry"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_access_model_view_create(self, client: AsyncClient):
        response = await client.get("/admin/post/create", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.post("/admin/post/create", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/post/create", cookies={"session": "terry"})
        assert response.status_code == 200
        data = {"title": "title", "content": "content"}
        response = await client.post(
            "/admin/post/create",
            data=data,
            cookies={"session": "terry"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_edit(self, client: AsyncClient):
        response = await client.get("/admin/post/edit/1", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.post("/admin/post/edit/1", cookies={"session": "john"})
        assert response.status_code == 403
        response = await client.get("/admin/post/edit/1", cookies={"session": "terry"})
        assert response.status_code == 200
        response = await client.post(
            "/admin/post/edit/1", cookies={"session": "terry"}, follow_redirects=True
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_delete(self, client):
        response = await client.post(
            "/admin/api/post/action",
            params={"pks": [1, 2], "name": "delete"},
            cookies={"session": "john"},
        )
        assert response.status_code == 400
        response = await client.post(
            "/admin/api/post/action",
            params={"pks": [1, 2], "name": "delete"},
            cookies={"session": "doe"},
        )
        assert response.status_code == 400
        response = await client.post(
            "/admin/api/post/action",
            params={"pks": [1, 2], "name": "delete"},
            cookies={"session": "terry"},
        )
        assert response.status_code == 400
        response = await client.post(
            "/admin/api/post/action",
            params={"pks": [1, 2], "name": "delete"},
            cookies={"session": "admin"},
        )
        assert response.status_code == 200


class TestFieldAccess:
    def setup_method(self, method):
        PostView.db.clear()
        with open("./tests/data/posts.json") as f:
            for post in json.load(f):
                del post["tags"]
                PostView.db[post["id"]] = Post(**post)
        PostView.seq = len(PostView.db.keys()) + 1

    @pytest.fixture
    def client(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_create(self, client, session, expected_value):
        response = await client.get("/admin/post/create", cookies={"session": session})
        assert response.status_code == 200
        assert response.text.count('name="super_admin_only_field"') == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 5),
            ("terry", 0),
        ],
    )
    async def test_create(self, client, session, expected_value):
        dummy_data = {
            "title": "Dummy post",
            "content": "This is a content",
            "views": 10,
            "super_admin_only_field": 5,
        }
        response = await client.post(
            "/admin/post/create",
            data=dummy_data,
            cookies={"session": session},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PostView.db[6].super_admin_only_field == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_edit(self, client, session, expected_value):
        response = await client.get("/admin/post/edit/1", cookies={"session": session})
        assert response.status_code == 200
        assert response.text.count('name="super_admin_only_field"') == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 5),
            ("terry", 0),
        ],
    )
    async def test_edit(self, client, session, expected_value):
        dummy_data = {
            "title": "Dummy post - edit",
            "content": "This is a content - edit",
            "views": 8,
            "super_admin_only_field": 5,
        }
        response = await client.post(
            "/admin/post/edit/1",
            data=dummy_data,
            cookies={"session": session},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PostView.db[1].super_admin_only_field == expected_value
