"""Integration tests for contrib.tortoise.InlineModelView.

Covers FK auto-detection and normalization, plus inline create, edit, add and
delete flows through the parent form.
"""

import pytest
import pytest_asyncio
from starlette.applications import Starlette
from starlette_admin.contrib.tortoise import Admin, InlineModelView, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

from tests.integration.tortoise.utils import reset_schema, tortoise_init
from tests.utils import csrf_async_client


class Article(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=100)


class Comment(Model):
    id = fields.IntField(primary_key=True)
    article = fields.ForeignKeyField("models.Article", related_name="comments")
    author = fields.CharField(max_length=50)
    body = fields.TextField()


class Standalone(Model):
    id = fields.IntField(primary_key=True)
    label = fields.CharField(max_length=50)


class DoubleRef(Model):
    id = fields.IntField(primary_key=True)
    main = fields.ForeignKeyField("models.Article", related_name="main_refs")
    other = fields.ForeignKeyField("models.Article", related_name="other_refs")


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class ArticleView(ModelView):
    fields = ["id", "title"]
    inlines = [CommentInline]


@pytest_asyncio.fixture()
async def db(tortoise_backend):
    backend, db_url = tortoise_backend
    await tortoise_init(backend, db_url, __name__)
    await Tortoise.generate_schemas()
    yield
    await reset_schema(backend)
    await Tortoise.close_connections()


@pytest_asyncio.fixture()
async def client(db):
    admin = Admin()
    admin.add_view(ArticleView(Article))
    app = Starlette()
    admin.mount_to(app)
    async with csrf_async_client(app) as c:
        yield c


class TestFkDetection:
    async def test_auto_detects_fk_from_relation(self, db):
        admin = Admin()
        view = ArticleView(Article)
        admin.add_view(view)
        assert view._inline_instances[0].fk_attr == "article_id"

    async def test_explicit_relation_name_is_normalized(self, db):
        class _Inline(InlineModelView):
            model = Comment
            fk_attr = "article"

        class _ArticleView(ModelView):
            inlines = [_Inline]

        admin = Admin()
        view = _ArticleView(Article)
        admin.add_view(view)
        assert view._inline_instances[0].fk_attr == "article_id"

    async def test_explicit_raw_column_is_kept(self, db):
        class _Inline(InlineModelView):
            model = Comment
            fk_attr = "article_id"

        inline = _Inline(parent_view=ModelView(Article))
        assert inline.fk_attr == "article_id"

    async def test_invalid_fk_attr(self, db):
        class _Inline(InlineModelView):
            model = Comment
            fk_attr = "nope"

        with pytest.raises(ValueError, match="not a field"):
            _Inline(parent_view=ModelView(Article))

    async def test_detect_fails_without_parent_model(self, db):
        class _NakedParent:
            pass

        class _Inline(InlineModelView):
            model = Comment

        with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
            _Inline(parent_view=_NakedParent())

    async def test_detect_fails_without_relation_to_parent(self, db):
        class _Inline(InlineModelView):
            model = Standalone

        with pytest.raises(ValueError, match="has no relation pointing to"):
            _Inline(parent_view=ModelView(Article))

    async def test_detect_fails_with_multiple_relations_to_parent(self, db):
        class _Inline(InlineModelView):
            model = DoubleRef

        with pytest.raises(ValueError, match="multiple relations"):
            _Inline(parent_view=ModelView(Article))


class TestInlineCreate:
    async def test_create_page_renders_inlines(self, client):
        response = await client.get("/admin/article/create")
        assert response.status_code == 200
        assert "inline-formset" in response.text
        assert response.text.count('name="inlines.comment.0.body"') == 1
        assert response.text.count('name="inlines.comment.1.body"') == 1

    async def test_create_saves_parent_and_inlines(self, client):
        response = await client.post(
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
        assert await Article.all().count() == 1
        article = await Article.first()
        comments = await Comment.filter(article_id=article.id).order_by("author")
        assert [c.author for c in comments] == ["Alice", "Bob"]

    async def test_create_ignores_empty_extra_rows(self, client):
        response = await client.post(
            "/admin/article/create",
            data={
                "title": "Sparse",
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Only comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Comment.all().count() == 1


class TestInlineEdit:
    @pytest_asyncio.fixture(autouse=True)
    async def _seed(self, db):
        article = await Article.create(title="Draft")
        await Comment.create(article=article, author="Alice", body="Original")

    async def test_edit_page_renders_existing_inlines(self, client):
        article = await Article.first()
        response = await client.get(f"/admin/article/edit?pk={article.id}")
        assert response.status_code == 200
        assert "Original" in response.text
        assert response.text.count('name="inlines.comment.0.pk"') == 1

    async def test_edit_updates_existing_inline(self, client):
        article = await Article.first()
        comment = await Comment.first()
        response = await client.post(
            f"/admin/article/edit?pk={article.id}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.id),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Edited",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (await Comment.first()).body == "Edited"
        assert await Comment.all().count() == 1

    async def test_edit_adds_new_inline(self, client):
        article = await Article.first()
        comment = await Comment.first()
        response = await client.post(
            f"/admin/article/edit?pk={article.id}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.id),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original",
                "inlines.comment.1.author": "Bob",
                "inlines.comment.1.body": "New comment",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Comment.all().count() == 2
        new_comment = await Comment.get(author="Bob")
        assert new_comment.article_id == article.id

    async def test_edit_deletes_inline(self, client):
        article = await Article.first()
        comment = await Comment.first()
        response = await client.post(
            f"/admin/article/edit?pk={article.id}",
            data={
                "title": "Updated",
                "inlines.comment.0.pk": str(comment.id),
                "inlines.comment.0.author": "Alice",
                "inlines.comment.0.body": "Original",
                "inlines.comment.0.DELETE": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Comment.all().count() == 0

    async def test_detail_page_shows_inline_rows(self, client):
        article = await Article.first()
        response = await client.get(f"/admin/article/detail?pk={article.id}")
        assert response.status_code == 200
        assert "Original" in response.text
