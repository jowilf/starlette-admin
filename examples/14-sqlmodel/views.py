from datetime import UTC, datetime
from typing import Any

from models import ArticleStatus, Comment, Role
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import (
    BooleanField,
    ColorField,
    DateTimeField,
    EmailField,
    EnumField,
    IntegerField,
    StringField,
    TagsField,
    TextAreaField,
    action,
    flash,
    row_action,
)
from starlette_admin.contrib.sqla.filters import DateTimeBetweenFilter
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.export import CsvExporter, ExcelExporter

# ── Inline ────────────────────────────────────────────────────────────────────


class CommentInline(InlineModelView):
    """Comments embedded inside the Article create/edit form."""

    model = Comment
    fields = [
        IntegerField("id"),
        StringField("author_name"),
        EmailField("email"),
        TextAreaField("body"),
        BooleanField("approved"),
    ]
    menu_label = "Comments"
    extra = 1

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)


# ── Author ────────────────────────────────────────────────────────────────────


class AuthorView(ModelView):
    fields = [
        "id",
        "full_name",
        EmailField("email"),
        EnumField("role", enum=Role),
        ColorField("avatar_color"),
        TextAreaField("bio"),
        DateTimeField("created_at"),
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]

    exporters = [CsvExporter(), ExcelExporter()]
    searchable_fields = ["full_name", "email"]
    sortable_fields = ["id", "full_name", "role", "created_at"]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)


# ── Category ──────────────────────────────────────────────────────────────────


class CategoryView(ModelView):
    fields = ["id", "name", TextAreaField("description")]
    searchable_fields = ["name"]
    sortable_fields = ["id", "name"]


# ── Article ───────────────────────────────────────────────────────────────────


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        TextAreaField("content"),
        TagsField("tags"),
        EnumField("status", enum=ArticleStatus),
        IntegerField("views"),
        DateTimeField("published_at"),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter]),
        DateTimeField("updated_at"),
        "author",
        "category",
    ]
    exclude_fields_from_list = ["content", "updated_at"]
    exclude_fields_from_create = ["published_at", "created_at", "updated_at", "views"]
    exclude_fields_from_edit = ["created_at", "updated_at"]

    inlines = [CommentInline]

    exporters = [CsvExporter(), ExcelExporter()]
    searchable_fields = ["title"]
    sortable_fields = ["id", "title", "status", "views", "created_at"]
    fields_default_sort = [("created_at", True)]

    actions = ["make_published", "archive", "delete"]
    row_actions = ["view", "edit", "make_published", "delete"]

    # ── Hooks ──────────────────────────────────────────────────────────────────

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.updated_at = datetime.now(UTC)

    # ── Batch actions ──────────────────────────────────────────────────────────

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Publish the selected articles?",
        submit_btn_text="Publish",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        session: Session = request.state.session
        count = 0
        for article in await self.find_by_pks(request, pks):
            if article.status != ArticleStatus.PUBLISHED:
                article.status = ArticleStatus.PUBLISHED
                article.published_at = datetime.now(UTC)
                session.add(article)
                count += 1
        session.flush()
        flash(request, f"{count} article(s) published.", "success")

    @action(
        name="archive",
        text="Archive selected",
        confirmation="Move the selected articles to the archive?",
        submit_btn_text="Archive",
        submit_btn_class="btn-warning",
    )
    async def archive_action(self, request: Request, pks: list[Any]) -> None:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = ArticleStatus.ARCHIVED
            session.add(article)
        session.flush()
        flash(request, f"{len(pks)} article(s) archived.", "success")

    # ── Row action ─────────────────────────────────────────────────────────────

    @row_action(
        name="make_published",
        text="Publish",
        confirmation="Publish this article?",
        icon_class="fas fa-bullhorn",
        submit_btn_text="Publish",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        article = await self.find_by_pk(request, pk)
        if article.status == ArticleStatus.PUBLISHED:
            raise ActionFailed("Article is already published.")
        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.now(UTC)
        session.add(article)
        session.flush()
        flash(request, "Article published.", "success")


# ── Comment (standalone) ──────────────────────────────────────────────────────


class CommentView(ModelView):
    fields = [
        "id",
        StringField("author_name"),
        EmailField("email"),
        TextAreaField("body"),
        BooleanField("approved"),
        DateTimeField("created_at"),
        "article",
    ]
    exclude_fields_from_list = ["body"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["author_name", "email"]
    sortable_fields = ["id", "author_name", "approved", "created_at"]
    fields_default_sort = [("created_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)
