import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, IntegerField, StringField, TextAreaField
from starlette_admin.views import CustomView

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView


class Post(TinydbBaseModel):
    title: str = ""
    content: str = ""
    views: int = 0


class User(TinydbBaseModel):
    name: str = ""


@pytest.fixture()
def report_view() -> CustomView:
    return CustomView(
        "Report",
        icon="fa fa-report",
        path="/report",
        route_name="report",
    )


class UserView(TinydbModelView):
    fields = [IntegerField("id"), StringField("name")]


class PostView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        TextAreaField("content"),
        IntegerField("views"),
    ]


def test_multiple_admin(report_view):
    app = Starlette()

    admin1 = BaseAdmin(
        "Admin1",
        base_url="/admin1",
        route_name="admin1",
        templates_dir="tests/templates/multiple-admin",
    )
    admin1.add_view(report_view)
    admin1.add_view(PostView(Post))
    admin1.mount_to(app)

    admin2 = BaseAdmin("Admin2", base_url="/admin2", route_name="admin2")
    admin2.add_view(PostView(Post))
    admin2.add_view(UserView(User))
    admin2.mount_to(app)

    assert app.url_path_for("admin1:index") == "/admin1/"
    assert app.url_path_for("admin2:index") == "/admin2/"

    client = TestClient(app)
    response = client.get("/admin1")
    assert response.status_code == 200
    assert response.text.count("<title>Admin1</title>") == 1
    assert response.text.count('<span class="nav-link-title">Report</span>') == 1
    assert response.text.count('<span class="nav-link-title">Posts</span>') == 1

    response = client.get("/admin2")
    assert response.status_code == 200
    assert response.text.count("<title>Admin2</title>") == 1
    assert response.text.count('<span class="nav-link-title">Users</span>') == 1
    assert response.text.count('<span class="nav-link-title">Posts</span>') == 1

    assert client.get("/admin1/report").status_code == 200
    assert client.get("/admin1/post/list").status_code == 200
    assert client.get("/admin1/user/list").status_code == 404

    assert client.get("/admin2/report").status_code == 404
    assert client.get("/admin2/post/list").status_code == 200
    assert client.get("/admin2/user/list").status_code == 200
