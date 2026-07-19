from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import I18nConfig, TimezoneConfig
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.i18n import SUPPORTED_LOCALES

DATABASE_FILE = "10_i18n_timezone.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────────


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(Author.id))
    author: Mapped["Author"] = relationship(Author, back_populates="posts")


# ── App setup ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin →</a>'),
        )
    ],
)

admin = Admin(
    engine,
    title="Example: i18n & Timezone",
    i18n_config=I18nConfig(
        default_locale="en",
        language_switcher=SUPPORTED_LOCALES,
    ),
    timezone_config=TimezoneConfig(
        default_timezone="UTC",
        database_timezone="UTC",
        timezone_switcher=[
            "UTC",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
        ],
    ),
    secret_key="dev-only-change-me",
)

admin.add_view(ModelView(Author, icon="fa fa-users"))
admin.add_view(ModelView(Post, icon="fa fa-newspaper", menu_label="Blog Posts"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
