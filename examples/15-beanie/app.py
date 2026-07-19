"""
15-beanie: comprehensive Beanie + MongoDB example.

Features demonstrated
─────────────────────
- Beanie Documents with Link relationships and enums
- Multiple field types: Email, Color, Tags, DateTime, Boolean, TextArea, Enum
- ImageField with LocalStorage: book cover photo
- FileField with LocalStorage: sample PDF preview
- Custom file-type validator (filetype library)
- InlineModelView: loans embedded in the Member form
- Lifecycle hooks (before_create) for automatic timestamps
- AdminEventSubscriber for cross-view audit logging
- Batch @action and per-row @row_action (mark_returned, mark_overdue)
- Column-level filter (DateTimeBetween on loan_date)
- Export to CSV and Excel
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from beanie import init_beanie
from models import Book, Genre, Loan, Member
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.beanie import Admin
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)
from views import BookView, GenreView, LoanView, MemberView

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE: str = os.environ.get("MONGO_DATABASE", "beanie_library")

ALL_DOCUMENTS = [Genre, Book, Member, Loan]

mongo_client = AsyncMongoClient(MONGO_URI)


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
    await init_beanie(
        database=mongo_client.get_database(MONGO_DATABASE),
        document_models=ALL_DOCUMENTS,
    )
    if await Genre.find().count() == 0:
        from seed import seed

        await seed()
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>15: Beanie Library</h2>"
                "<p>A library catalog demo: genres, books, members, loans, "
                "relationships, inline forms, actions, filters, events, "
                "image &amp; file uploads.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(title="Beanie Library", secret_key="dev-only-change-me")

admin.add_view(GenreView(Genre, icon="fa fa-tags"))
admin.add_view(BookView(Book, icon="fa fa-book"))
admin.add_view(MemberView(Member, icon="fa fa-users"))
admin.add_view(LoanView(Loan, icon="fa fa-clipboard-list"))

admin.events.subscribe(AuditSubscriber())

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
