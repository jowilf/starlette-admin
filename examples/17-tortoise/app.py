"""
17-tortoise: Tortoise ORM + SQLite example.

Features demonstrated
─────────────────────
- Tortoise models with FK, one-to-one and many-to-many relations
- Automatic field conversion (enums, JSON, dates, auto timestamps)
- InlineModelView: comments embedded in the Post form
- Backward relations rendered read-only on the Author view
- Full-text search, sorting and the filter builder
"""

import datetime
import os
from contextlib import asynccontextmanager

import uvicorn
from models import Author, AuthorProfile, Comment, Post, PostStatus, Tag
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.tortoise import Admin
from tortoise import Tortoise
from views import AuthorProfileView, AuthorView, PostView, TagView

DB_URL: str = os.environ.get("DB_URL", "sqlite://blog.db")


async def seed() -> None:
    """Populate the database on first run so the admin is not empty."""
    if await Author.all().count() > 0:
        return
    alice = await Author.create(
        name="Alice",
        email="alice@example.com",
        bio="Writes about Python.",
        joined_on=datetime.date(2023, 5, 1),
    )
    bob = await Author.create(name="Bob", email="bob@example.com")
    await AuthorProfile.create(author=alice, website="https://alice.example.com")
    python, web = (
        await Tag.create(name="python"),
        await Tag.create(name="web"),
    )
    post = await Post.create(
        title="Hello Tortoise",
        content="Using Tortoise ORM with starlette-admin.",
        status=PostStatus.PUBLISHED,
        published=True,
        views=42,
        metadata={"featured": True},
        author=alice,
    )
    await post.tags.add(python, web)
    await Comment.create(post=post, author_name="Bob", body="Nice write-up!")
    draft = await Post.create(
        title="Drafting ideas", content="Work in progress.", author=bob
    )
    await draft.tags.add(python)


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["models"]})
    await Tortoise.generate_schemas()
    await seed()
    yield
    await Tortoise.close_connections()


async def homepage(request):
    return HTMLResponse('<a href="/admin">Open the admin interface</a>')


app = Starlette(routes=[Route("/", homepage)], lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me-in-production")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(AuthorProfileView(AuthorProfile, icon="fa fa-id-card"))
admin.add_view(TagView(Tag, icon="fa fa-tags"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, port=8081)
