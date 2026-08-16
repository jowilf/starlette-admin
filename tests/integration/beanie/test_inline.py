"""Integration tests for contrib.beanie.InlineModelView.

Tests cover two FK styles:
  - Plain PydanticObjectId FK (``article_id: PydanticObjectId``)
  - Beanie Link FK (``article: Link[Article]``) with auto-detection

For each style we test create/edit/detail pages, empty-row skipping, inline
update, add, and delete.
"""

import os

import pytest_asyncio
from beanie import Document, Link, PydanticObjectId, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, InlineModelView, ModelView

from tests.utils import csrf_async_client

MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "testdb_inline")

# Models: plain ObjectId FK


class Article(Document):
    title: str

    class Settings:
        collection = "beanie_inline_articles"


class Comment(Document):
    article_id: PydanticObjectId
    author: str
    body: str

    class Settings:
        collection = "beanie_inline_comments"


# Models: Link FK


class Post(Document):
    title: str

    class Settings:
        collection = "beanie_inline_posts"


class Tag(Document):
    post: Link[Post] | None = None
    label: str

    class Settings:
        collection = "beanie_inline_tags"


# Inline / view declarations


class CommentInline(InlineModelView):
    document = Comment
    fk_attr = "article_id"
    fields = ["id", "author", "body"]
    extra = 2


class ArticleView(ModelView):
    document = Article
    inlines = [CommentInline]


class TagInline(InlineModelView):
    # The 'fk_attr' is auto-detected from Link[Post].
    document = Tag
    fields = ["id", "label"]
    extra = 1


class PostView(ModelView):
    document = Post
    inlines = [TagInline]


# Fixtures


@pytest_asyncio.fixture(loop_scope="function")
async def db(mongo_url):
    mongo_client = AsyncMongoClient(host=mongo_url)
    await mongo_client.drop_database(MONGO_DATABASE)
    await init_beanie(
        database=mongo_client.get_database(MONGO_DATABASE),
        document_models=[Article, Comment, Post, Tag],
    )
    yield
    await mongo_client.drop_database(MONGO_DATABASE)
    await mongo_client.close()


@pytest_asyncio.fixture(loop_scope="function")
async def article_client(db):
    admin = Admin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    async with csrf_async_client(app) as c:
        yield c


@pytest_asyncio.fixture(loop_scope="function")
async def post_client(db):
    admin = Admin()
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    async with csrf_async_client(app) as c:
        yield c


# ── Plain ObjectId FK tests ───────────────────────────────────────────────────


class TestBeanieInlineCreate:
    async def test_create_page_renders_inlines(self, article_client):
        response = await article_client.get("/admin/article/create")
        assert response.status_code == 200
        assert "inline-formset" in response.text
        assert "inlines.comment" in response.text
        assert response.text.count('name="inlines.comment.0.body"') == 1
        assert response.text.count('name="inlines.comment.1.body"') == 1

    async def test_create_saves_parent_and_inlines(self, article_client):
        response = await article_client.post(
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
        assert await Article.count() == 1
        assert await Comment.count() == 2

        article = await Article.find_one()
        assert article.title == "Hello world"

        comments = await Comment.find(Comment.article_id == article.id).to_list()
        comments.sort(key=lambda c: c.author)
        assert [c.author for c in comments] == ["Alice", "Bob"]
        assert [c.body for c in comments] == ["First comment", "Second comment"]

    async def test_create_ignores_empty_extra_rows(self, article_client):
        response = await article_client.post(
            "/admin/article/create",
            data={
                "title": "Sparse",
                "inlines.comment.0.body": "Only comment",
                "inlines.comment.0.author": "Alice",
                # row 1 left empty
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Comment.count() == 1


class TestBeanieInlineEdit:
    @pytest_asyncio.fixture(loop_scope="function", autouse=True)
    async def _seed(self, db):
        article = Article(title="Draft")
        await article.save()
        comment = Comment(article_id=article.id, author="Alice", body="Original")
        await comment.save()

    async def test_edit_page_renders_existing_inlines(self, article_client):
        article = await Article.find_one()
        response = await article_client.get(f"/admin/article/edit?pk={article.id}")
        assert response.status_code == 200
        assert "Original" in response.text
        assert response.text.count('name="inlines.comment.0.pk"') == 1
        # extra empty row after the existing one
        assert response.text.count('name="inlines.comment.1.body"') == 1

    async def test_edit_updates_existing_inline(self, article_client):
        article = await Article.find_one()
        comment = await Comment.find_one()
        response = await article_client.post(
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
        assert (await Article.find_one()).title == "Updated"
        updated = await Comment.find_one()
        assert updated.body == "Edited"
        assert await Comment.count() == 1

    async def test_edit_adds_new_inline(self, article_client):
        article = await Article.find_one()
        comment = await Comment.find_one()
        response = await article_client.post(
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
        assert await Comment.count() == 2
        bodies = {c.body async for c in Comment.find()}
        assert bodies == {"Original", "New comment"}

    async def test_edit_deletes_inline(self, article_client):
        article = await Article.find_one()
        comment = await Comment.find_one()
        response = await article_client.post(
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
        assert await Comment.count() == 0


class TestBeanieInlineDetail:
    @pytest_asyncio.fixture(loop_scope="function", autouse=True)
    async def _seed(self, db):
        article = Article(title="My Article")
        await article.save()
        await Comment(article_id=article.id, author="Alice", body="First").save()
        await Comment(article_id=article.id, author="Bob", body="Second").save()

    async def test_detail_page_shows_inline_rows(self, article_client):
        article = await Article.find_one()
        response = await article_client.get(f"/admin/article/detail?pk={article.id}")
        assert response.status_code == 200
        assert "First" in response.text
        assert "Second" in response.text
        assert "Alice" in response.text
        assert "Bob" in response.text

    async def test_detail_page_has_no_form_inputs_for_inlines(self, article_client):
        article = await Article.find_one()
        response = await article_client.get(f"/admin/article/detail?pk={article.id}")
        assert response.status_code == 200
        assert 'name="inlines.comment' not in response.text


# ── Link FK tests (auto-detection) ────────────────────────────────────────────


class TestBeanieInlineLinkFk:
    async def test_auto_detect_fk_attr(self, db):
        """TagInline.fk_attr is auto-detected from Link[Post]."""
        admin = Admin()
        app = Starlette()
        pv = PostView(Post)
        admin.add_view(pv)
        admin.mount_to(app)
        inline = pv._inline_instances[0]
        assert inline.fk_attr == "post"

    async def test_create_saves_parent_and_link_inlines(self, post_client):
        response = await post_client.post(
            "/admin/post/create",
            data={
                "title": "My Post",
                "inlines.tag.0.label": "python",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Post.count() == 1
        assert await Tag.count() == 1

        post = await Post.find_one()
        tags = await Tag.find({"post.$id": post.id}).to_list()
        assert len(tags) == 1
        assert tags[0].label == "python"

    async def test_edit_adds_link_inline(self, post_client):
        response = await post_client.post(
            "/admin/post/create",
            data={"title": "Draft"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        post = await Post.find_one()

        response = await post_client.post(
            f"/admin/post/edit?pk={post.id}",
            data={
                "title": "Draft",
                "inlines.tag.0.label": "beanie",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Tag.count() == 1
        tags = await Tag.find({"post.$id": post.id}).to_list()
        assert tags[0].label == "beanie"
