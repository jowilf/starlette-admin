"""Runnable demo for starlette-admin-geospatial.

Mounts an in-memory-backed SQLAlchemy admin with the plugin registered.
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

from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin_geospatial.fields import GeospatialRatingField

engine = create_engine(
    "sqlite:///example.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]
    rating: Mapped[int] = mapped_column(Integer, default=0)


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        GeospatialRatingField("rating"),
    ]
    inline_editable_fields = ["rating"]


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
    title="Geospatial demo",
    secret_key="dev-only-change-me",
    plugins=[GeospatialPlugin()],
    debug=True,
)

admin.add_view(ProductView(Product))

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
