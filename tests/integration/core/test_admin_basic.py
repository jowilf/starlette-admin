import pytest
from jinja2 import DictLoader, FileSystemLoader
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, HasMany, IntegerField, StringField, route
from starlette_admin.exceptions import InvalidRelationFieldError
from starlette_admin.flash import FlashMiddleware
from starlette_admin.security.csrf import CSRFMiddleware
from starlette_admin.views import CustomView

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView


class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(
            request=request,
            name="custom_index.html",
            context={"title": self.title(request)},
        )


class TestAdminBasic:
    def test_admin_default(self):
        admin = BaseAdmin()
        assert admin.base_url == "/admin"
        assert admin.title == "Admin"
        assert admin.logo_url is None
        assert admin.login_logo_url is None
        assert isinstance(admin.index_view, CustomView)
        app = Starlette()
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 200
        assert response.text.count("<title>Admin</title>") == 1
        assert response.text.count('<li class="nav-item">') == 0
        response = client.get("/admin/login")
        assert response.status_code == 404

    def test_custom_index_view(self):
        app = Starlette()
        admin = BaseAdmin(
            index_view=HomeView(),
            templates_dir="tests/templates/basic",
        )
        admin.mount_to(app)
        assert len(admin._views) == 1
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 404
        assert app.url_path_for("admin:index") == "/admin/home"
        response = client.get("/admin/home")
        assert response.status_code == 200
        assert response.text.count('<li class="nav-item">') == 1
        assert response.text.count('<span class="nav-link-title">Home</span>') == 1
        assert response.text.count("This is custom index view.") == 1

    def test_admin_customisation(self):
        app = Starlette()
        admin = BaseAdmin(
            base_url="/dashboard",
            title="DashBoard",
            logo_url="https://test.com/logo.png",
        )
        admin.mount_to(app)
        assert admin.base_url == "/dashboard"
        assert admin.title == "DashBoard"
        assert admin.logo_url == "https://test.com/logo.png"
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 404
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert response.text.count("<title>DashBoard</title>") == 1
        assert response.text.count("https://test.com/logo.png") == 1

    def test_template_override(self):
        app = Starlette()
        admin = BaseAdmin(templates_dir="tests/templates/basic")
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 200
        assert (
            response.text.count('<meta name="custom-meta" content="Custom metadata" />')
            == 1
        )

    def test_additional_loaders(self):
        app = Starlette()
        admin = BaseAdmin(
            additional_loaders=[FileSystemLoader("tests/templates/basic")]
        )
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 200
        assert (
            response.text.count('<meta name="custom-meta" content="Custom metadata" />')
            == 1
        )

    def test_templates_dir_takes_precedence_over_additional_loaders(self):
        app = Starlette()
        admin = BaseAdmin(
            templates_dir="tests/templates/basic",
            additional_loaders=[
                DictLoader(
                    {
                        "base.html": (
                            '{% extends "@starlette-admin/base.html" %}'
                            "{% block head_meta %}"
                            '<meta name="custom-meta" content="From loader" />'
                            "{% endblock %}"
                        )
                    }
                )
            ],
        )
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 200
        assert (
            response.text.count('<meta name="custom-meta" content="Custom metadata" />')
            == 1
        )
        assert response.text.count("From loader") == 0

    def test_admin_with_pre_existing_csrf_middleware(self):
        admin = BaseAdmin(
            secret_key="test",
            middlewares=[Middleware(CSRFMiddleware, secret_key="test")],
        )
        csrf_count = sum(
            1 for m in admin.middlewares if getattr(m, "cls", None) is CSRFMiddleware
        )
        assert csrf_count == 1

    def test_admin_with_pre_existing_flash_middleware(self):
        admin = BaseAdmin(
            secret_key="test",
            middlewares=[Middleware(FlashMiddleware, secret_key="test")],
        )
        flash_count = sum(
            1 for m in admin.middlewares if getattr(m, "cls", None) is FlashMiddleware
        )
        assert flash_count == 1


class TestMountLifecycle:
    def test_app_raises_before_mount(self):
        admin = BaseAdmin()
        with pytest.raises(RuntimeError, match="mount_to"):
            admin.app  # noqa: B018

    def test_mount_to_sets_app(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.mount_to(app)
        assert isinstance(admin.app, Starlette)

    def test_add_view_after_mount_raises(self):
        admin = BaseAdmin()
        admin.mount_to(Starlette())
        with pytest.raises(RuntimeError, match="mount_to"):
            admin.add_view(CustomView(menu_label="Extra"))

    def test_mount_to_twice_raises(self):
        admin = BaseAdmin()
        admin.mount_to(Starlette())
        with pytest.raises(RuntimeError, match="already been mounted"):
            admin.mount_to(Starlette())


class _Author(TinydbBaseModel):
    name: str = ""


class _Book(TinydbBaseModel):
    title: str = ""


class _AuthorView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class _BookView(TinydbModelView):
    fields = [IntegerField("id"), StringField("title")]


class TestRelationFieldValidation:
    def test_mount_to_raises_on_unknown_relation_key(self):
        app = Starlette()
        admin = BaseAdmin()
        admin.add_view(_AuthorView(_Author, key="author"))
        with pytest.raises(InvalidRelationFieldError, match="book"):
            admin.mount_to(app)

    def test_mount_to_passes_when_relation_key_registered(self):
        app = Starlette()
        admin = BaseAdmin()
        admin.add_view(_AuthorView(_Author, key="author"))
        admin.add_view(_BookView(_Book, key="book"))
        admin.mount_to(app)
