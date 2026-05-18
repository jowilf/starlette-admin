from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, IntegerField, StringField

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Article(DummyBaseModel):
    title: str
    content: str = ""


class ArticleView(DummyModelView):
    model = Article
    fields = (
        IntegerField("id"),
        StringField("title"),
        StringField("content"),
    )


class TestReturnUrl:
    def setup_method(self):
        ArticleView.db = {}
        ArticleView.seq = 1
        app = Starlette()
        admin = BaseAdmin()
        admin.add_view(ArticleView)
        admin.mount_to(app)
        self.client = TestClient(app)
        # Create an article
        self.client.post(
            "/admin/article/create",
            data={"title": "Test", "content": "Hello"},
            follow_redirects=False,
        )

    def test_edit_with_valid_return_url(self):
        """Edit POST with valid returnTo redirects to that URL."""
        return_url = "/admin/article/list?page=2&search=test"
        response = self.client.post(
            "/admin/article/edit/1",
            data={"title": "Updated", "content": "World", "returnTo": return_url},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == return_url

    def test_edit_with_malicious_return_url(self):
        """Edit POST with external returnTo falls back to list URL."""
        response = self.client.post(
            "/admin/article/edit/1",
            data={
                "title": "Updated",
                "content": "World",
                "returnTo": "https://evil.com/steal",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin/article/list" in response.headers["location"]
        assert "evil.com" not in response.headers["location"]

    def test_edit_with_protocol_relative_return_url(self):
        """Edit POST with // prefix returnTo falls back to list URL."""
        response = self.client.post(
            "/admin/article/edit/1",
            data={
                "title": "Updated",
                "content": "World",
                "returnTo": "//evil.com/admin",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "evil.com" not in response.headers["location"]

    def test_edit_without_return_url(self):
        """Edit POST without returnTo defaults to list URL."""
        response = self.client.post(
            "/admin/article/edit/1",
            data={"title": "Updated", "content": "World"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin/article/list" in response.headers["location"]

    def test_edit_continue_editing_ignores_return_url(self):
        """Edit with _continue_editing ignores returnTo."""
        response = self.client.post(
            "/admin/article/edit/1",
            data={
                "title": "Updated",
                "content": "World",
                "returnTo": "/admin/article/list?page=2",
                "_continue_editing": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin/article/edit/1" in response.headers["location"]

    def test_create_with_valid_return_url(self):
        """Create POST with valid returnTo redirects to that URL."""
        return_url = "/admin/article/list?page=1&search=foo"
        response = self.client.post(
            "/admin/article/create?returnTo=" + return_url,
            data={"title": "New", "content": "Body", "returnTo": return_url},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == return_url

    def test_create_with_malicious_return_url(self):
        """Create POST with external returnTo falls back to list URL."""
        response = self.client.post(
            "/admin/article/create",
            data={
                "title": "New",
                "content": "Body",
                "returnTo": "https://evil.com",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "evil.com" not in response.headers["location"]
        assert "/admin/article/list" in response.headers["location"]

    def test_edit_get_passes_return_url_to_template(self):
        """Edit GET with returnTo query param renders it in the page."""
        return_url = "/admin/article/list?page=2"
        response = self.client.get(
            f"/admin/article/edit/1?returnTo={return_url}"
        )
        assert response.status_code == 200
        assert return_url in response.text

    def test_create_get_passes_return_url_to_template(self):
        """Create GET with returnTo query param renders it in the page."""
        return_url = "/admin/article/list?page=3"
        response = self.client.get(
            f"/admin/article/create?returnTo={return_url}"
        )
        assert response.status_code == 200
        assert return_url in response.text
