"""
01: Quickstart Example

A minimal blog administration interface demonstrating the core features of
starlette-admin with SQLAlchemy, including ModelView, SlugField, ComputedField,
and basic form validation.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from enum import StrEnum
from typing import Any

import uvicorn
from sqlalchemy import DateTime, Integer, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import (
    ComputedField,
    SlugField,
    StringField,
    TextAreaField,
    validators,
)
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///01_quickstart.sqlite",
    connect_args={"check_same_thread": False},
    echo=True,
)


@asynccontextmanager
async def lifespan(app: Starlette):
    """
    Manage the application lifecycle.

    Creates database tables and seeds initial sample data on startup.
    """
    Base.metadata.create_all(engine)
    from seed import seed_posts

    seed_posts(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Quickstart example</h2>"
                "<p>A minimal SQLAlchemy blog admin.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


class PostStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    async def __admin_repr__(self, request: Request) -> str:
        """Provide a string representation for the admin interface."""
        return self.title


async def unique_slug(request: Request, field: Any, value: Any) -> None:
    """Rejects a slug already used by another post.

    The edit form carries the current pk as a query param, so that row is
    excluded from the uniqueness check.
    """
    session: Session = request.state.session
    stmt = select(Post.id).where(Post.slug == value)
    pk = request.query_params.get("pk")
    if pk is not None:
        stmt = stmt.where(Post.id != int(pk))
    if session.execute(stmt).first() is not None:
        raise ValueError("This slug is already in use")


class PostView(ModelView):
    """
    Admin interface view for the Post model.

    Configures field visibility, searchability, default sorting, and
    computed fields (like word_count) for the admin dashboard.
    """

    fields = [
        "id",
        StringField(
            "title", required=True, validators=[validators.length(min=3, max=255)]
        ),
        SlugField(
            "slug",
            populate_from="title",
            required=True,
            copy_to_clipboard=True,
            validators=[unique_slug],
        ),
        ComputedField(
            "word_count",
            label="Word Count",
            fn=lambda post: len((post.content or "").split()),
        ),
        TextAreaField(
            "content", required=True, validators=[validators.length(min=10, max=600)]
        ),
        "status",
        "views",
        "published_at",
        "created_at",
    ]
    form_layout = [("title", "slug"), "content", ("status", "views", "published_at")]
    exclude_fields_from_create = ("word_count", "created_at")
    exclude_fields_from_edit = ("word_count", "created_at")
    searchable_fields = (
        "title",
        "slug",
        "content",
        "status",
        "views",
        "published_at",
        "created_at",
    )
    fields_default_sort = (("created_at", True),)
    search_auto_submit = True
    inline_editable_fields = ["title", "slug", "status"]


admin = Admin(
    engine, title="Quickstart example", secret_key="dev-only-change-me", debug=True
)

admin.add_view(PostView(Post, icon="fa fa-blog"))

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
