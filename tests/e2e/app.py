"""End-to-end test application.

A small library admin: ``Author`` (one) to ``Book`` (many), wired up with
enough fields, filters, actions, and auth to exercise the admin's user-facing
features from a real browser via Playwright. ``build_app`` takes a database
URL so each backend's test session gets its own throwaway database.
"""

import enum
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin import ActionSelection, TabsWidget, action, flash, row_action
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin, InlineModelView, ModelView
from starlette_admin.exceptions import ActionFailed

SECRET_KEY = "e2e-test-secret"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class Base(DeclarativeBase):
    pass


class Genre(enum.StrEnum):
    FICTION = "FICTION"
    NON_FICTION = "NON_FICTION"
    SCIENCE_FICTION = "SCIENCE_FICTION"
    BIOGRAPHY = "BIOGRAPHY"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    books: Mapped[list["Book"]] = relationship(
        "Book", back_populates="author", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("authors.id"))
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(20))
    genre: Mapped[Genre] = mapped_column(Enum(Genre))
    price: Mapped[float] = mapped_column(Float)
    rating: Mapped[int] = mapped_column(Integer, default=3)
    published_at: Mapped[datetime] = mapped_column(DateTime)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    author: Mapped["Author"] = relationship("Author", back_populates="books")

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


# ── Auth ─────────────────────────────────────────────────────────────────────


class MyAuthProvider(AuthProvider):
    """Single-user session auth, just enough to gate the admin behind a login."""

    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("username") == ADMIN_USERNAME:
            return AdminUser(username=ADMIN_USERNAME)
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# ── Views ────────────────────────────────────────────────────────────────────


class BookInline(InlineModelView):
    """Lets an Author's books be added/edited/removed without leaving the
    Author create/edit form (fk_attr is auto-detected from the Book.author
    relationship)."""

    model = Book
    fields = ["title", "isbn", "genre", "price", "rating", "published_at", "in_stock"]
    # No blank row by default; tests exercise the "Add Book" button explicitly.
    extra = 0


class AuthorView(ModelView):
    fields = ["id", "name", "email", "bio", "birth_date", "is_active", "books"]
    exclude_fields_from_create = ["books"]
    exclude_fields_from_edit = ["books"]
    exclude_fields_from_import = ["books"]
    searchable_fields = ("name", "email")
    fields_default_sort = (("name", False),)
    menu_label = "Authors"
    inlines = [BookInline]


class BookView(ModelView):
    fields = [
        "id",
        "title",
        "isbn",
        "author",
        "genre",
        "price",
        "rating",
        "published_at",
        "in_stock",
    ]
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True
    menu_label = "Books"

    # Splits the create/edit form across two tabs to exercise form_layout
    # composition; save_state=False keeps the first tab active on every page
    # load, so it doesn't depend on cross-test sessionStorage state.
    form_layout = [
        TabsWidget(
            tabs=[
                ("Details", [("title", "isbn"), "author", "genre"]),
                (
                    "Pricing & Availability",
                    [("price", "rating"), "published_at", "in_stock"],
                ),
            ],
            save_state=False,
        ),
    ]
    inline_editable_fields = ["price", "rating"]

    actions = ["mark_out_of_stock", "delete"]
    row_actions = ["view", "edit", "restock", "delete"]

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: "Book"
    ) -> bool:
        if name == "restock":
            return not obj.in_stock
        return await super().is_row_action_allowed_for_obj(request, name, obj)

    @action(
        name="mark_out_of_stock",
        text="Mark selected books as out of stock",
        confirmation="Are you sure you want to mark selected books as out of stock?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-danger",
    )
    async def mark_out_of_stock_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        session: Session = request.state.session
        books = await selection.rows()
        for book in books:
            book.in_stock = False
            session.add(book)
        session.flush()
        flash(request, f"{len(books)} book(s) marked as out of stock", "success")

    @row_action(
        name="restock",
        text="Restock",
        confirmation="Mark this book as back in stock?",
        icon_class="fas fa-box",
        submit_btn_text="Yes, restock",
        submit_btn_class="btn-success",
        action_btn_class="btn-outline-success",
    )
    async def restock_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        book = await self.find_by_pk(request, pk)
        if book.in_stock:
            raise ActionFailed("This book is already in stock.")
        book.in_stock = True
        session.add(book)
        session.flush()
        flash(request, "Book restocked", "success")


def build_app(database_url: str) -> Starlette:
    """Build a fresh Starlette + starlette-admin app backed by ``database_url``."""
    engine = create_engine(database_url)

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        Base.metadata.create_all(engine)
        from tests.e2e.seed import seed_data

        seed_data(engine)
        yield

    app = Starlette(
        lifespan=lifespan,
        middleware=[Middleware(SessionMiddleware, secret_key=SECRET_KEY)],
    )

    admin = Admin(
        engine,
        title="Library Admin",
        auth_provider=MyAuthProvider(),
        secret_key=SECRET_KEY,
    )
    admin.add_view(AuthorView(Author, icon="fa fa-user-pen"))
    admin.add_view(BookView(Book, icon="fa fa-book"))
    admin.mount_to(app)

    return app
