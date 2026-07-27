import json
import re
from typing import Optional
from urllib.parse import quote_plus

import pytest
from pydantic import Field
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    CardRowWidget,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    StatWidget,
    StringField,
    TagsField,
    TextAreaField,
    route,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.views import CustomView, DropDown, Link

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Post(TinydbBaseModel):
    title: str
    content: str
    views: int | None = 0
    tags: list[str] = Field(default_factory=list)

    async def __admin_repr__(self, request: Request):
        return self.title

    async def __admin_select2_repr__(self, request: Request):
        return f"<span>{self.title}</span>"


class User(TinydbBaseModel):
    name: str
    posts: list[Post] = Field(default_factory=list)
    reviewer: Optional["User"] = None

    def __admin_repr__(self, request: Request):
        return self.name

    def __admin_select2_repr__(self, request: Request):
        return f"<span>{self.name}</span>"


class UserView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("posts", key="post"),
        HasOne("reviewer", key="user"),
    ]
    searchable_fields = ("name",)
    sortable_fields = ("id", "name")


class PostView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        TextAreaField("content"),
        IntegerField("views"),
        TagsField("tags"),
    ]
    searchable_fields = ("title", "content")
    sortable_fields = ("id", "title", "content", "views")


class ReportView(CustomView):
    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(
            request=request,
            name="report.html",
            context={"title": self.title(request)},
        )


@pytest.fixture()
def report_view() -> CustomView:
    return ReportView(
        "Report",
        icon="fa fa-report",
        path="/report",
        route_name="report",
    )


@pytest.fixture()
def link_to_google() -> Link:
    return Link("LinkToGoogle", icon="fa fa-link", url="https://google.com")


@pytest.fixture()
def section_dropdown(report_view, link_to_google) -> DropDown:
    return DropDown(
        "Models",
        icon="fa fa-models",
        views=[UserView(User), report_view, link_to_google],
    )


def _breadcrumb_href(html: str) -> str:
    """Return the URL the "Users" breadcrumb link points at.

    Several carry-origin tests check this, so it is defined once at
    module scope rather than duplicated in each test.
    """
    match = re.search(r'<a href="([^"]+)">Users</a>', html)
    assert match is not None, "breadcrumb link not found"
    return match.group(1)


