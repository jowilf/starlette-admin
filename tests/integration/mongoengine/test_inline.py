import mongoengine as me
import pytest
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, InlineModelView, ModelView

from tests.utils import CsrfTestClient


class Article(me.Document):
    title = me.StringField(required=True)

    meta = {"collection": "inline_test_articles"}


class Comment(me.Document):
    article = me.ReferenceField(Article)
    author = me.StringField()
    body = me.StringField()

    meta = {"collection": "inline_test_comments"}


class CommentInline(InlineModelView):
    document = Comment
    fields = ["id", "author", "body"]
    extra = 2


class ArticleView(ModelView):
    document = Article
    inlines = [CommentInline]


@pytest.fixture(autouse=True)
def _db(mongo_url):
    connect(host=mongo_url, uuidRepresentation="standard")
    yield
    Article.drop_collection()
    Comment.drop_collection()
    disconnect()


@pytest.fixture()
def client():
    admin = Admin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    return CsrfTestClient(app, base_url="http://testserver")


class TestMongoInlineCreate:
    def test_create_page_renders_inlines(self, client):
        response = client.get("/admin/article/create")
        assert response.status_code == 200
        assert "inline-formset" in response.text
        assert "inlines.comment" in response.text
        assert response.text.count('name="inlines.comment.0.body"') == 1
        assert response.text.count('name="inlines.comment.1.body"') == 1

    def test_create_saves_parent_and_inlines(self, client):
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
        assert Article.objects.count() == 1
        assert Comment.objects.count() == 2

        article = Article.objects.first()
        assert article.title == "Hello world"

        comments = list(Comment.objects(article=article).order_by("author"))
        assert [c.author for c in comments] == ["Alice", "Bob"]
        assert [c.body for c in comments] == ["First comment", "Second comment"]

    def test_create_ignores_empty_extra_rows(self, client):
        response = client.post(
            "/admin/article/create",
            data={
                "title": "Hello world",
                "inlines.comment.0.body": "Only comment",
                # The first row is left empty.
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Comment.objects.count() == 1


class TestMongoInlineEdit:
    @pytest.fixture(autouse=True)
    def _seed(self):
        article = Article(title="Draft").save()
        Comment(article=article, author="Alice", body="Original comment").save()

    def test_edit_page_renders_existing_inlines(self, client):
        article_id = Article.objects.first().pk
        response = client.get(f"/admin/article/edit?pk={article_id}")
        assert response.status_code == 200
        assert "Original comment" in response.text
        assert response.text.count('name="inlines.comment.0.pk"') == 1
        # An extra empty row is added after the existing one.
        assert response.text.count('name="inlines.comment.1.body"') == 1

    def test_edit_updates_existing_inline(self, client):
        article = Article.objects.first()
        comment = Comment.objects.first()
        response = client.post(
            f"/admin/article/edit?pk={article.pk}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.pk),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Edited comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        updated_article = Article.objects.first()
        assert updated_article.title == "Updated"
        updated_comment = Comment.objects.first()
        assert updated_comment.body == "Edited comment"
        assert Comment.objects.count() == 1

    def test_edit_adds_new_inline(self, client):
        article = Article.objects.first()
        comment = Comment.objects.first()
        response = client.post(
            f"/admin/article/edit?pk={article.pk}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.pk),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original comment",
                "inlines.comment.1.author": "Bob",
                "inlines.comment.1.body": "New comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Comment.objects.count() == 2
        bodies = {c.body for c in Comment.objects.all()}
        assert bodies == {"Original comment", "New comment"}

    def test_edit_deletes_inline(self, client):
        article = Article.objects.first()
        comment = Comment.objects.first()
        response = client.post(
            f"/admin/article/edit?pk={article.pk}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.pk),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original comment",
                "inlines.comment.0.DELETE": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Comment.objects.count() == 0


class TestMongoInlineDetail:
    @pytest.fixture(autouse=True)
    def _seed(self):
        article = Article(title="My Article").save()
        Comment(article=article, author="Alice", body="First comment").save()
        Comment(article=article, author="Bob", body="Second comment").save()

    def test_detail_page_shows_existing_inline_rows(self, client):
        article_id = Article.objects.first().pk
        response = client.get(f"/admin/article/detail?pk={article_id}")
        assert response.status_code == 200
        assert "First comment" in response.text
        assert "Second comment" in response.text
        assert "Alice" in response.text
        assert "Bob" in response.text

    def test_detail_page_has_no_form_inputs_for_inlines(self, client):
        article_id = Article.objects.first().pk
        response = client.get(f"/admin/article/detail?pk={article_id}")
        assert response.status_code == 200
        assert 'name="inlines.comment' not in response.text
