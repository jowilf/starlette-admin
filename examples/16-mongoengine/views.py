from datetime import UTC, datetime
from typing import Any

from models import Episode, EpisodeStatus, HostRole, PodcastStatus
from starlette.requests import Request
from starlette_admin import (
    BooleanField,
    ColorField,
    DateTimeField,
    EmailField,
    EnumField,
    IntegerField,
    SlugField,
    StringField,
    TagsField,
    TextAreaField,
    action,
    flash,
    row_action,
)
from starlette_admin.contrib.mongoengine import InlineModelView, ModelView
from starlette_admin.contrib.mongoengine.filters import DateTimeBetweenFilter
from starlette_admin.exceptions import ActionFailed

# ── Inline ────────────────────────────────────────────────────────────────────


class EpisodeInline(InlineModelView):
    """Episodes embedded inside the Podcast create/edit form."""

    document = Episode
    fields = [
        "id",
        "host",
        StringField("title"),
        IntegerField("episode_number"),
        IntegerField("season"),
        IntegerField("duration_minutes"),
        DateTimeField("published_at"),
        EnumField("status", enum=EpisodeStatus),
        TextAreaField("notes"),
    ]
    menu_label = "Episodes"
    extra = 1


# ── Category ──────────────────────────────────────────────────────────────────


class CategoryView(ModelView):
    fields = ["id", "name", ColorField("color"), TextAreaField("description")]
    searchable_fields = ["name"]
    sortable_fields = ["name"]


# ── Podcast ───────────────────────────────────────────────────────────────────


class PodcastView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        TextAreaField("description"),
        StringField("language"),
        BooleanField("featured"),
        "cover",
        "trailer",
        TagsField("tags"),
        "categories",
        EnumField("status", enum=PodcastStatus),
        DateTimeField("created_at"),
    ]
    exclude_fields_from_list = ["description", "trailer"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]

    inlines = [EpisodeInline]

    exporters = ["csv", "xlsx"]
    searchable_fields = ["title", "slug"]
    sortable_fields = ["title", "featured", "status", "created_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)


# ── Host ──────────────────────────────────────────────────────────────────────


class HostView(ModelView):
    fields = [
        "id",
        "full_name",
        EmailField("email"),
        TextAreaField("bio"),
        EnumField("role", enum=HostRole),
        DateTimeField("joined_at"),
    ]
    exclude_fields_from_create = ["joined_at"]
    exclude_fields_from_edit = ["joined_at"]

    exporters = ["csv", "xlsx"]
    searchable_fields = ["full_name", "email"]
    sortable_fields = ["full_name", "role", "joined_at"]
    fields_default_sort = [("joined_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.joined_at = datetime.now(UTC)


# ── Episode ───────────────────────────────────────────────────────────────────


class EpisodeView(ModelView):
    fields = [
        "id",
        "podcast",
        "host",
        StringField("title"),
        IntegerField("episode_number"),
        IntegerField("season"),
        IntegerField("duration_minutes"),
        DateTimeField("published_at", filters=[DateTimeBetweenFilter]),
        EnumField("status", enum=EpisodeStatus),
        TextAreaField("notes"),
    ]
    exclude_fields_from_list = ["notes"]

    exporters = ["csv", "xlsx"]
    sortable_fields = ["episode_number", "published_at", "status", "duration_minutes"]
    fields_default_sort = [("published_at", True)]

    actions = ["publish", "archive", "delete"]
    row_actions = ["view", "edit", "publish", "delete"]

    # ── Batch actions ──────────────────────────────────────────────────────────

    @action(
        name="publish",
        text="Publish episodes",
        confirmation="Mark the selected episodes as published?",
        submit_btn_text="Publish",
        submit_btn_class="btn btn-success",
    )
    async def publish_action(self, request: Request, pks: list[Any]) -> None:
        now = datetime.now(UTC)
        count = 0
        for ep in await self.find_by_pks(request, pks):
            if ep.status != EpisodeStatus.PUBLISHED:
                ep.status = EpisodeStatus.PUBLISHED
                if ep.published_at is None:
                    ep.published_at = now
                ep.save()
                count += 1
        flash(request, f"{count} episode(s) published.", "success")

    @action(
        name="archive",
        text="Archive episodes",
        confirmation="Archive the selected episodes?",
        submit_btn_text="Archive",
        submit_btn_class="btn btn-warning",
    )
    async def archive_action(self, request: Request, pks: list[Any]) -> None:
        count = 0
        for ep in await self.find_by_pks(request, pks):
            if ep.status != EpisodeStatus.ARCHIVED:
                ep.status = EpisodeStatus.ARCHIVED
                ep.save()
                count += 1
        flash(request, f"{count} episode(s) archived.", "success")

    # ── Row action ─────────────────────────────────────────────────────────────

    @row_action(
        name="publish",
        text="Publish",
        confirmation="Publish this episode?",
        icon_class="fas fa-broadcast-tower",
        submit_btn_text="Publish",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
    )
    async def publish_row_action(self, request: Request, pk: Any) -> None:
        ep = await self.find_by_pk(request, pk)
        if ep.status == EpisodeStatus.PUBLISHED:
            raise ActionFailed("Episode is already published.")
        ep.status = EpisodeStatus.PUBLISHED
        if ep.published_at is None:
            ep.published_at = datetime.now(UTC)
        ep.save()
        flash(request, "Episode published.", "success")
