from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import ComputedField, SlugField
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///11_sqla_pydantic.sqlite",
    connect_args={"check_same_thread": False},
    echo=True,
)


class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="user")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(User.id))
    user: Mapped["User"] = relationship(User, back_populates="posts")


# ── Pydantic schemas ────────────────────────────────────────────────────────────


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    user: User
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v


# ── Views ───────────────────────────────────────────────────────────────────────


class PostView(ModelView):
    """Post view with a slug and a word count derived from content."""

    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "user",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "user", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


# ── App ─────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin →</a>'),
        )
    ],
)

admin = Admin(engine, title="SQLA + Pydantic", secret_key="dev-only-change-me")

admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
