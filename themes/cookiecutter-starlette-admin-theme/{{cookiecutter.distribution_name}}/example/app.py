"""Runnable demo for {{ cookiecutter.distribution_name }}.

Run with `uv run python example/app.py` from the project root, then open
http://localhost:8000/admin/.
"""

from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView

from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Theme

engine = create_engine(
    "sqlite:///example.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]


class ProductView(ModelView):
    fields = ["id", "name"]


@asynccontextmanager
async def lifespan(app: Starlette):
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin &rarr;</a>'),
        )
    ],
)

admin = Admin(
    engine,
    title="{{ cookiecutter.theme_name }} demo",
    secret_key="dev-only-change-me",
    theme={{ cookiecutter.class_prefix }}Theme(),
    debug=True,
)

admin.add_view(ProductView(Product))

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
