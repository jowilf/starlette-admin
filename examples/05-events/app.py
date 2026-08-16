"""
05: Events Example

Demonstrates five ways to hook into the admin lifecycle.

Pattern 1: Hook overrides on ModelView
    Override before_create / before_edit on a view subclass to inject
    automatic fields before the record is written to the database.
    after_edit_committed shows the post-commit hook, which fires only once
    the edit transaction has been durably committed.

Pattern 2: AdminEventSubscriber with @on decorator
    Subclass AdminEventSubscriber, decorate methods with @on(AdminEvent.*),
    then call admin.events.subscribe(). The subscriber receives a typed
    context object (AfterCreateContext, AfterEditContext, etc.) after the
    database operation completes.

Pattern 3: Direct handler registration (admin-wide)
    Pass a coroutine to admin.events.on() to handle a single event type
    across all views without creating a subscriber class.

Pattern 4: View-scoped handler via view.events.on()
    Register a handler directly on an individual view's EventBus.
    The handler only fires for that view, not for other views.

Pattern 5: View-scoped subscriber via view.events.subscribe()
    Same as Pattern 2 but subscribed on a single view's EventBus instead of
    admin.events. The subscriber class only receives events from that view.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
import uvicorn
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    AfterExportContext,
    AfterImportContext,
    BeforeDeleteContext,
    BeforeEditContext,
    BeforeExportContext,
    BeforeImportContext,
    on,
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

DATABASE_FILE = "05_events.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models in the events example."""


class Post(Base):
    """SQLAlchemy model representing a blog post."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class Comment(Base):
    """SQLAlchemy model representing a comment on a blog post."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.author}: {self.body[:50]}"


