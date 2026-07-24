"""Runnable demo for starlette-admin-adminlte.

Single-file showcase exercising every field type, filter, action, inline form,
relation, lifecycle hook, export/import flow, dashboard widget, and custom route
that starlette-admin supports — all under the AdminLTE 4 theme.

    uv run python example/app.py
    # → http://localhost:8000/admin/  (admin / admin)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import uuid4

import uvicorn
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Time,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import (
    ActionSelection,
    BooleanField,
    Breakpoints,
    CardRowWidget,
    ChartWidget,
    CollectionField,
    ColorField,
    ColumnWidget,
    ComputedField,
    CountryField,
    CurrencyField,
    CustomView,
    DateField,
    DateTimeField,
    DecimalField,
    DividerWidget,
    DropDown,
    EmailField,
    EnumField,
    FileField,
    FloatField,
    GridWidget,
    HasMany,
    HasOne,
    HtmlWidget,
    I18nConfig,
    ImageField,
    IntegerField,
    IPAddressField,
    JSONField,
    Link,
    ListField,
    PasswordField,
    PhoneField,
    RowActionsDisplayType,
    RowActionsPosition,
    SlugField,
    StringField,
    TableWidget,
    TabsWidget,
    TagsField,
    TextAreaField,
    TextWidget,
    TimeField,
    TimezoneConfig,
    TimeZoneField,
    TinyMCEEditorField,
    URLField,
    UUIDField,
    action,
    flash,
    link_row_action,
    route,
    row_action,
    validators,
)
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin, InlineModelView, ModelView
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
)
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)
from starlette_admin.exceptions import ActionFailed
from starlette_admin.i18n import SUPPORTED_LOCALES
from starlette_admin.storage import LocalStorage
from starlette_admin.widgets import Col, PanelWidget, StatWidget

from starlette_admin_adminlte import AdminlteTheme

# ── Config ────────────────────────────────────────────────────────────────────

DATABASE_FILE = "example.sqlite"
SECRET = "dev-only-change-me"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)
local_storage = LocalStorage(base_dir="uploads/", name="local")


def _now() -> datetime:
    return datetime.now(UTC)


# ── Base & Enums ──────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Base class for every SQLAlchemy model in this demo."""


class PostStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProductStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


# ── Models ────────────────────────────────────────────────────────────────────

product_tag_table = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    posts: Mapped[list[Post]] = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.name} <{self.email}>"


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus),
        default=PostStatus.DRAFT,
    )
    views: Mapped[int] = mapped_column(Integer, default=0)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    author_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("authors.id"),
        nullable=True,
    )

    author: Mapped[Author | None] = relationship("Author", back_populates="posts")
    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="Comment.id",
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("posts.id"),
        nullable=True,
    )
    author: Mapped[str] = mapped_column(String(100), default="Anonymous")
    body: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    post: Mapped[Post | None] = relationship("Post", back_populates="comments")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.author}: {self.body[:50]}"


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(60))

    async def __admin_repr__(self, request: Request) -> str:
        return self.label


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220))
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rich_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    contact_email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secret_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    identifier: Mapped[str | None] = mapped_column(String(36), nullable=True)
    server_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus),
        default=ProductStatus.ACTIVE,
    )
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    features: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extra_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    manual: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )
    category: Mapped[Category | None] = relationship(
        "Category",
        back_populates="products",
    )
    tags = relationship("Tag", secondary=product_tag_table)

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    attachment: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(50))
    view_key: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ── Shared action helpers (DRY for batch + row actions) ───────────────────────


def _publish_post(session: Session, post: Post) -> None:
    post.status = PostStatus.PUBLISHED
    session.add(post)


def _clone_post(post: Post) -> Post:
    return Post(
        title=f"{post.title} (copy)",
        slug=f"{post.slug}-copy",
        body=post.body,
        status=PostStatus.DRAFT,
        views=0,
        featured=False,
        author_id=post.author_id,
    )


def _write_audit(
    event: AdminEvent | str,
    view_key: str,
    pk: str,
    detail: str,
    request: Request,
) -> None:
    """Persist an audit entry in a standalone session (avoids interfering
    with the request's active transaction)."""
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
                detail=detail,
                actor=actor,
                created_at=_now(),
            )
        )
        session.commit()


