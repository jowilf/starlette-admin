import random
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from sqlalchemy import DateTime, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.theme import DefaultTheme, TablerSettings

engine = create_engine(
    "sqlite:///08_themes.sqlite",
    connect_args={"check_same_thread": False},
)


def random_theme() -> TablerSettings:
    return TablerSettings(
        base=random.choice(["slate", "gray", "zinc", "neutral", "stone"]),
        primary=random.choice(
            ["azure", "indigo", "purple", "yellow", "lime", "green", "teal", "cyan"]
        ),
        radius=random.choice([0, 0.5, 1, 1.5, 2]),
        mode="light",
    )


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    title="Example: Themes",
    theme=DefaultTheme(settings=random_theme()),
    secret_key="dev-only-change-me",
)

admin.add_view(ModelView(Post, icon="fa fa-blog"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
