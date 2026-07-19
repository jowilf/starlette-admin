import json
from collections.abc import Sequence

import pytest
import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import (
    BaseAdmin,
    BaseField,
    IntegerField,
    StringField,
    TinyMCEEditorField,
)
from starlette_admin.auth import AdminUser, AuthProvider, OAuthProvider
from starlette_admin.views import CustomView

from tests.auth_provider import MyAuthProvider
from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import make_csrf_async_client


class _ConcreteOAuthProvider(OAuthProvider):
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        return RedirectResponse(
            f"https://oauth.example.com/authorize?cb={callback_url}",
            status_code=302,
        )

    async def handle_callback(self, request: Request) -> None:
        request.session["user"] = "oauth_user"

    async def authenticate(self, request: Request) -> AdminUser | None:
        if user := request.session.get("user"):
            return AdminUser(username=user)
        return None


class Post(TinydbBaseModel):
    title: str = ""
    content: str = ""
    views: int | None = 0
    super_admin_only_field: int | None = 0


class ReportView(CustomView):
    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles


@pytest.fixture()
def report_view() -> ReportView:
    return ReportView(
        "Report",
        icon="fa fa-report",
        path="/report",
        route_name="report",
    )


class PostView(TinydbModelView):
    page_size = 2
    fields = [
        IntegerField("id"),
        StringField("title"),
        TinyMCEEditorField("content"),
        IntegerField("views"),
        IntegerField("super_admin_only_field"),
    ]
    searchable_fields = ("title", "content")
    sortable_fields = ("id", "title", "content", "views")

    def get_fields_list(
        self,
        request: Request,
        *,
        include_nested: bool = False,
    ) -> Sequence[BaseField]:
        fields = super().get_fields_list(request, include_nested=include_nested)
        if "super-admin" not in request.state.user_roles:
            fields = [f for f in fields if f.name != "super_admin_only_field"]
        return fields

    def is_accessible(self, request: Request) -> bool:
        return (
            "admin" in request.state.user_roles
            or "post:list" in request.state.user_roles
        )

    def can_view_detail(self, request: Request) -> bool:
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
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
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
        client = await make_csrf_async_client(app)
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
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
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
        client = await make_csrf_async_client(app)
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
        client = await make_csrf_async_client(app)
        response = await client.post(
            "/admin/login",
            data={"username": "admin", "password": "password", "remember_me": "on"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/"
        assert "session" in response.cookies
        assert response.cookies.get("session") == "admin"
        client.cookies.set("session", "admin")
        response = await client.post("/admin/logout", follow_redirects=False)
        assert response.status_code == 303
        assert "session" not in response.cookies

    @pytest.mark.asyncio
    async def test_render_login_already_authenticated_redirects_to_index(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
        client.cookies.set("session", "admin")
        response = await client.get(
            "/admin/login",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/"

    @pytest.mark.asyncio
    async def test_render_login_already_authenticated_with_valid_next_redirects_to_next(
        self,
    ):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
        client.cookies.set("session", "admin")
        response = await client.get(
            "/admin/login?next=http://testserver/admin/post/list",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/post/list"

    @pytest.mark.asyncio
    async def test_render_login_already_authenticated_cross_origin_next_falls_back_to_index(
        self,
    ):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.mount_to(app)
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
        client.cookies.set("session", "admin")
        response = await client.get(
            "/admin/login?next=http://evil.com/steal",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/"


def _seed_posts():
    PostView._db.truncate()
    with open("tests/data/posts.json") as f:
        for post in json.load(f):
            del post["tags"]
            PostView._db.insert(Post(**post).to_tinydb_doc())


class TestViewAccess:
    def setup_method(self, method):
        _seed_posts()

    @pytest_asyncio.fixture
    async def client(self, report_view):
        admin = BaseAdmin(
            auth_provider=MyAuthProvider(), templates_dir="tests/templates/auth"
        )
        app = Starlette()
        admin.add_view(report_view)
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        return await make_csrf_async_client(app)

    @pytest.mark.asyncio
    async def test_access_custom_view(self, client: AsyncClient):
        client.cookies.set("session", "john")
        response = await client.get("/admin/report")
        assert response.status_code == 403
        client.cookies.set("session", "admin")
        response = await client.get("/admin/report")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_list(self, client: AsyncClient):
        client.cookies.set("session", "doe")
        response = await client.get("/admin/post/list")
        assert response.status_code == 403
        response = await client.get("/admin/_api/post/relation-lookup")
        assert response.status_code == 403
        client.cookies.set("session", "john")
        response = await client.get("/admin/post/list")
        assert response.status_code == 200
        response = await client.get("/admin/_api/post/relation-lookup")
        assert response.status_code == 200
        assert '<span class="nav-link-title">Report</span>' not in response.text

    @pytest.mark.asyncio
    async def test_access_model_view_detail(self, client: AsyncClient):
        client.cookies.set("session", "john")
        response = await client.get("/admin/post/detail?pk=1")
        assert response.status_code == 200
        client.cookies.set("session", "terry")
        response = await client.get("/admin/post/detail?pk=1")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_access_model_view_create(self, client: AsyncClient):
        client.cookies.set("session", "john")
        response = await client.get("/admin/post/create")
        assert response.status_code == 403
        response = await client.post("/admin/post/create")
        assert response.status_code == 403
        client.cookies.set("session", "terry")
        response = await client.get("/admin/post/create")
        assert response.status_code == 200
        data = {"title": "title", "content": "content"}
        response = await client.post(
            "/admin/post/create",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_edit(self, client: AsyncClient):
        client.cookies.set("session", "john")
        response = await client.get("/admin/post/edit?pk=1")
        assert response.status_code == 403
        response = await client.post("/admin/post/edit?pk=1")
        assert response.status_code == 403
        client.cookies.set("session", "terry")
        response = await client.get("/admin/post/edit?pk=1")
        assert response.status_code == 200
        data = {"title": "title", "content": "content"}
        response = await client.post(
            "/admin/post/edit?pk=1",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_access_model_view_delete(self, client):
        client.cookies.set("session", "john")
        response = await client.post(
            "/admin/_api/post/action",
            params={"pks": [1, 2], "name": "delete"},
        )
        assert response.status_code == 400
        client.cookies.set("session", "doe")
        response = await client.post(
            "/admin/_api/post/action",
            params={"pks": [1, 2], "name": "delete"},
        )
        assert response.status_code == 400
        client.cookies.set("session", "terry")
        response = await client.post(
            "/admin/_api/post/action",
            params={"pks": [1, 2], "name": "delete"},
        )
        assert response.status_code == 400
        client.cookies.set("session", "admin")
        response = await client.post(
            "/admin/_api/post/action",
            params={"pks": [1, 2], "name": "delete"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "route_path,response_text",
        [
            ("public_sync", "sync public route"),
            ("public_async", "async public route"),
        ],
    )
    async def test_public_route(self, client, route_path, response_text):
        response = await client.get(f"/admin/{route_path}")
        assert response.status_code == 200
        assert response.text == response_text


class TestFieldAccess:
    def setup_method(self, method):
        _seed_posts()

    @pytest_asyncio.fixture
    async def client(self):
        admin = BaseAdmin(auth_provider=MyAuthProvider())
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        return await make_csrf_async_client(app)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_create(self, client, session, expected_value):
        client.cookies.set("session", session)
        response = await client.get("/admin/post/create")
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
        client.cookies.set("session", session)
        response = await client.post(
            "/admin/post/create",
            data=dummy_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PostView._get(6).super_admin_only_field == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_edit(self, client, session, expected_value):
        client.cookies.set("session", session)
        response = await client.get("/admin/post/edit?pk=1")
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
        client.cookies.set("session", session)
        response = await client.post(
            "/admin/post/edit?pk=1",
            data=dummy_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PostView._get(1).super_admin_only_field == expected_value


class TestOAuthProvider:
    @pytest_asyncio.fixture
    async def client(self):
        admin = BaseAdmin(
            auth_provider=_ConcreteOAuthProvider(),
            secret_key="test-secret",
            middlewares=[Middleware(SessionMiddleware, secret_key="test-secret")],
        )
        app = Starlette()
        admin.mount_to(app)
        return await make_csrf_async_client(app)

    def test_init_default_callback_path(self):
        provider = _ConcreteOAuthProvider()
        assert provider.callback_path == "/oauth/callback"
        assert "oauth_callback" in provider.allow_routes

    def test_init_custom_params(self):
        provider = _ConcreteOAuthProvider(
            callback_path="/custom/callback",
            allow_routes=["extra"],
        )
        assert provider.callback_path == "/custom/callback"
        assert "oauth_callback" in provider.allow_routes
        assert "extra" in provider.allow_routes

    @pytest.mark.asyncio
    async def test_login_redirects_to_oauth_provider(self, client: AsyncClient):
        response = await client.get("/admin/login", follow_redirects=False)
        assert response.status_code == 302
        assert "oauth.example.com" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_callback_without_next_redirects_to_index(self, client: AsyncClient):
        response = await client.get("/admin/oauth/callback", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/"

    @pytest.mark.asyncio
    async def test_login_with_next_then_callback_redirects_to_next(
        self, client: AsyncClient
    ):
        await client.get(
            "/admin/login?next=http://testserver/admin/post/list",
            follow_redirects=False,
        )
        response = await client.get(
            "/admin/oauth/callback?next=http://testserver/admin/post/list",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/post/list"

    @pytest.mark.asyncio
    async def test_logout_redirects_to_index(self, client: AsyncClient):
        await client.get("/admin/oauth/callback", follow_redirects=False)
        response = await client.post("/admin/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "http://testserver/admin/"


class TestLogoutEdgeCases:
    @pytest.mark.asyncio
    async def test_logout_exception_is_raised(self):
        class FailingLogoutProvider(MyAuthProvider):
            async def logout(self, request: Request) -> None:
                raise RuntimeError("logout boom")

        admin = BaseAdmin(auth_provider=FailingLogoutProvider())
        app = Starlette()
        admin.mount_to(app)
        client = await make_csrf_async_client(app)
        client.cookies.set("session", "admin")
        with pytest.raises(RuntimeError, match="logout boom"):
            await client.post("/admin/logout", follow_redirects=False)
