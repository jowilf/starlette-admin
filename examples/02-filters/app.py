"""
02: Filters Example

Demonstrates custom and built-in filters for various field types, including
overriding default filter sets and implementing custom filter logic.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

import uvicorn
from filters import ActiveThisMonthFilter
from sqlalchemy import JSON, DateTime, Integer, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    IntegerField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    IsNotNullFilter,
    IsNullFilter,
    NumericEqualFilter,
)

engine = create_engine(
    "sqlite:///02_filters.sqlite",
    connect_args={"check_same_thread": False},
    echo=True,
)


class Base(DeclarativeBase):
    pass


class ProductStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class Product(Base):
    """
    Product model demonstrating various SQLAlchemy column types
    for filtering scenarios.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[ProductStatus]
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        """String representation of the Product model."""
        return self.name


class ProductView(ModelView):
    """
    Admin interface for the Product model, showcasing advanced filtering capabilities.
    """

    fields = [
        IntegerField("id"),
        # name + status use default filter sets from the registry (no override needed)
        StringField("name"),
        EnumField("status", enum=ProductStatus),
        # Explicit override: narrow price to only the most useful numeric filters.
        DecimalField(
            "price", filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter]
        ),
        # TagsField has no default registry entry; explicitly allow null checks.
        TagsField("tags", filters=[IsNullFilter, IsNotNullFilter]),
        # DateTimeField gets a custom filter bolted on alongside the built-in two.
        DateTimeField(
            "created_at",
            filters=[DateTimeBetweenFilter, DateInPastFilter, ActiveThisMonthFilter],
        ),
    ]
    exclude_fields_from_create = ("created_at",)
    exclude_fields_from_edit = ("created_at",)
    fields_default_sort = (("created_at", True),)
    inline_editable_fields = ("tags", "status")


@asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application startup, creating tables and seeding sample products."""
    Base.metadata.create_all(engine)
    from seed import seed_products

    seed_products(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Filters example</h2>"
                "<p>Product inventory catalogue with filter builder demo.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(engine, title="Filters example", secret_key="dev-only-change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
