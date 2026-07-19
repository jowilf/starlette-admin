import pytest
from starlette.applications import Starlette
from starlette.datastructures import FormData, ImmutableMultiDict
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    CollectionField,
    IntegerField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import BaseField
from starlette_admin.views import InlineModelView

from tests.integration.core.tinydb_model_view import (
    TinydbBaseModel,
    TinydbInlineModelView,
    TinydbModelView,
)
from tests.utils import CsrfTestClient


class Article(TinydbBaseModel):
    title: str


class Comment(TinydbBaseModel):
    article_id: int
    author: str = ""
    body: str


class CommentInline(TinydbInlineModelView):
    model = Comment
    fk_attr = "article_id"
    fields = [IntegerField("id"), StringField("author"), TextAreaField("body")]
    extra = 2
    collapsible = False

    async def validate_data(self, data: dict) -> None:
        if not data.get("body"):
            raise FormValidationError({"body": "Body is required"})


class ArticleView(TinydbModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [CommentInline]
    searchable_fields = ("title",)


class CollapsedCommentInline(TinydbInlineModelView):
    model = Comment
    fk_attr = "article_id"
    key = "collapsed-comment"
    fields = [IntegerField("id"), StringField("author"), TextAreaField("body")]
    extra = 1
    collapsed = True


class DefaultCommentInline(TinydbInlineModelView):
    model = Comment
    fk_attr = "article_id"
    key = "default-comment"
    fields = [IntegerField("id"), StringField("author"), TextAreaField("body")]
    extra = 1


class CollapsibleArticleView(TinydbModelView):
    key = "collapsible-article"
    fields = [IntegerField("id"), StringField("title")]
    inlines = [CollapsedCommentInline]


class DefaultArticleView(TinydbModelView):
    key = "default-article"
    fields = [IntegerField("id"), StringField("title")]
    inlines = [DefaultCommentInline]


@pytest.fixture()
def client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    return CsrfTestClient(app)


@pytest.fixture()
def collapsible_client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(CollapsibleArticleView(Article))
    admin.mount_to(app)
    return CsrfTestClient(app)


@pytest.fixture()
def default_client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(DefaultArticleView(Article))
    admin.mount_to(app)
    return CsrfTestClient(app)


class TestInlineCreate:
    def setup_method(self, method) -> None:
        ArticleView._db.truncate()
        CommentInline._db.truncate()

    def test_create_page_renders_inlines(self, client: TestClient) -> None:
        response = client.get("/admin/article/create")
        assert response.status_code == 200
        assert "inline-formset" in response.text
        assert "inlines.comment" in response.text
        # Two extra empty inline rows
        assert response.text.count('name="inlines.comment.0.body"') == 1
        assert response.text.count('name="inlines.comment.1.body"') == 1

    def test_create_saves_parent_and_inlines(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/create",
            data={
                "title": "Hello world",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "First comment",
                "inlines.comment.1.author": "Bob",
                "inlines.comment.1.body": "Second comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert ArticleView._len() == 1
        assert CommentInline._len() == 2

        article = ArticleView._get(1)
        assert article is not None
        assert article.title == "Hello world"

        comments = sorted(
            [CommentInline._get(pk) for pk in CommentInline._all_pks()],
            key=lambda c: c.body,
        )
        assert [c.body for c in comments] == ["First comment", "Second comment"]
        assert [c.author for c in comments] == ["Alice", "Bob"]
        assert all(c.article_id == 1 for c in comments)

    def test_create_ignores_empty_extra_rows(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/create",
            data={
                "title": "Hello world",
                "inlines.comment.0.body": "Only comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert CommentInline._len() == 1


class TestInlineCollapsible:
    def setup_method(self, method) -> None:
        ArticleView._db.truncate()
        CollapsedCommentInline._db.truncate()
        DefaultCommentInline._db.truncate()

    def test_collapsible_is_the_default(self) -> None:
        assert InlineModelView.collapsible is True
        assert InlineModelView.collapsed is False

    def test_default_inline_renders_collapsible_but_expanded(
        self, default_client: TestClient
    ) -> None:
        response = default_client.get("/admin/default-article/create")
        assert response.status_code == 200
        # collapsible defaults to True, collapsed defaults to False: the
        # toggle is present but the formset starts open ("show" class)
        assert 'aria-expanded="true"' in response.text
        assert 'id="default-comment-inline-formset"' in response.text

    def test_collapsed_inline_renders_collapsed_by_default(
        self, collapsible_client: TestClient
    ) -> None:
        response = collapsible_client.get("/admin/collapsible-article/create")
        assert response.status_code == 200
        # collapsible + collapsed formset starts hidden (no "show" class)
        assert 'aria-expanded="false"' in response.text
        assert 'id="collapsed-comment-inline-formset"' in response.text
        # fields are still rendered, just visually hidden behind the collapse
        assert response.text.count('name="inlines.collapsed-comment.0.body"') == 1

    def test_opting_out_of_collapsible_has_no_collapse_markup(
        self, client: TestClient
    ) -> None:
        response = client.get("/admin/article/create")
        assert response.status_code == 200
        assert "sa-panel-toggle" not in response.text
        assert 'id="comment-inline-formset"' not in response.text


class TestInlineEdit:
    def setup_method(self, method) -> None:
        ArticleView._db.truncate()
        CommentInline._db.truncate()
        ArticleView._db.insert(Article(title="Draft").to_tinydb_doc())
        CommentInline._db.insert(
            Comment(
                article_id=1, author="Alice", body="Original comment"
            ).to_tinydb_doc()
        )

    def test_edit_page_renders_existing_inlines(self, client: TestClient) -> None:
        response = client.get("/admin/article/edit?pk=1")
        assert response.status_code == 200
        assert "Original comment" in response.text
        assert response.text.count('name="inlines.comment.0.pk"') == 1
        # Extra rows after existing one
        assert response.text.count('name="inlines.comment.1.body"') == 1

    def test_edit_updates_existing_inline(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/edit?pk=1",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": "1",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Edited comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        article = ArticleView._get(1)
        assert article.title == "Updated"
        comment = CommentInline._get(1)
        assert comment.body == "Edited comment"
        assert comment.author == "Alice"
        assert CommentInline._len() == 1

    def test_edit_adds_new_inline(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/edit?pk=1",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": "1",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original comment",
                "inlines.comment.1.author": "Bob",
                "inlines.comment.1.body": "New comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert CommentInline._len() == 2
        bodies = {CommentInline._get(pk).body for pk in CommentInline._all_pks()}
        assert bodies == {"Original comment", "New comment"}

    def test_edit_deletes_inline(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/edit?pk=1",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": "1",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original comment",
                "inlines.comment.0.DELETE": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert CommentInline._len() == 0

    def test_create_renders_inline_validation_errors(self, client: TestClient) -> None:
        response = client.post(
            "/admin/article/create",
            data={
                "title": "Hello world",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "Body is required" in response.text


class TestInlineDetail:
    def setup_method(self, method) -> None:
        ArticleView._db.truncate()
        CommentInline._db.truncate()
        ArticleView._db.insert(Article(title="My Article").to_tinydb_doc())
        CommentInline._db.insert(
            Comment(article_id=1, author="Alice", body="First comment").to_tinydb_doc()
        )
        CommentInline._db.insert(
            Comment(article_id=1, author="Bob", body="Second comment").to_tinydb_doc()
        )

    def test_detail_page_renders_inline_table_headers(self, client: TestClient) -> None:
        response = client.get("/admin/article/detail?pk=1")
        assert response.status_code == 200
        # Inline label rendered as table heading
        assert "Comment" in response.text
        # Column headers from inline fields
        assert "Author" in response.text
        assert "Body" in response.text

    def test_detail_page_shows_existing_inline_rows(self, client: TestClient) -> None:
        response = client.get("/admin/article/detail?pk=1")
        assert response.status_code == 200
        assert "First comment" in response.text
        assert "Second comment" in response.text
        assert "Alice" in response.text
        assert "Bob" in response.text

    def test_detail_page_shows_no_items_when_empty(self, client: TestClient) -> None:
        CommentInline._db.truncate()
        response = client.get("/admin/article/detail?pk=1")
        assert response.status_code == 200
        assert "No items" in response.text

    def test_detail_page_has_no_form_inputs_for_inlines(
        self, client: TestClient
    ) -> None:
        response = client.get("/admin/article/detail?pk=1")
        assert response.status_code == 200
        # No editable inline form inputs on the detail page
        assert 'name="inlines.comment' not in response.text


class BadField(BaseField):
    async def parse_form_data(self, request, form_data):
        raise ValueError("bad field")


class EdgeArticle(TinydbBaseModel):
    title: str


class EdgeComment(TinydbBaseModel):
    article_id: int
    title: str = ""
    locked: str = ""
    tags: list[str] = []
    config: dict = {}
    bad: str = ""


class TagsInline(TinydbInlineModelView):
    model = EdgeComment
    fk_attr = "article_id"
    key = "tags"
    fields = [IntegerField("id"), TagsField("tags")]
    extra = 1


class ConfigInline(TinydbInlineModelView):
    model = EdgeComment
    fk_attr = "article_id"
    key = "config"
    fields = [
        IntegerField("id"),
        StringField("title"),
        StringField("locked", read_only=True),
        CollectionField(
            "config",
            fields=[
                StringField("key"),
                IntegerField("value"),
                StringField("secret", read_only=True),
            ],
        ),
    ]
    extra = 1


class BadInline(TinydbInlineModelView):
    model = EdgeComment
    fk_attr = "article_id"
    key = "bad"
    fields = [IntegerField("id"), BadField("bad")]
    extra = 1


class EdgeArticleView(TinydbModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [TagsInline, ConfigInline, BadInline]


@pytest.fixture()
def edge_client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(EdgeArticleView(EdgeArticle))
    admin.mount_to(app)
    return CsrfTestClient(app)


class TestInlineFormParsing:
    def setup_method(self, method) -> None:
        EdgeArticleView._db.truncate()
        TagsInline._db.truncate()
        ConfigInline._db.truncate()
        BadInline._db.truncate()

    def test_create_skips_completely_empty_inline_row(
        self, edge_client: TestClient
    ) -> None:
        response = edge_client.post(
            "/admin/edge-article/create",
            data={
                "title": "Hello",
                "inlines.tags.0.tags": "x",
                "inlines.tags.1.tags": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert TagsInline._len() == 1

    def test_create_detects_non_empty_multiple_field(
        self, edge_client: TestClient
    ) -> None:
        response = edge_client.post(
            "/admin/edge-article/create",
            data={
                "title": "Hello",
                "inlines.tags.0.tags": ["", "x"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert TagsInline._len() == 1

    def test_create_parses_collection_field_inline(
        self, edge_client: TestClient
    ) -> None:
        response = edge_client.post(
            "/admin/edge-article/create",
            data={
                "title": "Hello",
                "inlines.config.0.title": "Inline title",
                "inlines.config.0.config.key": "k",
                "inlines.config.0.config.value": "42",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert ConfigInline._len() == 1
        saved = ConfigInline._get(1)
        assert saved.title == "Inline title"
        assert saved.config == {"key": "k", "value": 42}

    def test_create_ignores_read_only_inline_fields(
        self, edge_client: TestClient
    ) -> None:
        """Read-only fields, top-level or nested in a CollectionField, are never
        parsed from submitted inline form data.
        """
        response = edge_client.post(
            "/admin/edge-article/create",
            data={
                "title": "Hello",
                "inlines.config.0.title": "Inline title",
                "inlines.config.0.locked": "should be ignored",
                "inlines.config.0.config.key": "k",
                "inlines.config.0.config.value": "42",
                "inlines.config.0.config.secret": "should be ignored",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert ConfigInline._len() == 1
        saved = ConfigInline._get(1)
        assert saved.locked == ""
        assert saved.config == {"key": "k", "value": 42}

    def test_create_renders_inline_parse_errors(self, edge_client: TestClient) -> None:
        response = edge_client.post(
            "/admin/edge-article/create",
            data={
                "title": "Hello",
                "inlines.bad.0.bad": "anything",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "bad field" in response.text

    def test_edit_renders_inline_parse_errors(self, edge_client: TestClient) -> None:
        EdgeArticleView._db.insert(EdgeArticle(title="Draft").to_tinydb_doc())
        response = edge_client.post(
            "/admin/edge-article/edit?pk=1",
            data={
                "title": "Updated",
                "inlines.bad.0.bad": "anything",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "bad field" in response.text


def test_inline_row_is_empty_checks_getlist() -> None:
    """A multiple-value field whose last item is empty but earlier items are not
    should still mark the row as non-empty.
    """
    admin = BaseAdmin()
    form = FormData(
        ImmutableMultiDict([("inlines.tags.0.tags", "x"), ("inlines.tags.0.tags", "")])
    )
    assert admin._inline_row_is_empty(TagsInline(), form, 0) is False
