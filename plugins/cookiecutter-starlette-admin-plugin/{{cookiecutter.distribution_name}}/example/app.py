"""Runnable demo for {{ cookiecutter.distribution_name }}.

This script mounts an in-memory-backed SQLAlchemy admin with the plugin registered. Run with `uv run python example/app.py` from the project root, then open http://localhost:8000/admin/.
"""

from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView

from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Plugin
{% if cookiecutter.include_example_field == "yes" %}
from {{ cookiecutter.package_slug }}.fields import {{ cookiecutter.class_prefix }}SliderField
{% endif %}

engine = create_engine(
    "sqlite:///example.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]
{% if cookiecutter.include_example_field == "yes" %}
    discount: Mapped[int] = mapped_column(Integer, default=0)
{% endif %}


class ProductView(ModelView):
    fields = [
        "id",
        "name",
{% if cookiecutter.include_example_field == "yes" %}
        {{ cookiecutter.class_prefix }}SliderField("discount"),
{% endif %}
    ]
{% if cookiecutter.include_example_field == "yes" %}
    inline_editable_fields = ["discount"]
{% endif %}


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
    title="{{ cookiecutter.plugin_name }} demo",
    secret_key="dev-only-change-me",
    plugins=[{{ cookiecutter.class_prefix }}Plugin()],
    debug=True,
)

admin.add_view(ProductView(Product))

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
