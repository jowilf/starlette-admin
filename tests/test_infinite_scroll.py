"""Tests for infinite_scroll feature on BaseModelView."""

from typing import Optional

from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, IntegerField, StringField, TextAreaField

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Article(DummyBaseModel):
    title: str
    body: Optional[str] = ""


class ArticleView(DummyModelView):
    model = Article
    fields = (
        IntegerField("id"),
        StringField("title"),
        TextAreaField("body"),
    )
    searchable_fields = ("title",)
    sortable_fields = ("id", "title")
    infinite_scroll = True
    db = {}
    seq = 1


class ArticleViewCustomTemplate(DummyModelView):
    model = Article
    fields = (
        IntegerField("id"),
        StringField("title"),
    )
    infinite_scroll = True
    list_template = "custom_list.html"
    db = {}
    seq = 1


class TestInfiniteScroll:
    def setup_method(self, method):
        ArticleView.db.clear()
        ArticleView.seq = 1
        for i in range(1, 26):
            ArticleView.db[i] = Article(id=i, title=f"Article {i}", body=f"Body {i}")
        ArticleView.seq = 26

    def _create_app(self, view_class=ArticleView):
        app = Starlette()
        admin = BaseAdmin()
        admin.add_view(view_class)
        admin.mount_to(app)
        return app

    def test_infinite_scroll_sets_template(self):
        """When infinite_scroll=True and list_template is default, it should switch to list_infinite.html."""
        view = ArticleView()
        assert view.infinite_scroll is True
        assert view.list_template == "list_infinite.html"

    def test_infinite_scroll_preserves_custom_template(self):
        """When infinite_scroll=True but list_template is already custom, don't override."""
        view = ArticleViewCustomTemplate()
        assert view.list_template == "custom_list.html"

    def test_list_page_renders_infinite_template(self):
        """The list page should render the infinite scroll template."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/article/list")
        assert response.status_code == 200
        assert "infinite-scroll-container" in response.text
        assert "scroll-sentinel" in response.text

    def test_api_endpoint_returns_items(self):
        """The API endpoint should return paginated items for infinite scroll."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/api/article", params={"skip": 0, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 10

    def test_api_pagination(self):
        """Verify skip/limit work correctly for infinite scroll pagination."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/api/article", params={"skip": 20, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 5

    def test_model_config_includes_infinite_scroll(self):
        """The JS model config should include infiniteScroll flag."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/article/list")
        assert response.status_code == 200
        assert (
            '"infiniteScroll": true' in response.text
            or '"infiniteScroll":true' in response.text
        )

    def test_export_all_js_included(self):
        """The infinite scroll template should include export_all.js."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/article/list")
        assert response.status_code == 200
        assert "export_all.js" in response.text

    def test_list_infinite_js_included(self):
        """The infinite scroll template should include list_infinite.js."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/article/list")
        assert response.status_code == 200
        assert "list_infinite.js" in response.text

    def test_no_items_message_in_config(self):
        """The JS model config should include noItemsMessage."""
        app = self._create_app()
        client = TestClient(app)
        response = client.get("/admin/article/list")
        assert response.status_code == 200
        assert "noItemsMessage" in response.text
