"""
06: Inline Forms Example

Demonstrates three patterns for embedding related records in a parent form
using InlineModelView.

Pattern 1: Auto-detected FK (zero config)
    Omit fk_attr on InlineModelView; starlette-admin inspects the SQLAlchemy
    relationship on the parent to find the FK column automatically.

Pattern 2: Explicit FK
    Set fk_attr = "<column_name>" when auto-detection is ambiguous or the
    relationship between parent and child is not defined.

Pattern 3: Composite FK
    Set fk_attr = ("<col1>", "<col2>") when the parent has a composite primary
    key and the child references all of them.
"""

from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, InlineModelView, ModelView

DATABASE_FILE = "06_inline_forms.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models in the inline forms example."""


# ── Pattern 1 models: single FK, auto-detected from relationship ───────────────


class Article(Base):
    """Parent model demonstrating an auto-detected foreign key relationship."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="article", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class Comment(Base):
    """Child model for an Article, with an auto-detected foreign key."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"))
    author: Mapped[str] = mapped_column(String(100), default="Anonymous")
    body: Mapped[str] = mapped_column(Text)

    article: Mapped["Article"] = relationship("Article", back_populates="comments")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.author}: {self.body[:50]}"


# ── Pattern 2 models: single FK, explicit fk_attr ─────────────────────────────


class Project(Base):
    """Parent model demonstrating an explicit foreign key relationship."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Task(Base):
    """Child model for a Project, with an explicit foreign key attribute."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


# ── Pattern 3 models: composite FK ────────────────────────────────────────────


class Order(Base):
    """Parent model demonstrating a composite primary key relationship."""

    __tablename__ = "orders"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String(100))

    lines: Mapped[list["OrderLine"]] = relationship(
        "OrderLine", back_populates="order", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Order #{self.store_id}-{self.seq} ({self.customer})"


class OrderLine(Base):
    """Child model for an Order, with a composite foreign key."""

    __tablename__ = "order_lines"

    order_store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product: Mapped[str] = mapped_column(String(100))
    qty: Mapped[int] = mapped_column(Integer, default=1)

    order: Mapped["Order"] = relationship("Order", back_populates="lines")

    __table_args__ = (
        ForeignKeyConstraint(
            ["order_store_id", "order_seq"],
            ["orders.store_id", "orders.seq"],
        ),
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Line {self.line_no}: {self.product} x {self.qty}"


# ── Pattern 1: auto-detected FK (fk_attr omitted) ─────────────────────────────


class CommentInline(InlineModelView):
    """Inline view for Comments, utilizing an auto-detected foreign key."""

    model = Comment
    # fk_attr omitted: starlette-admin detects "article_id" from Article.comments
    fields = ["id", "author", "body"]
    menu_label = "Comments"
    extra = 1


class ArticleView(ModelView):
    """Admin view for Articles, embedding Comments as an inline form."""

    fields = ["id", "title", "body"]
    inlines = [CommentInline]
    exclude_fields_from_list = ["body"]
    searchable_fields = ("title",)
    menu_label = "Articles"


# ── Pattern 2: explicit fk_attr ───────────────────────────────────────────────


class TaskInline(InlineModelView):
    """Inline view for Tasks, utilizing an explicit foreign key attribute."""

    model = Task
    fk_attr = "project_id"
    fields = [
        "id",
        "title",
        "done",
    ]
    menu_label = "Tasks"
    extra = 2


class ProjectView(ModelView):
    """Admin view for Projects, embedding Tasks as an inline form."""

    fields = ["id", "name", "description"]
    inlines = [TaskInline]
    exclude_fields_from_list = ["description"]
    searchable_fields = ("name",)
    menu_label = "Projects"


# ── Pattern 3: composite FK ───────────────────────────────────────────────────


class OrderLineInline(InlineModelView):
    """Inline view for Order Lines, utilizing composite foreign keys."""

    model = OrderLine
    fields = [
        # The foreign keys are set automatically
        "line_no",
        "product",
        "qty",
    ]
    menu_label = "Order Lines"
    extra = 1


class OrderView(ModelView):
    """Admin view for Orders, embedding Order Lines as an inline form."""

    fields = ["store_id", "seq", "customer"]
    inlines = [OrderLineInline]
    searchable_fields = ("customer",)
    menu_label = "Orders"


# ── App setup ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application lifecycle, ensuring tables are created and seeded."""
    Base.metadata.create_all(engine)
    from seed import seed_data

    seed_data(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Inline Forms example</h2>"
                "<p>Demonstrates auto-detected FK, explicit FK, and composite FK inlines.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(engine, title="Inline Forms example", secret_key="dev-only-change-me")

admin.add_view(ArticleView(Article, icon="fa fa-newspaper"))
admin.add_view(ProjectView(Project, icon="fa fa-diagram-project"))
admin.add_view(OrderView(Order, icon="fa fa-shopping-cart"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
