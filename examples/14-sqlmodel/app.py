"""
14-sqlmodel: comprehensive SQLModel example.

Features demonstrated
─────────────────────
- SQLModel models with relationships and enums
- Multiple field types: Email, Color, Tags, DateTime, Boolean, TextArea, Enum
- InlineModelView: comments embedded in the Article form
- Lifecycle hooks (before_create, before_edit) for automatic timestamps
- AdminEventSubscriber for cross-view audit logging
- Batch @action and per-row @row_action (publish, archive)
- Column-level filter (DateTimeBetween on created_at)
- Export to CSV and Excel
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from models import Article, Author, Category, Comment
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import Admin
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)
from views import ArticleView, AuthorView, CategoryView, CommentView

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

DATABASE_FILE = "14_sqlmodel.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=False,
)


# ── Event subscriber ──────────────────────────────────────────────────────────


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create / update / delete event across all views."""

    @on(AdminEvent.AFTER_CREATE)
    async def on_create(self, ctx: AfterCreateContext) -> None:
        logger.info("[audit] created  resource=%s pk=%s", ctx.resource, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def on_update(self, ctx: AfterEditContext) -> None:
        logger.info("[audit] updated  resource=%s pk=%s", ctx.resource, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def on_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("[audit] deleted  resource=%s pk=%s", ctx.resource, ctx.pk)


# ── App ───────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: Starlette):
    first_run = not os.path.exists(DATABASE_FILE)
    SQLModel.metadata.create_all(engine)
    if first_run:
        from seed import seed

        with Session(engine) as session:
            seed(session)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>14: SQLModel</h2>"
                "<p>A CMS demo: relationships, inline forms, actions, filters, events.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(engine, title="SQLModel CMS", secret_key="dev-only-change-me")

admin.add_view(AuthorView(Author, icon="fa fa-users"))
admin.add_view(CategoryView(Category, icon="fa fa-folder", menu_label="Categories"))
admin.add_view(ArticleView(Article, icon="fa fa-blog"))
admin.add_view(CommentView(Comment, icon="fa fa-comments"))

admin.events.subscribe(AuditSubscriber())

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
