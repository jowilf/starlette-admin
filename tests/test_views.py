import json
from typing import Dict, List, Optional

import pytest
from pydantic import Field
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.views import CustomView, DropDown, Link

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Post(DummyBaseModel):
    title: str
    content: str
    views: Optional[int] = 0
    tags: List[str]


class User(DummyBaseModel):
    name: str
    posts: List[Post] = Field(default_factory=list)
    reviewer: Optional["User"] = None


class UserView(DummyModelView):
    model = User
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("posts", identity="post"),
        HasOne("reviewer", identity="user"),
    ]
    searchable_fields = "name"
    sortable_fields = ("id", "name")
    db = {}
    seq = 1


class PostView(DummyModelView):
    model = Post
    fields = (
        IntegerField("id"),
        StringField("title"),
        TextAreaField("content"),
        IntegerField("views"),
        TagsField("tags"),
    )
    searchable_fields = ("title", "content")
    sortable_fields = ("id", "title", "content", "views")
    db = {}
    seq = 1


class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"


class LinkToGoogle(Link):
    label = "LinkToGoogle"
    icon = "fa fa-link"
    url = "https://google.com"


class Section(DropDown):
    label = "Models"
    icon = "fa fa-models"
    views = [UserView, ReportView, LinkToGoogle]


class TestViews:
    def setup(self):
        UserView.db.clear()
        UserView.db[1] = User(id=1, name="John Doe")
        UserView.db[2] = User(id=2, name="Terry Smitham")
        UserView.seq = 3

        PostView.db.clear()
        for post in json.load(open("./tests/data/posts.json")):
            PostView.db[post["id"]] = Post(**post)
        PostView.seq = len(PostView.db.keys()) + 1

    def test_add_custom_view(self):
        admin = BaseAdmin(templates_dir="tests/templates")
        app = Starlette()
        admin.add_view(ReportView)
        admin.mount_to(app)
        assert len(admin._views) == 1
        assert app.url_path_for("admin:report") == "/admin/report"
        client = TestClient(app)
        response = client.get("/admin/report")
        assert response.text.count('<li class="nav-item">') == 1
        assert response.text.count('<span class="nav-link-title">Report</span>') == 1
        assert response.text.count('<i class="fa fa-report"></i>') == 1
        assert "This is custom view to display some data." in response.text

    def test_add_model_view(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        assert len(admin._views) == 1
        identity = "post"
        assert admin._find_model_from_identity(identity) is not None
        with pytest.raises(
            HTTPException, match="Model with identity unknown not found"
        ):
            admin._find_model_from_identity("unknown")
        client = TestClient(app)
        assert app.url_path_for("admin:api", identity=identity) == "/admin/api/post"
        assert client.get("/admin/api/post").status_code == 200
        assert app.url_path_for("admin:list", identity=identity) == "/admin/post/list"
        assert client.get("/admin/post/list").status_code == 200
        assert (
            app.url_path_for("admin:detail", identity=identity, pk=1)
            == "/admin/post/detail/1"
        )
        assert client.get("/admin/post/detail/1").status_code == 200
        assert client.get("/admin/post/detail/6").status_code == 404
        assert (
            app.url_path_for("admin:create", identity=identity) == "/admin/post/create"
        )
        assert client.get("/admin/post/create").status_code == 200
        assert (
            app.url_path_for("admin:edit", identity=identity, pk=1)
            == "/admin/post/edit/1"
        )
        assert client.get("/admin/post/edit/1").status_code == 200
        assert client.get("/admin/post/edit/6").status_code == 404

    def test_model_view_api(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin/api/post?limit=-1")
        assert response.status_code == 200
        assert [x["id"] for x in response.json()["items"]] == [1, 2, 3, 4, 5]
        response = client.get("/admin/api/post?skip=2&limit=2&order_by=title desc")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert [x["id"] for x in data["items"]] == [4, 3]
        response = client.get("/admin/api/post?skip=1&where=important&order_by=id asc")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["items"][0]["id"] == 5
        response = client.get("/admin/api/post?select2=true")
        for value in response.json()["items"]:
            assert value.get("_select2_selection") is not None
            assert value.get("_select2_result") is not None

    def test_model_view_create_new(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app, base_url="http://testserver")
        dummy_data = {
            "title": "Dummy post",
            "content": "This is a content",
            "views": 10,
            "tags": ["tag1", "tag2"],
        }
        response = client.post(
            "/admin/post/create", data=dummy_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/list"
        assert len(PostView.db) == 6
        assert PostView.db[6] == Post(id=6, **dummy_data)

        response = client.post(
            "/admin/post/create",
            data=dict(**dummy_data, _continue_editing=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/edit/7"

        response = client.post(
            "/admin/post/create",
            data=dict(**dummy_data, _add_another=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/create"

    def test_model_view_edit(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app, base_url="http://testserver")
        dummy_data = {
            "title": "Edited dummy post",
            "content": "This is a content",
            "views": 10,
            "tags": ["tag1", "tag2"],
        }
        response = client.post(
            "/admin/post/edit/5", data=dummy_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/list"
        assert len(PostView.db) == 5
        assert PostView.db[5] == Post(id=5, **dummy_data)

        response = client.post(
            "/admin/post/edit/5",
            data=dict(**dummy_data, _continue_editing=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/edit/5"

        response = client.post(
            "/admin/post/edit/5",
            data=dict(**dummy_data, _add_another=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/create"

    def test_model_view_create_validation_error(self):
        class PostViewWithRestrictedTitle(PostView):
            def validate_data(self, data: Dict):
                if len(data["title"]) < 3:
                    raise FormValidationError(
                        {"title": "Ensure Post title has at least 03 characters"}
                    )

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostViewWithRestrictedTitle)
        admin.mount_to(app)
        client = TestClient(app)
        dummy_data = {
            "title": "Du",
            "content": "This is a content",
            "views": None,
            "tags": ["tag1", "tag2"],
        }
        response = client.post("/admin/post/create", data=dummy_data)
        assert response.status_code == 200
        assert "Ensure Post title has at least 03 characters" in response.text
        response = client.post("/admin/post/edit/1", data=dummy_data)
        assert response.status_code == 200
        assert "Ensure Post title has at least 03 characters" in response.text

    def test_model_view_delete(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app)
        response = client.delete("/admin/api/post", params={"pks": [1, 3, 5]})
        assert response.status_code == 204
        assert len(PostView.db) == 2
        assert [x for x in PostView.db.keys()] == [2, 4]

    def test_other_fields(self):
        class MyModel(DummyBaseModel):
            score: Optional[float]
            gender: str
            json_field: Optional[dict]

        class MyModelView(DummyModelView):
            fields = [
                IntegerField("id"),
                FloatField("score"),
                EnumField.from_choices(
                    "gender",
                    (
                        "male",
                        "female",
                    ),
                ),
                JSONField("json_field"),
            ]
            model = MyModel
            db = {}
            seq = 1

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(MyModelView)
        admin.mount_to(app)
        client = TestClient(app)

        response = client.post(
            "/admin/my-model/create",
            data={"score": 3.4, "gender": "male", "json_field": '{"key":"value"}'},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView.db[1] == MyModel(
            id=1, score=3.4, gender="male", json_field=dict(key="value")
        )
        # Test Api
        response = client.get("/admin/api/my-model?pks=1")
        assert response.status_code == 200
        assert [1] == [x["id"] for x in response.json()["items"]]

        # Test edit page load
        response = client.get("/admin/my-model/edit/1")
        assert response.status_code == 200

        # Test edition
        response = client.post(
            "/admin/my-model/edit/1",
            data={
                "score": 5.6,
                "gender": "female",
                "json_field": '{"new_key":"new_value"}',
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView.db[1] == MyModel(
            id=1, score=5.6, gender="female", json_field={"new_key": "new_value"}
        )
        # Test None for float and invalid json
        response = client.post(
            "/admin/my-model/edit/1",
            data={"score": "", "gender": "male", "json_field": "}"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView.db[1] == MyModel(
            id=1, score=None, gender="male", json_field=None
        )

        # Test enum value error
        MyModelView.db[2] = MyModel(
            id=2, score=4.5, gender="unknown", json_field=dict()
        )
        with pytest.raises(ValueError, match="Invalid choice value: unknown"):
            response = client.get("/admin/api/my-model?pks=2")

    def test_has_one_relationships(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView)
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app)
        assert client.get("/admin/user/create").status_code == 200
        dummy_data = {"reviewer": 1, "name": "John Doe"}
        client.post("/admin/user/create", data=dummy_data)
        assert len(UserView.db) == 3
        assert UserView.db[3].reviewer == UserView.db[1]
        dummy_data.update({"reviewer": 2})
        assert client.get("/admin/user/edit/3").status_code == 200
        client.post("/admin/user/edit/3", data=dummy_data)
        assert len(UserView.db) == 3
        assert UserView.db[3].reviewer == UserView.db[2]
        del dummy_data["reviewer"]
        assert client.get("/admin/user/edit/3").status_code == 200
        client.post("/admin/user/edit/3", data=dummy_data)
        assert len(UserView.db) == 3
        assert UserView.db[3].reviewer is None
        assert client.get("/admin/user/edit/3").status_code == 200

    def test_has_many_relationships(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView)
        admin.add_view(PostView)
        admin.mount_to(app)
        client = TestClient(app)
        dummy_data = {"name": "John Doe", "posts": [1, 3, 4]}
        assert client.get("/admin/user/create").status_code == 200
        client.post("/admin/user/create", data=dummy_data)
        assert len(UserView.db) == 3
        assert UserView.db[3].posts == [PostView.db[x] for x in [1, 3, 4]]
        dummy_data.update({"posts": [2, 5]})
        assert client.get("/admin/user/edit/3").status_code == 200
        client.post("/admin/user/edit/3", data=dummy_data)
        assert len(UserView.db) == 3
        assert UserView.db[3].posts == [PostView.db[x] for x in [2, 5]]

    def test_add_link(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(LinkToGoogle)
        admin.mount_to(app)
        assert len(admin._views) == 1
        client = TestClient(app, base_url="http://testserver")
        response = client.get("/admin")
        assert (
            response.text.count('<span class="nav-link-title">LinkToGoogle</span>') == 1
        )
        assert (
            response.text.count(
                '<a class="nav-link" href="https://google.com" target="_self">'
            )
            == 1
        )

    def test_add_dropdown(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView)
        admin.add_view(Section)
        admin.mount_to(app)
        assert len(admin._views) == 2
        assert admin._find_model_from_identity("user") is not None
        assert admin._find_model_from_identity("post") is not None
        client = TestClient(app, base_url="http://testserver")
        response = client.get("/admin")
        assert response.text.count('<li class="nav-item dropdown ">') == 1
        assert response.text.count('<span class="nav-link-title">') == 2
        assert (
            response.text.count(
                '<a href="http://testserver/admin/user/list"'
                ' class="dropdown-item">Users</a>'
            )
            == 1
        )
        assert (
            response.text.count(
                '<a href="http://testserver/admin/report"'
                ' class="dropdown-item">Report</a>'
            )
            == 1
        )
        assert (
            response.text.count(
                '<a href="https://google.com" class="dropdown-item"'
                ' target="_self">LinkToGoogle</a>'
            )
            == 1
        )