# ── Dashboard query helpers ───────────────────────────────────────────────────


def _post_status_counts(session: Session) -> dict[str, int]:
    """Single grouped query returning {status_value: count}."""
    counts = {s.value: 0 for s in PostStatus}
    for status, count in session.execute(
        select(Post.status, func.count(Post.id)).group_by(Post.status)
    ).all():
        counts[status.value] = count
    return counts


def _daily_post_counts(session: Session) -> list[int]:
    """One grouped query instead of seven per-day queries."""
    today = date.today()
    start = today - timedelta(days=6)
    by_date = dict(
        session.execute(
            select(func.date(Post.created_at), func.count(Post.id))
            .where(func.date(Post.created_at) >= start)
            .group_by(func.date(Post.created_at))
        ).all()
    )
    return [by_date.get(start + timedelta(days=i), 0) for i in range(7)]


def _top_posts(session: Session) -> list[list[Any]]:
    rows = session.execute(
        select(Post.title, Post.views).order_by(Post.views.desc()).limit(5)
    ).all()
    return [[t, v] for t, v in rows]


def _recent_audit(session: Session) -> list[list[Any]]:
    rows = session.execute(
        select(AuditLog.event, AuditLog.detail, AuditLog.created_at)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    ).all()
    return [[e, (d or ""), c.strftime("%Y-%m-%d %H:%M")] for e, d, c in rows]


# ── Inline views ──────────────────────────────────────────────────────────────


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body", "approved"]
    menu_label = "Comments"
    extra = 1


# ── Views: blog domain ─────────────────────────────────────────────────────────


