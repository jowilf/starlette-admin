from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin
from starlette_admin.base import DefaultAdminIndexView
from starlette_admin.views import CustomView


class TestAdminBasic:
    def test_admin_default(self):
        admin = BaseAdmin()
        assert admin.base_url == "/admin"
        assert admin.title == "Admin"
        assert admin.logo_url is None
        assert admin.login_logo_url is None
        assert admin.middlewares is None
        assert admin.index_view == DefaultAdminIndexView
        assert not admin.debug
        app = Starlette()
        admin.mount_to(app)
        # Test default index view
        client = TestClient(app)
        response = client.get("/admin")
        assert response.status_code == 200
        assert response.text.count("<title>Admin</title>") == 1
        assert response.text.count('<li class="nav-item">') == 0
        # Test login url is not added by default
        response = client.get("/admin/login")
        assert response.status_code == 404

    def test_custom_index_view(self):
        class CustomIndexView(CustomView):
            label = "Home"
            path = "/home"
            template_path = "custom_index.html"

        app = Starlette()
        admin = BaseAdmin(index_view=CustomIndexView, templates_dir="tests/templates")
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
            debug=True,
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
