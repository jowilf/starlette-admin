"""Integration tests for InlineModelView: single FK and composite FK."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx2 import AsyncClient
from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette.applications import Starlette
from starlette_admin import IntegerField, StringField, TextAreaField
from starlette_admin.contrib.sqla import Admin, InlineModelView, ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


class Base(DeclarativeBase):
    pass


# ── Single FK models ──────────────────────────────────────────────────────────


class Article(Base):
    __tablename__ = "sqla_inline_article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    comments: Mapped[list["InlineComment"]] = relationship(
        "InlineComment", back_populates="article", cascade="all, delete-orphan"
    )


class Moderator(Base):
    __tablename__ = "sqla_inline_moderator"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    async def __admin_repr__(self, request):
        return self.name


class InlineComment(Base):
    __tablename__ = "sqla_inline_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sqla_inline_article.id"), nullable=False
    )
    moderator_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sqla_inline_moderator.id"), nullable=True
    )
    author: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Anonymous"
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    article: Mapped["Article"] = relationship("Article", back_populates="comments")
    moderator: Mapped["Moderator | None"] = relationship("Moderator")


# ── Composite FK models ───────────────────────────────────────────────────────


class Order(Base):
    """Parent model with a composite PK (store_id, seq)."""

    __tablename__ = "sqla_inline_order"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    lines: Mapped[list["OrderLine"]] = relationship(
        "OrderLine", back_populates="order", cascade="all, delete-orphan"
    )


class OrderLine(Base):
    """Child model with a composite FK referencing Order(store_id, seq)."""

    __tablename__ = "sqla_inline_order_line"

    order_store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped["Order"] = relationship("Order", back_populates="lines")

    __table_args__ = (
        ForeignKeyConstraint(
            ["order_store_id", "order_seq"],
            ["sqla_inline_order.store_id", "sqla_inline_order.seq"],
        ),
    )


# ── Admin views ───────────────────────────────────────────────────────────────


class CommentInline(InlineModelView):
    model = InlineComment
    fk_attr = "article_id"
    fields = [IntegerField("id"), StringField("author"), TextAreaField("body")]
    extra = 1


# Same inline without explicit fk_attr (auto-detected from Article.comments)
class CommentInlineAuto(InlineModelView):
    model = InlineComment
    fields = [IntegerField("id"), StringField("author"), TextAreaField("body")]
    extra = 1


class ArticleView(ModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [CommentInline]
    label = "Articles"


class ArticleViewAuto(ModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [CommentInlineAuto]
    label = "Articles (auto FK)"


class OrderLineInline(InlineModelView):
    model = OrderLine
    fk_attr = ("order_store_id", "order_seq")
    fields = [
        IntegerField("order_store_id"),
        IntegerField("order_seq"),
        IntegerField("line_no"),
        StringField("product"),
    ]
    extra = 1
    label = "Order Lines"


# Same inline without explicit fk_attr (auto-detected from Order.lines)
class OrderLineInlineAuto(InlineModelView):
    model = OrderLine
    fields = [
        IntegerField("order_store_id"),
        IntegerField("order_seq"),
        IntegerField("line_no"),
        StringField("product"),
    ]
    extra = 1
    label = "Order Lines (auto FK)"


class OrderView(ModelView):
    fields = [IntegerField("store_id"), IntegerField("seq"), StringField("customer")]
    inlines = [OrderLineInline]
    label = "Orders"


class OrderViewAuto(ModelView):
    fields = [IntegerField("store_id"), IntegerField("seq"), StringField("customer")]
    inlines = [OrderLineInlineAuto]
    label = "Orders (auto FK)"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine() -> Engine:
    _engine = get_test_engine()
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)
    _engine.dispose()


@pytest.fixture()
def session(engine: Engine) -> Session:
    with Session(engine) as s:
        yield s
        s.rollback()
        # Cleanup between tests
        s.execute(OrderLine.__table__.delete())
        s.execute(Order.__table__.delete())
        s.execute(InlineComment.__table__.delete())
        s.execute(Article.__table__.delete())
        s.commit()


@pytest.fixture()
def app(engine: Engine) -> Starlette:
    _app = Starlette()
    admin = Admin(engine, title="Test Inline")
    admin.add_view(ArticleView(Article))
    admin.add_view(OrderView(Order))
    admin.mount_to(_app)
    return _app


@pytest.fixture()
def app_auto(engine: Engine) -> Starlette:
    """Same app but using auto-detected fk_attr inlines."""
    _app = Starlette()
    admin = Admin(engine, title="Test Inline Auto")
    admin.add_view(ArticleViewAuto(Article, key="article-auto"))
    admin.add_view(OrderViewAuto(Order, key="order-auto"))
    admin.mount_to(_app)
    return _app


@pytest_asyncio.fixture()
async def client_auto(app_auto: Starlette) -> AsyncClient:
    async with csrf_async_client(app_auto) as ac:
        yield ac


@pytest_asyncio.fixture()
async def client(app: Starlette) -> AsyncClient:
    async with csrf_async_client(app) as ac:
        yield ac


# ── Single FK tests ───────────────────────────────────────────────────────────


class TestSingleFKInline:
    async def test_create_with_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        resp = await client.post(
            "/admin/article/create",
            data={
                "title": "My Article",
                "inlines.inline-comment.0.author": "Alice",
                "inlines.inline-comment.0.body": "Great read!",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303

        articles = session.execute(select(Article)).scalars().all()
        assert len(articles) == 1
        comments = session.execute(select(InlineComment)).scalars().all()
        assert len(comments) == 1
        assert comments[0].author == "Alice"
        assert comments[0].body == "Great read!"
        assert comments[0].article_id == articles[0].id

    async def test_edit_adds_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        article = Article(title="Draft")
        session.add(article)
        session.flush()
        article_id = article.id
        session.commit()
        session.expire_all()

        resp = await client.post(
            f"/admin/article/edit?pk={article_id}",
            data={
                "title": "Published",
                "inlines.inline-comment.0.author": "Bob",
                "inlines.inline-comment.0.body": "First!",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303

        comments = session.execute(select(InlineComment)).scalars().all()
        assert len(comments) == 1
        assert comments[0].article_id == article_id

    async def test_edit_deletes_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        article = Article(title="Draft")
        comment = InlineComment(author="X", body="old")
        article.comments.append(comment)
        session.add(article)
        session.commit()
        article_id = article.id
        comment_id = comment.id
        session.expire_all()

        resp = await client.post(
            f"/admin/article/edit?pk={article_id}",
            data={
                "title": "Draft",
                "inlines.inline-comment.0.pk": str(comment_id),
                "inlines.inline-comment.0.author": "X",
                "inlines.inline-comment.0.body": "old",
                "inlines.inline-comment.0.DELETE": "on",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert session.execute(select(InlineComment)).scalars().first() is None


# ── Composite FK tests ────────────────────────────────────────────────────────


class TestCompositeFKInline:
    async def test_create_with_composite_fk_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        resp = await client.post(
            "/admin/order/create",
            data={
                "store_id": "1",
                "seq": "42",
                "customer": "Acme Corp",
                "inlines.order-line.0.line_no": "1",
                "inlines.order-line.0.product": "Widget A",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        orders = session.execute(select(Order)).scalars().all()
        assert len(orders) == 1
        lines = session.execute(select(OrderLine)).scalars().all()
        assert len(lines) == 1
        assert lines[0].product == "Widget A"
        assert lines[0].order_store_id == 1
        assert lines[0].order_seq == 42

    async def test_edit_adds_composite_fk_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        order = Order(store_id=2, seq=10, customer="Beta LLC")
        existing_line = OrderLine(
            order_store_id=2, order_seq=10, line_no=1, product="Old"
        )
        order.lines.append(existing_line)
        session.add(order)
        session.commit()
        session.expire_all()

        resp = await client.post(
            "/admin/order/edit?pk=2%2C10",
            data={
                "store_id": "2",
                "seq": "10",
                "customer": "Beta LLC",
                "inlines.order-line.0.pk": "2,10,1",
                "inlines.order-line.0.order_store_id": "2",
                "inlines.order-line.0.order_seq": "10",
                "inlines.order-line.0.line_no": "1",
                "inlines.order-line.0.product": "Old",
                "inlines.order-line.1.line_no": "2",
                "inlines.order-line.1.product": "New Widget",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        lines = (
            session.execute(
                select(OrderLine).where(
                    OrderLine.order_store_id == 2, OrderLine.order_seq == 10
                )
            )
            .scalars()
            .all()
        )
        assert len(lines) == 2
        products = {line.product for line in lines}
        assert products == {"Old", "New Widget"}
        assert all(line.order_store_id == 2 and line.order_seq == 10 for line in lines)

    async def test_find_by_parent_composite_fk(
        self, client: AsyncClient, session: Session
    ) -> None:
        """edit page renders existing inline rows for a composite-PK parent."""
        order = Order(store_id=3, seq=99, customer="Gamma Inc")
        order.lines.append(
            OrderLine(order_store_id=3, order_seq=99, line_no=1, product="Gadget")
        )
        session.add(order)
        session.commit()
        session.expire_all()

        resp = await client.get("/admin/order/edit?pk=3%2C99")
        assert resp.status_code == 200
        assert "Gadget" in resp.text


# ── Auto-detected fk_attr tests ───────────────────────────────────────────────


class TestAutoFKDetectionSingle:
    """Same scenarios as TestSingleFKInline but fk_attr is auto-detected."""

    async def test_auto_detect_create(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        resp = await client_auto.post(
            "/admin/article-auto/create",
            data={
                "title": "Auto Article",
                "inlines.inline-comment.0.author": "AutoAlice",
                "inlines.inline-comment.0.body": "Auto body",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        articles = session.execute(select(Article)).scalars().all()
        assert len(articles) == 1
        comments = session.execute(select(InlineComment)).scalars().all()
        assert len(comments) == 1
        assert comments[0].author == "AutoAlice"
        assert comments[0].article_id == articles[0].id

    async def test_auto_detect_edit_page_renders(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        article = Article(title="Auto Draft")
        comment = InlineComment(author="Z", body="existing")
        article.comments.append(comment)
        session.add(article)
        session.commit()
        article_id = article.id
        session.expire_all()

        resp = await client_auto.get(f"/admin/article-auto/edit?pk={article_id}")
        assert resp.status_code == 200
        assert "existing" in resp.text


class TestAutoFKDetectionComposite:
    """Same scenarios as TestCompositeFKInline but fk_attr is auto-detected."""

    async def test_auto_detect_composite_create(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        resp = await client_auto.post(
            "/admin/order-auto/create",
            data={
                "store_id": "10",
                "seq": "1",
                "customer": "Auto Corp",
                "inlines.order-line.0.line_no": "1",
                "inlines.order-line.0.product": "Auto Widget",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        lines = session.execute(select(OrderLine)).scalars().all()
        assert len(lines) == 1
        assert lines[0].product == "Auto Widget"
        assert lines[0].order_store_id == 10
        assert lines[0].order_seq == 1

    async def test_auto_detect_composite_edit_page_renders(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        order = Order(store_id=20, seq=5, customer="Auto Beta")
        order.lines.append(
            OrderLine(order_store_id=20, order_seq=5, line_no=1, product="Auto Gadget")
        )
        session.add(order)
        session.commit()
        session.expire_all()

        resp = await client_auto.get("/admin/order-auto/edit?pk=20%2C5")
        assert resp.status_code == 200
        assert "Auto Gadget" in resp.text


# ── Relation fields on inline rows (async engine) ─────────────────────────────


class CommentInlineWithModerator(InlineModelView):
    model = InlineComment
    fk_attr = "article_id"
    fields = [
        IntegerField("id"),
        StringField("author"),
        TextAreaField("body"),
        "moderator",
    ]


class ArticleViewWithModerator(ModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [CommentInlineWithModerator]


class ModeratorView(ModelView):
    fields = [IntegerField("id"), StringField("name")]


@pytest_asyncio.fixture()
async def async_relation_app(tmp_path) -> AsyncGenerator[Starlette, None]:
    """Admin on an async engine, with an inline exposing a relation field."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/inline_async.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as s:
        s.add_all(
            [
                Moderator(id=1, name="Mod Riley"),
                Article(id=1, title="Async inlines"),
                InlineComment(
                    id=1,
                    article_id=1,
                    moderator_id=1,
                    author="Sam",
                    body="Looks good",
                ),
            ]
        )
        await s.commit()
    _app = Starlette()
    admin = Admin(engine, title="Test Inline Relation Async")
    admin.add_view(ArticleViewWithModerator(Article))
    admin.add_view(ModeratorView(Moderator))
    admin.mount_to(_app)
    yield _app
    await engine.dispose()


class TestInlineRelationFieldAsync:
    """Inline rows carrying relation fields must be eager-loaded.

    Serialization happens after find_by_parent returns, so an unloaded
    relation would lazy-load at that point and raise MissingGreenlet on
    async engines.
    """

    async def test_detail_page_renders_inline_relation(
        self, async_relation_app: Starlette
    ) -> None:
        async with csrf_async_client(async_relation_app) as client:
            resp = await client.get("/admin/article/detail?pk=1")
            assert resp.status_code == 200
            assert "Mod Riley" in resp.text