class AuthorView(ModelView):
    fields = ["id", "name", "email", "created_at", "posts"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    form_layout = [("name", "email"), "posts"]
    searchable_fields = ("name", "email")
    fields_default_sort = [("name", False)]


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, validators=[validators.length(min=3)]),
        SlugField("slug", populate_from="title", copy_to_clipboard=True),
        EnumField("status", enum=PostStatus),
        IntegerField("views", filters=[GreaterThanFilter, BetweenFilter]),
        BooleanField("featured"),
        "author",
        TextAreaField("body", validators=[validators.length(min=10)]),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda _req, post: len((post.body or "").split()),
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter]),
        "updated_at",
    ]
    form_layout = [
        ("title", "slug"),
        ("status", "views", "featured"),
        ("author", "body"),
    ]
    exclude_fields_from_create = ("created_at", "updated_at", "word_count")
    exclude_fields_from_edit = ("created_at", "updated_at", "word_count")
    exclude_fields_from_list = ("body",)
    searchable_fields = ("title", "slug", "body", "status")
    sortable_fields = ("title", "views", "created_at", "status")
    fields_default_sort = (("created_at", True),)
    inline_editable_fields = ("title", "status", "featured")
    search_auto_submit = True
    inlines = [CommentInline]
    exporters = ("csv", "json")
    importers = ("csv", "json")
    page_size = 10
    page_size_options = (10, 25, 50, 100, -1)

    actions = (
        "make_published",
        "increase_views",
        "duplicate",
        "delete",
        "no_confirmation",
        "redirect_to_example",
        "always_failed",
        "sync_all",
    )
    row_actions = ("view", "edit", "make_published", "duplicate_row", "delete")
    row_actions_display_type = RowActionsDisplayType.KEBAB
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

    async def before_create(self, request: Request, data: dict, obj: Any) -> None:
        obj.created_at = _now()

    async def before_edit(self, request: Request, data: dict, obj: Any) -> None:
        obj.updated_at = _now()

    async def after_edit_committed(self, request: Request, obj: Any) -> None:
        flash(request, f"Post '{obj.title}' committed to the database.", "info")

    # ── Batch actions ──

    @action(
        name="make_published",
        text="Mark selected as published",
        confirmation="Mark selected posts as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(
        self,
        request: Request,
        selection: ActionSelection,
    ) -> None:
        session: Session = request.state.session
        posts = await selection.rows()
        for post in posts:
            _publish_post(session, post)
        session.flush()
        flash(request, f"{len(posts)} post(s) marked as published.", "success")

    @action(
        name="increase_views",
        text="Increase views",
        confirmation="By how much should the view count grow?",
        form="""
        <form>
            <div class="mt-3">
                <input type="number" class="form-control" name="value"
                       placeholder="Enter value" min="1" max="10000">
            </div>
        </form>
        """,
    )
    async def increase_views_action(
        self,
        request: Request,
        selection: ActionSelection,
    ) -> None:
        session: Session = request.state.session
        data = await request.form()
        try:
            value = int(data.get("value"))
        except (TypeError, ValueError) as err:
            raise ActionFailed("Enter a valid number") from err
        posts = await selection.rows()
        for post in posts:
            post.views += value
            session.add(post)
        session.flush()
        flash(
            request,
            f"View count of {len(posts)} post(s) increased by {value}.",
            "success",
        )

    @action(
        name="duplicate",
        text="Duplicate selected",
        confirmation="Create a copy of each selected post?",
        submit_btn_text="Duplicate",
    )
    async def duplicate_action(
        self,
        request: Request,
        selection: ActionSelection,
    ) -> None:
        session: Session = request.state.session
        posts = await selection.rows()
        for post in posts:
            session.add(_clone_post(post))
        session.flush()
        flash(request, f"Duplicated {len(posts)} post(s).", "success")

    @action(name="no_confirmation", text="Run without confirmation")
    async def no_confirmation_action(
        self,
        request: Request,
        _selection: ActionSelection,
    ) -> None:
        flash(request, "Action ran without a confirmation dialog.", "info")

    @action(
        name="redirect_to_example",
        text="Redirect to example.com",
        custom_response=True,
    )
    async def redirect_to_example_action(
        self,
        _request: Request,
        _selection: ActionSelection,
    ) -> Response:
        return RedirectResponse("https://example.com/")

    @action(
        name="always_failed",
        text="Always fails",
        confirmation="This always fails. Continue?",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(
        self,
        _request: Request,
        _selection: ActionSelection,
    ) -> None:
        raise ActionFailed("This action is configured to always fail.")

    @action(
        name="sync_all",
        text="Sync all posts",
        confirmation="Re-sync every post from upstream?",
        submit_btn_text="Sync",
        allow_empty_selection=True,
    )
    async def sync_all_action(
        self,
        request: Request,
        _selection: ActionSelection,
    ) -> None:
        flash(request, "All posts were synced.", "success")

    # ── Row actions ──

    async def is_row_action_allowed_for_obj(
        self,
        request: Request,
        name: str,
        obj: Post,
    ) -> bool:
        if name == "make_published":
            return obj.status != PostStatus.PUBLISHED
        return await super().is_row_action_allowed_for_obj(request, name, obj)

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Mark this post as published?",
        icon_class="fas fa-bullhorn",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        post = await self.find_by_pk(request, pk)
        _publish_post(session, post)
        session.flush()
        flash(request, "Post marked as published.", "success")

    @row_action(
        name="duplicate_row",
        text="Duplicate post",
        confirmation="Create a copy of this post?",
        icon_class="fas fa-copy",
    )
    async def duplicate_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        post = await self.find_by_pk(request, pk)
        session.add(_clone_post(post))
        session.flush()
        flash(request, "Post duplicated.", "success")

    @link_row_action(
        name="view_online",
        text="View online",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def view_online_row_action(self, _request: Request, pk: Any) -> str:
        return f"https://example.com/posts/{pk}"


# ── Views: catalog domain ─────────────────────────────────────────────────────


class ProductView(ModelView):
    fields = [
        "id",
        UUIDField("sku", default=lambda _req: str(uuid4())),
        StringField("name", required=True, validators=[validators.length(min=2)]),
        SlugField("slug", populate_from="name"),
        StringField("summary"),
        TextAreaField("description"),
        TinyMCEEditorField("rich_content", label="Rich Content"),
        DecimalField(
            "price",
            min=0,
            validators=[validators.number_range(min=0)],
            filters=[GreaterThanFilter, BetweenFilter],
        ),
        IntegerField("stock", min=0),
        FloatField("weight", help_text="Weight in kilograms"),
        BooleanField("is_active", default=True),
        TagsField("keywords"),
        EmailField("contact_email", validators=[validators.email()]),
        URLField("website", validators=[validators.url()]),
        PhoneField("phone"),
        ColorField("accent_color"),
        PasswordField("secret_code", exclude_from_list=True, exclude_from_detail=True),
        UUIDField("identifier"),
        IPAddressField("server_ip", validators=[validators.ip_address()]),
        EnumField("status", enum=ProductStatus),
        EnumField(
            "priority",
            choices=[(1, "Low"), (2, "Normal"), (3, "High"), (4, "Critical")],
            label="Priority Level",
        ),
        TimeZoneField("timezone"),
        CountryField("country"),
        CurrencyField("currency"),
        DateTimeField("created_at"),
        DateField("manufacture_date"),
        TimeField("release_time"),
        CollectionField(
            "specs",
            fields=[
                StringField("material"),
                IntegerField("warranty_years"),
                BooleanField("recyclable"),
            ],
        ),
        ListField(StringField("features")),
        JSONField("extra_info", label="Extra Info (JSON)"),
        ImageField(
            "cover",
            storage=local_storage,
            upload_folder="products/covers",
            thumbnail_size=(256, 256),
        ),
        FileField(
            "manual",
            storage=local_storage,
            upload_folder="products/manuals",
            accept=".pdf,.doc,.docx,.txt",
            max_size=5 * 1024 * 1024,
        ),
        HasOne("category", key="category"),
        HasMany("tags", key="tag"),
        ComputedField(
            "in_stock_label",
            label="Stock Status",
            getter=lambda _req, p: "In stock" if (p.stock or 0) > 0 else "Out of stock",
        ),
    ]
    form_layout = [
        ("name", "slug"),
        ("sku", "identifier"),
        "summary",
        ("description", "rich_content"),
        ("price", "stock", "weight"),
        "is_active",
        ("contact_email", "website"),
        ("phone", "accent_color"),
        ("secret_code", "server_ip"),
        ("status", "priority"),
        ("timezone", "country", "currency"),
        ("manufacture_date", "release_time"),
        "keywords",
        "specs",
        ("features", "extra_info"),
        ("cover", "manual"),
        ("category", "tags"),
    ]
    exclude_fields_from_create = ("created_at",)
    exclude_fields_from_edit = ("created_at",)
    exclude_fields_from_list = ("description", "rich_content", "summary", "extra_info")
    searchable_fields = ("name", "slug", "sku", "status", "contact_email")
    sortable_fields = ("name", "price", "stock", "status", "created_at")
    fields_default_sort = (("name", False),)
    inline_editable_fields = ("name", "price", "stock", "is_active", "status")
    search_auto_submit = True
    exporters = ("csv", "json")
    importers = ("csv", "json")
    page_size = 10


class CategoryView(ModelView):
    fields = ["id", "name", "products"]
    searchable_fields = ("name",)


class TagView(ModelView):
    fields = ["id", "label"]
    searchable_fields = ("label",)


class DocumentView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=local_storage,
            upload_folder="documents/covers",
            thumbnail_size=(512, 512),
        ),
        FileField(
            "attachment",
            storage=local_storage,
            upload_folder="documents/files",
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.zip",
        ),
    ]
    searchable_fields = ("title",)


