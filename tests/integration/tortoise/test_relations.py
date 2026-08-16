"""Integration tests for relation handling in the Tortoise contrib.

Covers forward FK (`HasOne`), many-to-many (`HasMany`), one-to-one, backward
FK, and backward one-to-one fields: default field exposure, serialization,
create/edit through the admin forms, sorting and filtering on relations.
"""

import re

import pytest_asyncio
from starlette.applications import Starlette
from starlette_admin.contrib.tortoise import Admin, ModelView
from starlette_admin.contrib.tortoise.fields import BackwardHasOne
from starlette_admin.fields import HasMany, HasOne
from tortoise import Tortoise, fields
from tortoise.models import Model

from tests.integration.tortoise.utils import reset_schema, tortoise_init
from tests.utils import csrf_async_client


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50)


class Profile(Model):
    id = fields.IntField(primary_key=True)
    author = fields.OneToOneField("models.Author", related_name="profile")
    url = fields.CharField(max_length=100, null=True)


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50)


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=100)
    author = fields.ForeignKeyField("models.Author", related_name="posts", null=True)
    tags = fields.ManyToManyField("models.Tag", related_name="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts", "profile"]


class PostView(ModelView):
    searchable_fields = ["title", "author", "tags"]
    sortable_fields = ["id", "title", "author"]


def _list_total(html: str) -> int:
    m = re.search(r"Showing \d+ to \d+ of (\d+)", html)
    return int(m.group(1)) if m else 0


@pytest_asyncio.fixture()
async def client(tortoise_backend):
    backend, db_url = tortoise_backend
    await tortoise_init(backend, db_url, __name__)
    await Tortoise.generate_schemas()
    alice = await Author.create(name="Alice")
    await Author.create(name="Bob")
    await Profile.create(author=alice, url="https://alice.example.com")
    python = await Tag.create(name="python")
    await Tag.create(name="web")
    post = await Post.create(title="Hello", author=alice)
    await post.tags.add(python)
    await Post.create(title="Orphan")

    admin = Admin()
    admin.add_view(AuthorView(Author))
    admin.add_view(ModelView(Profile))
    admin.add_view(ModelView(Tag))
    admin.add_view(PostView(Post))
    app = Starlette()
    admin.mount_to(app)
    async with csrf_async_client(app) as c:
        yield c
    await reset_schema(backend)
    await Tortoise.close_connections()


class TestFieldConversion:
    async def test_default_fields_hide_raw_fk_column_and_backward_relations(
        self, client
    ):
        view = ModelView(Post)
        names = [f.name for f in view.fields]
        assert names == ["id", "title", "author", "tags"]
        assert isinstance(view.fields[2], HasOne)
        assert isinstance(view.fields[3], HasMany)

    async def test_backward_relations_are_read_only(self, client):
        view = AuthorView(Author)
        posts_field = next(f for f in view.fields if f.name == "posts")
        profile_field = next(f for f in view.fields if f.name == "profile")
        assert isinstance(posts_field, HasMany)
        assert posts_field.read_only
        assert isinstance(profile_field, BackwardHasOne)
        assert profile_field.read_only

    async def test_one_to_one_field_is_has_one(self, client):
        view = ModelView(Profile)
        author_field = next(f for f in view.fields if f.name == "author")
        assert isinstance(author_field, HasOne)


class TestRelationPages:
    async def test_list_shows_related_objects(self, client):
        response = await client.get("/admin/post/list")
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_detail_with_relations(self, client):
        post = await Post.filter(title="Hello").first()
        response = await client.get(f"/admin/post/detail?pk={post.id}")
        assert response.status_code == 200

    async def test_author_detail_links_backward_relations(self, client):
        author = await Author.filter(name="Alice").first()
        post = await Post.filter(title="Hello").first()
        response = await client.get(f"/admin/author/detail?pk={author.id}")
        assert response.status_code == 200
        assert f"post/detail?pk={post.id}" in response.text

    async def test_sort_by_relation_uses_raw_column(self, client):
        response = await client.get("/admin/post/list", params={"sort": "author__desc"})
        assert response.status_code == 200
        assert _list_total(response.text) == 2


class TestRelationFilters:
    async def test_relation_is_null(self, client):
        response = await client.get(
            "/admin/post/list", params={"filter": "author__is_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_relation_is_not_null(self, client):
        response = await client.get(
            "/admin/post/list", params={"filter": "author__is_not_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_to_many_relation_offers_no_filters(self, client):
        response = await client.get(
            "/admin/post/list", params={"filter": "tags__is_null"}
        )
        assert response.status_code == 400


class TestRelationForms:
    async def test_create_with_relations(self, client):
        author = await Author.filter(name="Bob").first()
        tags = await Tag.all()
        response = await client.post(
            "/admin/post/create",
            data={
                "title": "New post",
                "author": str(author.id),
                "tags": [str(t.id) for t in tags],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        post = await Post.get(title="New post").prefetch_related("author", "tags")
        assert post.author.name == "Bob"
        assert sorted(t.name for t in post.tags) == ["python", "web"]

    async def test_create_without_relations(self, client):
        response = await client.post(
            "/admin/post/create",
            data={"title": "Bare post"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        post = await Post.get(title="Bare post")
        assert post.author_id is None

    async def test_edit_replaces_relations(self, client):
        post = await Post.filter(title="Hello").first()
        bob = await Author.filter(name="Bob").first()
        web = await Tag.filter(name="web").first()
        response = await client.post(
            f"/admin/post/edit?pk={post.id}",
            data={
                "title": "Hello v2",
                "author": str(bob.id),
                "tags": [str(web.id)],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        updated = await Post.get(pk=post.id).prefetch_related("author", "tags")
        assert updated.author.name == "Bob"
        assert [t.name for t in updated.tags] == ["web"]

    async def test_edit_clears_relations(self, client):
        post = await Post.filter(title="Hello").first()
        response = await client.post(
            f"/admin/post/edit?pk={post.id}",
            data={"title": "Hello v3", "author": "", "tags": []},
            follow_redirects=False,
        )
        assert response.status_code == 303
        updated = await Post.get(pk=post.id).prefetch_related("author", "tags")
        assert updated.author is None
        assert list(updated.tags) == []
