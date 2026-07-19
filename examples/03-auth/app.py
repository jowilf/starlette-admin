"""
03: Authentication Example

Demonstrates securing the admin interface with username/password authentication
and role-based access control (RBAC). Provides a custom AuthProvider.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import uvicorn
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import action, flash, row_action
from starlette_admin.auth import (
    AdminUser,
    AuthProvider,
    FormValidationError,
    LoginFailed,
)
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField

DATABASE_FILE = "03_auth.sqlite"
SECRET = "change-me-in-production"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=True,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models in the auth example."""


class ArticleStatus(StrEnum):
    """Enumeration of possible statuses for an article."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    WITHDRAWN = "WITHDRAWN"


class Article(Base):
    """
    SQLAlchemy model representing an article.

    Used to demonstrate role-based permissions at the field and row level.
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[ArticleStatus]

    async def __admin_repr__(self, request: Request) -> str:
        """Provide a string representation for the admin interface."""
        return self.title


# Demo user store: use a real database in production
USERS = {
    "admin": {
        "name": "Administrator",
        "password": "password",
        "roles": [
            "read",
            "create",
            "edit",
            "delete",
            "export",
            "import",
            "read_body",
            "action_make_published",
            "row_action_make_published",
        ],
    },
    "editor": {
        "name": "Editor",
        "password": "password",
        "roles": [
            "read",
            "create",
            "edit",
            "export",
            "read_body",
            "action_make_published",
            "row_action_make_published",
        ],
    },
    "viewer": {
        "name": "Viewer",
        "password": "password",
        "roles": ["read"],
    },
}


@dataclass
class MyAdminUser(AdminUser):
    """Custom AdminUser model extending the base user with roles."""

    roles: list[str] = field(default_factory=list)


class MyAuthProvider(AuthProvider):
    """
    Custom authentication provider.

    Handles login, session management, and authentication state verification.
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
    ) -> None:
        if len(username) < 3:
            raise FormValidationError({"username": "Must be at least 3 characters"})
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return MyAdminUser(username=user["name"], roles=user["roles"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


class ArticleView(ModelView):
    """
    Admin interface view for the Article model.

    Implements custom role-based permissions for viewing, editing, and
    executing actions on articles.
    """

    exclude_fields_from_list = [Article.body]
    row_actions = ["view", "make_published", "edit", "delete"]

    def can_view_detail(self, request: Request) -> bool:
        return "read" in request.state.admin_user.roles

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.admin_user.roles

    def can_export(self, request: Request) -> bool:
        return "export" in request.state.admin_user.roles

    def can_import(self, request: Request) -> bool:
        return "import" in request.state.admin_user.roles

    def can_access_field(self, request: Request, field: BaseField) -> bool:
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "action_make_published" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "row_action_make_published" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = ArticleStatus.PUBLISHED
            session.add(article)
        session.flush()
        flash(request, f"{len(pks)} article(s) marked as published", "success")

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-bullhorn",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        article = await self.find_by_pk(request, pk)
        if article.status == ArticleStatus.PUBLISHED:
            raise ActionFailed("Article is already published.")
        article.status = ArticleStatus.PUBLISHED
        session.add(article)
        session.flush()
        flash(request, "Article marked as published", "success")


@asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application startup, creating tables and seeding sample articles."""
    Base.metadata.create_all(engine)
    from seed import seed_articles

    seed_articles(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET)],
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Auth example</h2>"
                "<p>Login with <b>admin</b>, <b>editor</b>, or <b>viewer</b> "
                "and password <b>password</b>.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(
    engine,
    title="Auth example",
    auth_provider=MyAuthProvider(),
    secret_key=SECRET,
)
admin.add_view(ArticleView(Article, icon="fa fa-newspaper"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