class AuditLogView(ModelView):
    fields_default_sort = (("created_at", True),)
    searchable_fields = ("event", "view_key", "detail")
    sortable_fields = ("event", "view_key", "created_at")

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


# ── Auth provider ─────────────────────────────────────────────────────────────

USERS = {
    "admin": {"name": "Administrator", "password": "admin"},
}


class DemoAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if not user or password != user["password"]:
            raise LoginFailed("Invalid username or password")
        request.session["username"] = username

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = USERS.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# ── Event subscriber ──────────────────────────────────────────────────────────


class AuditSubscriber(AdminEventSubscriber):
    @on(AdminEvent.AFTER_CREATE_COMMITTED)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        _write_audit(
            ctx.event,
            ctx.view_key,
            str(ctx.pk),
            f"Created {ctx.view_key!r} (pk={ctx.pk})",
            ctx.request,
        )

    @on(AdminEvent.AFTER_EDIT_COMMITTED)
    async def record_update(self, ctx: AfterEditContext) -> None:
        _write_audit(
            ctx.event,
            ctx.view_key,
            str(ctx.pk),
            f"Updated {ctx.view_key!r} (pk={ctx.pk})",
            ctx.request,
        )

    @on(AdminEvent.AFTER_DELETE_COMMITTED)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        _write_audit(
            ctx.event,
            ctx.view_key,
            str(ctx.pk),
            f"Deleted {ctx.view_key!r} (pk={ctx.pk})",
            ctx.request,
        )