class AuditLog(Base):
    """SQLAlchemy model representing an audit log entry for system events."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(50))
    view_key: Mapped[str] = mapped_column(String(100))
    record_pk: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


# ── Pattern 1: Hook overrides on ModelView ────────────────────────────────────


class PostView(ModelView):
    """Admin interface for the Post model, demonstrating hook overrides."""

    exclude_fields_from_list = ["content"]
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """Auto-stamp created_at before the new record is inserted."""
        obj.created_at = datetime.utcnow()

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """Stamp updated_at on every edit before the record is updated."""
        obj.updated_at = datetime.utcnow()

    async def after_edit_committed(self, request: Request, obj: Any) -> None:
        """Fires once the edit transaction is durably committed.

        Unlike after_edit, this runs after the database commit, so it's the
        right place for external side effects (emails, webhooks) that should
        only happen if the change actually persisted.
        """
        logger.info("post_after_edit_committed", pk=obj.id, title=obj.title)


class CommentView(ModelView):
    """Admin interface for the Comment model, demonstrating hook overrides."""

    exclude_fields_from_list = ["body"]
    exclude_fields_from_create = ["created_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """Auto-stamp created_at before the new comment is inserted."""
        obj.created_at = datetime.utcnow()


# ── Pattern 2: AdminEventSubscriber with @on ──────────────────────────────────


class AuditSubscriber(AdminEventSubscriber):
    """Persists an AuditLog row after every create, update, delete, export, or import.

    Create/update/delete use the *_committed variants because the SQLAlchemy
    backend defers the commit of request.state.session until the end of the
    request (see DBSessionMiddleware). AFTER_CREATE/AFTER_EDIT/AFTER_DELETE
    fire while that transaction is still open.
    """

    @on(AdminEvent.AFTER_CREATE_COMMITTED)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        title = getattr(ctx.obj, "title", None)
        detail = (
            f"Created {ctx.view_key!r}"
            + (f": {title!r}" if title else "")
            + f" (pk={ctx.pk})"
        )
        _write_audit(ctx.event, ctx.view_key, str(ctx.pk), detail, ctx.request)

    @on(AdminEvent.AFTER_EDIT_COMMITTED)
    async def record_update(self, ctx: AfterEditContext) -> None:
        title = getattr(ctx.obj, "title", None)
        detail = (
            f"Updated {ctx.view_key!r}"
            + (f": {title!r}" if title else "")
            + f" (pk={ctx.pk})"
        )
        _write_audit(ctx.event, ctx.view_key, str(ctx.pk), detail, ctx.request)

    @on(AdminEvent.AFTER_DELETE_COMMITTED)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        title = getattr(ctx.obj, "title", None)
        detail = (
            f"Deleted {ctx.view_key!r}"
            + (f": {title!r}" if title else "")
            + f" (pk={ctx.pk})"
        )
        _write_audit(ctx.event, ctx.view_key, str(ctx.pk), detail, ctx.request)

    @on(AdminEvent.AFTER_EXPORT)
    async def record_export(self, ctx: AfterExportContext) -> None:
        detail = f"Exported {ctx.row_count} row(s) from {ctx.view_key!r} as {ctx.export_type.extension}"
        _write_audit(ctx.event, ctx.view_key, "", detail, ctx.request)

    @on(AdminEvent.AFTER_IMPORT)
    async def record_import(self, ctx: AfterImportContext) -> None:
        detail = (
            f"Imported {ctx.row_count} row(s) into {ctx.view_key!r} as {ctx.import_type.extension}"
            + (f" ({ctx.error_count} error(s))" if ctx.error_count else "")
        )
        _write_audit(ctx.event, ctx.view_key, "", detail, ctx.request)


def _write_audit(
    event: AdminEvent | str,
    view_key: str,
    pk: str,
    detail: str,
    request: Request,
) -> None:
    client = request.client
    actor = request.headers.get("x-forwarded-for") or (
        client.host if client else "unknown"
    )
    event_str = event.value if isinstance(event, AdminEvent) else str(event)
    with Session(engine) as session:
        session.add(
            AuditLog(
                event=event_str,
                view_key=view_key,
                record_pk=pk,
                detail=detail,
                actor=actor,
                created_at=datetime.utcnow(),
            )
        )
        session.commit()


# ── Pattern 3: Direct handler registration (admin-wide) ───────────────────────


async def warn_before_delete(ctx: BeforeDeleteContext) -> None:
    """Admin-wide handler: warns before a row is deleted, in any view."""
    logger.warning("before_delete", view_key=ctx.view_key, pk=ctx.pk)


async def warn_before_export(ctx: BeforeExportContext) -> None:
    """Same handler style, registered for exports instead of deletes."""
    logger.warning("before_export", view_key=ctx.view_key, export_type=ctx.export_type)


async def warn_before_import(ctx: BeforeImportContext) -> None:
    """Same handler style, registered for imports instead of deletes."""
    logger.warning("before_import", view_key=ctx.view_key, import_type=ctx.import_type)


# ── Pattern 4: View-scoped handler via view.events.on() ───────────────────────


async def log_post_before_update(ctx: BeforeEditContext) -> None:
    """Registered on post_view.events; fires only for Post edits."""
    logger.info("post_before_update", pk=ctx.pk, changed_fields=list(ctx.data.keys()))


# ── Pattern 5: View-scoped subscriber via view.events.subscribe() ─────────────


class CommentModerationSubscriber(AdminEventSubscriber):
    """Logs moderation-relevant events only for the Comment view."""

    @on(AdminEvent.AFTER_CREATE)
    async def on_comment_created(self, ctx: AfterCreateContext) -> None:
        logger.info(
            "comment_created",
            pk=ctx.pk,
            author=getattr(ctx.obj, "author", None),
            approved=getattr(ctx.obj, "approved", None),
        )

    @on(AdminEvent.AFTER_EDIT)
    async def on_comment_updated(self, ctx: AfterEditContext) -> None:
        logger.info(
            "comment_updated",
            pk=ctx.pk,
            approved=getattr(ctx.obj, "approved", None),
        )


# ── Read-only audit-log view ──────────────────────────────────────────────────


class AuditLogView(ModelView):
    """Read-only admin interface for viewing audit logs."""

    fields_default_sort = [("created_at", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


# ── App setup ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application lifecycle, ensuring database tables are created."""
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Events example</h2>"
                "<p>Demonstrates hooks, event subscribers, and direct handler registration.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(engine, title="Events example", secret_key="dev-only-change-me")

post_view = PostView(Post, icon="fa fa-blog")
comment_view = CommentView(Comment, icon="fa fa-comments")

admin.add_view(post_view)
admin.add_view(comment_view)
admin.add_view(AuditLogView(AuditLog, icon="fa fa-clipboard-list"))

# Pattern 2: subscribe the audit logger across all views
admin.events.subscribe(AuditSubscriber())

# Pattern 3: direct registration for delete/export/import warnings, all views
admin.events.on(AdminEvent.BEFORE_DELETE, warn_before_delete)
admin.events.on(AdminEvent.BEFORE_EXPORT, warn_before_export)
admin.events.on(AdminEvent.BEFORE_IMPORT, warn_before_import)

# Pattern 4: view-scoped: only fires when a Post is about to be updated
post_view.events.on(AdminEvent.BEFORE_EDIT, log_post_before_update)

# Pattern 5: view-scoped subscriber: only fires for Comment events
comment_view.events.subscribe(CommentModerationSubscriber())

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
