"""
05: Custom Fields Example

An employee directory demonstrating two custom list-page fields:
`StatusBadgeField` (a colored presence badge) and `AvatarNameField`
(an avatar image rendered next to the employee's name).
"""

from contextlib import asynccontextmanager
from datetime import date

import uvicorn
from fields import AvatarNameField, StatusBadgeField
from sqlalchemy import JSON, Date, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import EnumField, ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine(
    "sqlite:///advanced_05_custom_fields.sqlite",
    connect_args={"check_same_thread": False},
    echo=True,
)

avatars_storage = LocalStorage(base_dir="uploads/")


@asynccontextmanager
async def lifespan(app: Starlette):
    """
    Manage the application lifecycle.

    Creates database tables and seeds initial sample data on startup.
    """
    Base.metadata.create_all(engine)
    from seed import seed_employees

    seed_employees(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Custom fields example</h2>"
                "<p>An employee directory with a status badge and an avatar/name field.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        ),
    ],
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


class Employee(Base):
    """SQLAlchemy model representing an employee."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    avatar: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date] = mapped_column(Date)
    department: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="Offline")

    async def __admin_repr__(self, request: Request) -> str:
        """Provide a string representation for the admin interface."""
        return self.name


class EmployeeView(ModelView):
    """
    Admin interface view for the Employee model.

    Combines `avatar` into the `name` column via `AvatarNameField` and
    renders `status` as a colored badge via `StatusBadgeField`.
    """

    fields = [
        "id",
        ImageField(
            "avatar",
            storage=avatars_storage,
            upload_folder="avatars",
            exclude_from_list=True,
        ),
        AvatarNameField(avatars_storage=avatars_storage),
        "city",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
        "start_date",
        EnumField(
            "department",
            choices=["Engineering", "Design", "Sales", "Support", "Marketing"],
        ),
    ]
    exclude_fields_from_list = ("id",)
    fields_default_sort = ("name",)


admin = Admin(
    engine, title="Custom fields example", secret_key="dev-only-change-me", debug=True
)

admin.add_view(EmployeeView(Employee, icon="fa fa-users"))

admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