class TestViews:
    def setup_method(self, method):
        UserView._db.truncate()
        UserView._db.insert(User(name="John Doe").to_tinydb_doc())
        UserView._db.insert(User(name="Terry Smitham").to_tinydb_doc())

        PostView._db.truncate()
        with open("tests/data/posts.json") as f:
            for post in json.load(f):
                PostView._db.insert(Post(**post).to_tinydb_doc())

    def test_add_custom_view(self, report_view):
        admin = BaseAdmin(templates_dir="tests/templates/views")
        app = Starlette()
        admin.add_view(report_view)
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
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        assert len(admin._views) == 1
        key = "post"
        assert admin._find_view_by_key(key) is not None
        with pytest.raises(HTTPException, match="Model with key unknown not found"):
            admin._find_view_by_key("unknown")
        client = TestClient(app)
        assert (
            app.url_path_for("admin:relation-lookup", key=key)
            == "/admin/_api/post/relation-lookup"
        )
        assert client.get("/admin/_api/post/relation-lookup").status_code == 200
        assert app.url_path_for("admin:list", key=key) == "/admin/post/list"
        assert client.get("/admin/post/list").status_code == 200
        assert app.url_path_for("admin:detail", key=key) == "/admin/post/detail"
        assert client.get("/admin/post/detail?pk=1").status_code == 200
        assert client.get("/admin/post/detail?pk=6").status_code == 404
        assert app.url_path_for("admin:create", key=key) == "/admin/post/create"
        assert client.get("/admin/post/create").status_code == 200
        assert app.url_path_for("admin:edit", key=key) == "/admin/post/edit"
        assert client.get("/admin/post/edit?pk=1").status_code == 200
        assert client.get("/admin/post/edit?pk=6").status_code == 404

    def test_sync_object_representation(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView(User))
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin/_api/user/relation-lookup")
        data = response.json()
        for value in data["items"]:
            assert value["_meta"]["select2"]["selection"] is not None
            assert value["_meta"]["select2"]["result"] is not None
        assert data["items"][0]["_meta"] == {
            "detailUrl": "http://testserver/admin/user/detail?pk=1",
            "repr": "John Doe",
            "select2": {
                "selection": "<span>John Doe</span>",
                "result": "<span>John Doe</span>",
            },
        }

    def test_async_object_representation(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin/_api/post/relation-lookup")
        data = response.json()
        for value in data["items"]:
            assert value["_meta"]["select2"]["selection"] is not None
            assert value["_meta"]["select2"]["selection"] is not None
        title = "Dave wasn't exactly sure how he had ended up"
        assert data["items"][0]["_meta"] == {
            "detailUrl": "http://testserver/admin/post/detail?pk=1",
            "repr": title,
            "select2": {
                "selection": f"<span>{title}</span>",
                "result": f"<span>{title}</span>",
            },
        }

    def test_relation_lookup_invalid_skip_limit_falls_back_to_defaults(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin/_api/post/relation-lookup?skip=abc&limit=xyz")
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    def test_model_view_create_new(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
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
        assert PostView._len() == 6
        assert PostView._get(6) == Post(id=6, **dummy_data)

        response = client.post(
            "/admin/post/create",
            data=dict(**dummy_data, _continue_editing=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers.get("location") == "http://testserver/admin/post/edit?pk=7"
        )

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
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        dummy_data = {
            "title": "Edited dummy post",
            "content": "This is a content",
            "views": 10,
            "tags": ["tag1", "tag2"],
        }
        response = client.post(
            "/admin/post/edit?pk=5", data=dummy_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/list"
        assert PostView._len() == 5
        assert PostView._get(5) == Post(id=5, **dummy_data)

        response = client.post(
            "/admin/post/edit?pk=5",
            data=dict(**dummy_data, _continue_editing=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers.get("location") == "http://testserver/admin/post/edit?pk=5"
        )

        response = client.post(
            "/admin/post/edit?pk=5",
            data=dict(**dummy_data, _add_another=True),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "http://testserver/admin/post/create"

    def _carry_origin_client(self) -> CsrfTestClient:
        """Build the admin app shared by every carry-origin test below.

        `_carry_origin` (in `starlette_admin/helpers.py`) decides what
        `_origin` a generated link should carry: the current page's own URL
        when leaving a list or detail page, an `_origin` already present on
        the request when leaving anywhere else (e.g. an edit page), or
        nothing at all for an internal API call with no meaningful "back"
        destination. The tests below each exercise one caller of that
        function - `detail_url`, `edit_url`, `create_url`, `back_url`, the
        row-action redirect, or the `safe_redirect_url` guard they all rely
        on - against a fresh instance of this same app.
        """
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView(User))
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    def test_list_stamps_own_url_as_origin(self):
        """The list page stamps its own path as `_origin` on its outbound
        links: both the per-row "detail" link and the "Add new" link."""
        client = self._carry_origin_client()

        # Jinja autoescapes `&` to `&amp;` inside href attributes, so the
        # URL embedded in the rendered HTML needs a separate escaped form
        # from the one used to issue requests or match redirect headers.
        # `_origin` carries only the path (no scheme/host).
        list_path = "/admin/user/list?q=John"
        list_origin = quote_plus(list_path)

        list_response = client.get(list_path)
        assert list_response.status_code == 200

        detail_url = f"http://testserver/admin/user/detail?pk=1&_origin={list_origin}"
        assert f'href="{detail_url.replace("&", "&amp;")}"' in list_response.text

        create_from_list_url = (
            f"http://testserver/admin/user/create?_origin={list_origin}"
        )
        assert (
            f'href="{create_from_list_url.replace("&", "&amp;")}"' in list_response.text
        )

    def test_detail_carries_own_url_as_origin_for_edit(self):
        """Detail hands its own path, origin nested inside, to its edit
        link, so editing from detail returns to detail instead of jumping
        past it back to the list."""
        client = self._carry_origin_client()

        list_url = "http://testserver/admin/user/list?q=John"
        list_origin = quote_plus(list_url)
        detail_url = f"http://testserver/admin/user/detail?pk=1&_origin={list_origin}"
        detail_path = detail_url.removeprefix("http://testserver")

        detail_response = client.get(detail_path)
        assert detail_response.status_code == 200

        # The breadcrumb reads `_origin` straight off the request, so it
        # still points at the original filtered list.
        assert f'href="{list_url}">' in detail_response.text

        # `_origin` carries only the path (no scheme/host).
        detail_origin = quote_plus(detail_path)
        edit_url = f"http://testserver/admin/user/edit?pk=1&_origin={detail_origin}"
        assert f'href="{edit_url.replace("&", "&amp;")}"' in detail_response.text

    def test_edit_breadcrumb_and_cancel_resolve_nested_origin_to_detail(self):
        """Both the breadcrumb and the Cancel button on an edit page
        resolve a nested `_origin` back to the detail page it came from."""
        client = self._carry_origin_client()

        list_origin = quote_plus("http://testserver/admin/user/list?q=John")
        detail_url = f"http://testserver/admin/user/detail?pk=1&_origin={list_origin}"
        detail_origin = quote_plus(detail_url)
        edit_url = f"http://testserver/admin/user/edit?pk=1&_origin={detail_origin}"

        edit_response = client.get(edit_url.removeprefix("http://testserver"))
        assert edit_response.status_code == 200
        assert (
            edit_response.text.count(f'href="{detail_url.replace("&", "&amp;")}"') == 2
        )

    def test_edit_save_redirects_back_to_origin(self):
        """Saving an edit closes the loop: the redirect lands back on the
        detail page the edit was reached from."""
        client = self._carry_origin_client()

        list_origin = quote_plus("http://testserver/admin/user/list?q=John")
        detail_url = f"http://testserver/admin/user/detail?pk=1&_origin={list_origin}"
        detail_origin = quote_plus(detail_url)
        edit_url = f"http://testserver/admin/user/edit?pk=1&_origin={detail_origin}"

        save_response = client.post(
            edit_url.removeprefix("http://testserver"),
            data={"name": "John Doe Jr."},
            follow_redirects=False,
        )
        assert save_response.status_code == 303
        assert save_response.headers.get("location") == detail_url

    def test_edit_continue_editing_carries_origin_forward(self):
        """ "Save and continue editing" keeps the `_origin` the edit page
        was reached with, so the next save still returns to it."""
        client = self._carry_origin_client()

        list_origin = quote_plus("http://testserver/admin/user/list?q=John")
        edit_url = f"/admin/user/edit?pk=1&_origin={list_origin}"

        response = client.post(
            edit_url,
            data={"name": "John Doe Jr.", "_continue_editing": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == f"http://testserver/admin/user/edit?pk=1&_origin={list_origin}"
        )

    def test_edit_add_another_carries_origin_forward(self):
        """ "Save and add another" also keeps the `_origin` the edit page
        was reached with, forwarding it to the new create page."""
        client = self._carry_origin_client()

        list_origin = quote_plus("http://testserver/admin/user/list?q=John")
        edit_url = f"/admin/user/edit?pk=1&_origin={list_origin}"

        response = client.post(
            edit_url,
            data={"name": "John Doe Jr.", "_add_another": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers.get("location")
            == f"http://testserver/admin/user/create?_origin={list_origin}"
        )

    def test_internal_api_lookup_carries_no_origin(self):
        """An internal API call, e.g. a select2 relation lookup, has no
        meaningful "back" destination, so it never carries an origin."""
        client = self._carry_origin_client()

        lookup_response = client.get("/admin/_api/user/relation-lookup")
        assert lookup_response.status_code == 200
        assert (
            lookup_response.json()["items"][0]["_meta"]["detailUrl"]
            == "http://testserver/admin/user/detail?pk=1"
        )

    @pytest.mark.parametrize(
        "bad_origin",
        [
            "javascript:alert(1)",  # disallowed scheme
            "http://evil.example/x",  # cross-origin absolute URL
            "not-a-leading-slash",  # relative URL missing its leading slash
            "//evil.example/x",  # protocol-relative URL
            "/\\evil.example/x",  # backslash-trick URL
        ],
    )
    def test_malicious_origin_falls_back_to_list(self, bad_origin):
        """`safe_redirect_url` rejects a malicious or malformed `_origin`,
        falling back to the plain list URL.

        Targets pk=2, which the other carry-origin tests leave untouched,
        so a rejected page still renders normally.
        """
        client = self._carry_origin_client()

        bad_response = client.get(
            f"/admin/user/edit?pk=2&_origin={quote_plus(bad_origin)}"
        )
        assert bad_response.status_code == 200
        assert _breadcrumb_href(bad_response.text) == (
            "http://testserver/admin/user/list"
        )

    def test_safe_relative_origin_is_honored(self):
        """A safe, relative `_origin` is honored as-is by
        `safe_redirect_url`."""
        client = self._carry_origin_client()

        safe_relative_origin = "/admin/user/list?q=Terry"
        safe_response = client.get(
            f"/admin/user/edit?pk=2&_origin={quote_plus(safe_relative_origin)}"
        )
        assert safe_response.status_code == 200
        assert _breadcrumb_href(safe_response.text) == safe_relative_origin

    def test_create_carries_list_origin_through_continue_editing(self):
        """Create also carries a list origin forward, through "continue
        editing" into the resulting edit page."""
        client = self._carry_origin_client()

        list_url = "http://testserver/admin/user/list?q=John"
        list_origin = quote_plus(list_url)
        create_from_list_url = (
            f"http://testserver/admin/user/create?_origin={list_origin}"
        )

        create_response = client.get(
            create_from_list_url.removeprefix("http://testserver")
        )
        assert create_response.status_code == 200
        assert f'href="{list_url}">' in create_response.text

        continue_response = client.post(
            create_from_list_url.removeprefix("http://testserver"),
            data={"name": "New Guy", "_continue_editing": "true"},
            follow_redirects=False,
        )
        assert continue_response.status_code == 303
        assert (
            continue_response.headers.get("location")
            == f"http://testserver/admin/user/edit?pk=3&_origin={list_origin}"
        )

    def test_delete_from_detail_unwraps_nested_origin_to_list(self):
        """Deleting an item from its own detail page unwraps the nested
        origin: the detail page no longer exists once the item is gone, so
        the redirect falls through to the filtered list it was reached
        from rather than the now-dead detail URL."""
        client = self._carry_origin_client()

        list_url = "http://testserver/admin/user/list?q=John"
        list_origin = quote_plus(list_url)
        detail_url = f"http://testserver/admin/user/detail?pk=1&_origin={list_origin}"

        delete_response = client.post(
            "/admin/_api/user/row-action",
            params={"name": "delete", "pk": 1, "_origin": detail_url},
        )
        assert delete_response.status_code == 200
        assert delete_response.json() == {"redirect": list_url}

    def test_model_view_create_validation_error(self):
        class PostViewWithRestrictedTitle(PostView):
            async def validate_data(self, data: dict):
                if len(data["title"]) < 3:
                    raise FormValidationError(
                        {"title": "Ensure Post title has at least 03 characters"}
                    )

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostViewWithRestrictedTitle(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app)
        dummy_data = {
            "title": "Du",
            "content": "This is a content",
            "views": None,
            "tags": ["tag1", "tag2"],
        }
        response = client.post("/admin/post/create", data=dummy_data)
        assert response.status_code == 422
        assert "Ensure Post title has at least 03 characters" in response.text
        response = client.post("/admin/post/edit?pk=1", data=dummy_data)
        assert response.status_code == 422
        assert "Ensure Post title has at least 03 characters" in response.text

    def test_model_view_delete(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app)
        response = client.post(
            "/admin/_api/post/action", params={"name": "delete", "pks": [1, 3, 5]}
        )
        assert response.status_code == 200
        assert PostView._len() == 2
        assert PostView._all_pks() == [2, 4]

    def test_other_fields(self):
        class MyModel(TinydbBaseModel):
            score: float | None = None
            gender: str = ""
            json_field: dict | None = None

        class MyModelView(TinydbModelView):
            fields = [
                IntegerField("id"),
                FloatField("score"),
                EnumField(
                    "gender",
                    choices=("male", "female"),
                ),
                JSONField("json_field"),
            ]

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(MyModelView(MyModel))
        admin.mount_to(app)
        client = CsrfTestClient(app)

        assert client.get("admin/my-model/list").status_code == 200

        response = client.post(
            "/admin/my-model/create",
            data={"score": 3.4, "gender": "male", "json_field": '{"key":"value"}'},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView._get(1) == MyModel(
            id=1, score=3.4, gender="male", json_field={"key": "value"}
        )
        # Test Api
        response = client.get("/admin/_api/my-model/relation-lookup?pks=1")
        assert response.status_code == 200
        assert [x["id"] for x in response.json()["items"]] == [1]

        # Test edit page load
        response = client.get("/admin/my-model/edit?pk=1")
        assert response.status_code == 200

        # Test edition
        response = client.post(
            "/admin/my-model/edit?pk=1",
            data={
                "score": 5.6,
                "gender": "female",
                "json_field": '{"new_key":"new_value"}',
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView._get(1) == MyModel(
            id=1, score=5.6, gender="female", json_field={"new_key": "new_value"}
        )
        # Test None for float and invalid json
        response = client.post(
            "/admin/my-model/edit?pk=1",
            data={"score": "", "gender": "male", "json_field": "}"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert MyModelView._get(1) == MyModel(
            id=1, score=None, gender="male", json_field=None
        )

        # Test enum value error
        MyModelView._db.insert(
            MyModel(id=2, score=4.5, gender="unknown", json_field={}).to_tinydb_doc()
        )
        with pytest.raises(ValueError, match="Invalid choice value: unknown"):
            client.get("/admin/_api/my-model/relation-lookup?pks=2")

    def test_has_one_relationships(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView(User))
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/user/create").status_code == 200
        dummy_data = {"reviewer": 1, "name": "John Doe"}
        client.post("/admin/user/create", data=dummy_data)
        assert UserView._len() == 3
        assert UserView._get(3).reviewer == UserView._get(1)
        dummy_data.update({"reviewer": 2})
        assert client.get("/admin/user/edit?pk=3").status_code == 200
        client.post("/admin/user/edit?pk=3", data=dummy_data)
        assert UserView._len() == 3
        assert UserView._get(3).reviewer == UserView._get(2)
        del dummy_data["reviewer"]
        assert client.get("/admin/user/edit?pk=3").status_code == 200
        client.post("/admin/user/edit?pk=3", data=dummy_data)
        assert UserView._len() == 3
        assert UserView._get(3).reviewer is None
        assert client.get("/admin/user/edit?pk=3").status_code == 200

    def test_has_many_relationships(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(UserView(User))
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app)
        dummy_data = {"name": "John Doe", "posts": [1, 3, 4]}
        assert client.get("/admin/user/create").status_code == 200
        client.post("/admin/user/create", data=dummy_data)
        assert UserView._len() == 3
        assert UserView._get(3).posts == [PostView._get(x) for x in [1, 3, 4]]
        dummy_data.update({"posts": [2, 5]})
        assert client.get("/admin/user/edit?pk=3").status_code == 200
        client.post("/admin/user/edit?pk=3", data=dummy_data)
        assert UserView._len() == 3
        assert UserView._get(3).posts == [PostView._get(x) for x in [2, 5]]

    def test_add_link(self, link_to_google):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(link_to_google)
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

    def test_add_dropdown(self, section_dropdown):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.add_view(section_dropdown)
        admin.mount_to(app)
        assert len(admin._views) == 2
        assert admin._find_view_by_key("user") is not None
        assert admin._find_view_by_key("post") is not None
        client = TestClient(app, base_url="http://testserver")
        response = client.get("/admin")
        text = re.sub(r"\s+", " ", response.text)
        assert text.count('<li class="nav-item dropdown ">') == 1
        assert text.count('<span class="nav-link-title">') == 2
        assert (
            text.count(
                '<a href="http://testserver/admin/user/list"'
                ' class="dropdown-item">Users</a>'
            )
            == 1
        )
        assert (
            text.count(
                '<a href="http://testserver/admin/report"'
                ' class="dropdown-item">Report</a>'
            )
            == 1
        )
        assert (
            text.count(
                '<a href="https://google.com" class="dropdown-item"'
                ' target="_self">LinkToGoogle</a>'
            )
            == 1
        )

    def test_custom_view_widgets_are_rendered(self):
        async def _count_users(request):
            return 42

        widget = CardRowWidget(
            children=[
                StatWidget(title="Users", value_callback=_count_users),
            ],
        )
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(
            CustomView(menu_label="Dashboard", path="/dashboard", widget=widget)
        )
        admin.mount_to(app)
        client = TestClient(app)
        response = client.get("/admin/dashboard")

        assert response.status_code == 200
        assert "Users" in response.text
        assert "42" in response.text
        assert 'class="row row-deck row-cards"' in response.text
