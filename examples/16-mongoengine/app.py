"""
16-mongoengine: comprehensive MongoEngine + MongoDB example.

Features demonstrated
─────────────────────
- MongoEngine Documents with ReferenceField relationships and enums
- Multiple field types: Email, Color, Tags, DateTime, Boolean, TextArea, Enum
- ImageField with GridFS: podcast cover art (with thumbnail)
- FileField with GridFS: podcast trailer audio
- me.EnumField for status and role fields (auto-converts to sa.EnumField)
- InlineModelView: episodes embedded in the Podcast form
- Lifecycle hooks (before_create) for automatic timestamps
- AdminEventSubscriber for cross-view audit logging
- Batch @action and per-row @row_action (publish, archive)
- Column-level filter (DateTimeBetween on published_at)
- Export to CSV and Excel
"""

import logging
import os
from contextlib import asynccontextmanager

import mongoengine as me
import uvicorn
from models import Category, Episode, Host, Podcast
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.mongoengine import Admin
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)
from views import CategoryView, EpisodeView, HostView, PodcastView

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE: str = os.environ.get("MONGO_DATABASE", "mongoengine_podcast")


# ── Event subscriber ──────────────────────────────────────────────────────────


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create / update / delete event across all views."""

    @on(AdminEvent.AFTER_CREATE)
    async def on_create(self, ctx: AfterCreateContext) -> None:
        logger.info("[audit] created  view_key=%s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def on_update(self, ctx: AfterEditContext) -> None:
        logger.info("[audit] updated  view_key=%s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def on_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("[audit] deleted  view_key=%s pk=%s", ctx.view_key, ctx.pk)


# ── App ───────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db=MONGO_DATABASE, host=MONGO_URI)
    if Category.objects.count() == 0:
        from seed import seed

        seed()
    yield
    me.disconnect()


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>16: MongoEngine Podcast</h2>"
                "<p>A podcast platform demo: categories, podcasts, hosts, episodes, "
                "GridFS image &amp; file uploads, inline forms, actions, filters, "
                "enum fields, and audit events.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(title="Podcast Admin", secret_key="dev-only-change-me")

admin.add_view(CategoryView(Category, icon="fa fa-tags", menu_label="Categories"))
admin.add_view(PodcastView(Podcast, icon="fa fa-podcast"))
admin.add_view(HostView(Host, icon="fa fa-microphone"))
admin.add_view(EpisodeView(Episode, icon="fa fa-play-circle"))

admin.events.subscribe(AuditSubscriber())

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