# ── Dashboard ─────────────────────────────────────────────────────────────────


def _const(value: Any):
    """Wrap a precomputed value in an async callable for widget callbacks."""

    async def _fn(_request: Request) -> Any:
        return value

    return _fn


class DashboardView(CustomView):
    def __init__(self) -> None:
        super().__init__(
            menu_label="Dashboard",
            icon="fa fa-gauge-high",
            path="/",
            add_to_menu=True,
            widget=self._build,
        )

    async def _build(self, request: Request) -> ColumnWidget:
        session: Session = request.state.session

        # ── Pre-compute all data in ~5 queries instead of ~12 ──
        post_count = session.scalar(select(func.count(Post.id))) or 0
        author_count = session.scalar(select(func.count(Author.id))) or 0
        product_count = session.scalar(select(func.count(Product.id))) or 0
        total_views = session.scalar(select(func.sum(Post.views))) or 0

        status_counts = _post_status_counts(session)
        status_labels = [s.value.title() for s in PostStatus]
        status_series = [status_counts[s.value] for s in PostStatus]
        published_pct = (
            round((status_counts[PostStatus.PUBLISHED.value] / post_count) * 100, 1)
            if post_count
            else 0.0
        )

        daily_counts = _daily_post_counts(session)
        post_trend = [{"name": "Posts", "data": daily_counts}]
        day_labels = [
            (date.today() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)
        ]

        top_posts = _top_posts(session)
        recent_audit = _recent_audit(session)

        post_link = request.url_for("admin:list", key="post")
        product_link = request.url_for("admin:list", key="product")

        # ── Helper to build a stat card ──
        def _stat(title: str, value: Any, **kw: Any) -> StatWidget:
            return StatWidget(
                title=title,
                value_callback=_const(value),
                countup=True,
                **kw,
            )

        return ColumnWidget(
            children=[
                TextWidget(
                    content=(
                        "AdminLTE demo dashboard. Every widget type is rendered on "
                        "this page: stat cards, charts, tables, text, raw HTML, "
                        "dividers, panels, tabs, fieldsets, and responsive grids."
                    ),
                    card=True,
                ),
                HtmlWidget(
                    html=(
                        '<div class="alert alert-info d-flex align-items-center gap-2">'
                        '<i class="fa-solid fa-circle-info"></i>'
                        "<span>Tip: open <b>Products</b> to see all field types, "
                        "and <b>Blog Posts</b> for actions and inlines.</span></div>"
                    )
                ),
                CardRowWidget(
                    children=[
                        Col(
                            _stat(
                                "Posts",
                                post_count,
                                chart_type="area",
                                chart_callback=_const(post_trend),
                                description="Last 7 days",
                                description_icon="fa-solid fa-clock",
                                color="success",
                                link=post_link,
                            ),
                            breakpoints=Breakpoints(default=12, md=6, lg=3),
                        ),
                        Col(
                            _stat(
                                "Authors",
                                author_count,
                                description="Registered",
                                description_icon="fa-solid fa-user",
                                color="primary",
                            ),
                            breakpoints=Breakpoints(default=12, md=6, lg=3),
                        ),
                        Col(
                            _stat(
                                "Products",
                                product_count,
                                description="In catalog",
                                description_icon="fa-solid fa-box",
                                color="info",
                                link=product_link,
                            ),
                            breakpoints=Breakpoints(default=12, md=6, lg=3),
                        ),
                        Col(
                            _stat(
                                "Total Views",
                                total_views,
                                description="Across all posts",
                                description_icon="fa-solid fa-eye",
                                color="warning",
                            ),
                            breakpoints=Breakpoints(default=12, md=6, lg=3),
                        ),
                    ]
                ),
                DividerWidget(),
                TabsWidget(
                    tabs=[
                        (
                            "Charts",
                            ColumnWidget(
                                children=[
                                    PanelWidget(
                                        title="Trends",
                                        icon="fa-solid fa-chart-line",
                                        children=[
                                            GridWidget(
                                                breakpoints=Breakpoints(
                                                    default=1, md=2, lg=3
                                                ),
                                                gutter=4,
                                                children=[
                                                    ChartWidget(
                                                        title="Posts - Line",
                                                        chart_type="line",
                                                        series_callback=_const(
                                                            post_trend
                                                        ),
                                                        options={
                                                            "xaxis": {
                                                                "categories": day_labels
                                                            }
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts - Area",
                                                        chart_type="area",
                                                        series_callback=_const(
                                                            post_trend
                                                        ),
                                                        options={
                                                            "xaxis": {
                                                                "categories": day_labels
                                                            }
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Status - Bar",
                                                        chart_type="bar",
                                                        series_callback=_const(
                                                            post_trend
                                                        ),
                                                        options={
                                                            "xaxis": {
                                                                "categories": status_labels
                                                            }
                                                        },
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                    PanelWidget(
                                        title="Distribution",
                                        icon="fa-solid fa-chart-pie",
                                        collapsible=True,
                                        collapsed=True,
                                        children=[
                                            GridWidget(
                                                breakpoints=Breakpoints(
                                                    default=1, md=2
                                                ),
                                                gutter=4,
                                                children=[
                                                    ChartWidget(
                                                        title="Status - Pie",
                                                        chart_type="pie",
                                                        series_callback=_const(
                                                            status_series
                                                        ),
                                                        options={
                                                            "labels": status_labels
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Published - Gauge",
                                                        chart_type="radialBar",
                                                        series_callback=_const(
                                                            [published_pct]
                                                        ),
                                                        options={
                                                            "labels": ["Published"]
                                                        },
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "Tables",
                            ColumnWidget(
                                children=[
                                    CardRowWidget(
                                        children=[
                                            Col(
                                                TableWidget(
                                                    title="Top Posts by Views",
                                                    columns=["Title", "Views"],
                                                    rows_callback=_const(top_posts),
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, lg=6
                                                ),
                                            ),
                                            Col(
                                                TableWidget(
                                                    title="Recent Audit Entries",
                                                    columns=["Event", "Detail", "When"],
                                                    rows_callback=_const(recent_audit),
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, lg=6
                                                ),
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                    ]
                ),
            ]
        )


# ── Custom reports view ───────────────────────────────────────────────────────


class ReportsView(CustomView):
    menu_label = "Reports"
    icon = "fa fa-file-lines"
    path = "/reports"

    @route("")
    async def index(self, request: Request) -> HTMLResponse:
        return HTMLResponse(
            "<div class='container py-5'>"
            "<h1>Reports</h1>"
            "<p>This page comes from a custom <code>@route</code> on a CustomView.</p>"
            "<p>Try the JSON endpoint at "
            "<a href='/admin/reports/data'>/admin/reports/data</a>.</p>"
            "</div>"
        )

    @route("/data", methods=["GET"])
    async def report_data(self, request: Request) -> JSONResponse:
        session: Session = request.state.session
        total = session.scalar(select(func.count(Post.id))) or 0
        return JSONResponse({"posts": total, "generated_at": _now().isoformat()})


# ── Seed data ─────────────────────────────────────────────────────────────────


def seed() -> None:
    with Session(engine) as session:
        if session.scalar(select(func.count(Author.id))):
            return

        admin = Author(name="Ada Lovelace", email="ada@example.com")
        editor = Author(name="Grace Hopper", email="grace@example.com")
        session.add_all([admin, editor])
        session.flush()

        statuses = list(PostStatus)
        for i in range(1, 13):
            post = Post(
                title=f"Sample post {i}",
                slug=f"sample-post-{i}",
                body=f"This is the body of sample post number {i}. " * 5,
                status=statuses[i % len(statuses)],
                views=i * 17,
                featured=(i % 4 == 0),
                author_id=admin.id if i % 2 else editor.id,
            )
            session.add(post)
            session.flush()
            session.add(
                Comment(
                    post_id=post.id,
                    author="Reader",
                    body=f"Great article, post {i}!",
                    approved=(i % 2 == 0),
                )
            )

        categories = [Category(name=c) for c in ("Hardware", "Books", "Toys")]
        session.add_all(categories)
        tags = [Tag(label=t) for t in ("new", "sale", "featured", "limited")]
        session.add_all(tags)
        session.flush()

        for i in range(1, 11):
            session.add(
                Product(
                    sku=str(uuid4()),
                    name=f"Product {i}",
                    slug=f"product-{i}",
                    summary=f"Short summary for product {i}.",
                    description=f"Full description for product {i}. " * 3,
                    rich_content=f"<p>Rich <strong>content</strong> for product {i}.</p>",
                    price=Decimal(f"{i * 9.99:.2f}"),
                    stock=i * 5,
                    weight=float(i) * 0.5,
                    is_active=(i % 3 != 0),
                    keywords=[f"tag-{i}", "demo"],
                    contact_email=f"product{i}@example.com",
                    website="https://example.com",
                    phone="+1-555-0100",
                    accent_color="#3b82f6",
                    secret_code=f"secret-{i}",
                    identifier=str(uuid4()),
                    server_ip=f"10.0.0.{i}",
                    status=ProductStatus.ACTIVE
                    if i % 2
                    else ProductStatus.OUT_OF_STOCK,
                    priority=(i % 4) + 1,
                    timezone="Europe/Paris",
                    country="US",
                    currency="USD",
                    manufacture_date=date(2023, 1, (i % 28) + 1),
                    release_time=time(9, i % 60),
                    specs={
                        "material": "Aluminum" if i % 2 else "Plastic",
                        "warranty_years": i % 5,
                        "recyclable": bool(i % 2),
                    },
                    features=[f"Feature {n}" for n in range(1, (i % 3) + 2)],
                    extra_info={"source": "seed", "batch": i},
                    category_id=categories[i % len(categories)].id,
                    tags=[tags[(i + n) % len(tags)] for n in range(2)],
                )
            )

        session.commit()


# ── App setup ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: Starlette):
    Base.metadata.create_all(engine)
    seed()
    yield


app = Starlette(
    lifespan=lifespan,
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET)],
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>AdminLTE demo</h2>"
                "<p>Comprehensive single-file showcase of starlette-admin.</p>"
                "<p>Login with <b>admin</b> / <b>admin</b>.</p>"
                '<a href="/admin/">Go to Admin &rarr;</a>'
            ),
        ),
    ],
)

admin = Admin(
    engine,
    title="AdminLTE demo",
    secret_key=SECRET,
    theme=AdminlteTheme(),
    auth_provider=DemoAuthProvider(),
    index_view=DashboardView(),
    i18n_config=I18nConfig(
        default_locale="en",
        language_switcher=SUPPORTED_LOCALES,
    ),
    timezone_config=TimezoneConfig(
        default_timezone="UTC",
        database_timezone="UTC",
        timezone_switcher=[
            "UTC",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
        ],
    ),
    debug=True,
)

admin.add_view(ReportsView())
admin.add_view(
    Link(
        menu_label="AdminLTE.io",
        icon="fa fa-up-right-from-square",
        url="https://adminlte.io",
        target="_blank",
    )
)
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))
admin.add_view(AuthorView(Author, icon="fa fa-users"))
admin.add_view(
    DropDown(
        "Catalog",
        icon="fa fa-tags",
        always_open=False,
        views=[
            ProductView(
                Product, key="product", menu_label="Products", icon="fa fa-box"
            ),
            CategoryView(Category, key="category", menu_label="Categories"),
            TagView(Tag, key="tag", menu_label="Tags"),
        ],
    )
)
admin.add_view(DocumentView(Document, icon="fa fa-file"))
admin.add_view(
    AuditLogView(AuditLog, icon="fa fa-clipboard-list", menu_label="Audit Log")
)
admin.events.subscribe(AuditSubscriber())
admin.mount_to(app)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
