"""Integration tests for InlineModelView with SQLModel."""

import pytest
import pytest_asyncio
from httpx2 import AsyncClient
from sqlalchemy.engine import Engine
from sqlmodel import Field, Relationship, Session, SQLModel, select
from starlette.applications import Starlette
from starlette_admin import IntegerField, StringField, TextAreaField
from starlette_admin.contrib.sqlmodel import Admin, InlineModelView, ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


# ── Models ────────────────────────────────────────────────────────────────────


class SMPost(SQLModel, table=True):
    __tablename__ = "sm_inline_post"

    id: int | None = Field(None, primary_key=True)
    title: str

    comments: list["SMComment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class SMComment(SQLModel, table=True):
    __tablename__ = "sm_inline_comment"

    id: int | None = Field(None, primary_key=True)
    body: str = Field(min_length=10)
    post_id: int | None = Field(default=None, foreign_key="sm_inline_post.id")

    post: SMPost | None = Relationship(back_populates="comments")


# ── Admin views ───────────────────────────────────────────────────────────────


class SMCommentInline(InlineModelView):
    model = SMComment
    key = "sm-comment"
    fk_attr = "post_id"
    fields = [IntegerField("id"), TextAreaField("body")]
    extra = 1


class SMCommentInlineAuto(InlineModelView):
    """Same inline but fk_attr is auto-detected from SMPost.comments."""

    model = SMComment
    key = "sm-comment"
    fields = [IntegerField("id"), TextAreaField("body")]
    extra = 1


class SMPostView(ModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [SMCommentInline]


class SMPostViewAuto(ModelView):
    fields = [IntegerField("id"), StringField("title")]
    inlines = [SMCommentInlineAuto]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine() -> Engine:
    _engine = get_test_engine()
    SMPost.metadata.create_all(_engine)
    yield _engine
    SMPost.metadata.drop_all(_engine)
    _engine.dispose()


@pytest.fixture()
def session(engine: Engine) -> Session:
    with Session(engine) as s:
        yield s
        s.rollback()
        s.execute(SMComment.__table__.delete())
        s.execute(SMPost.__table__.delete())
        s.commit()


@pytest.fixture()
def app(engine: Engine) -> Starlette:
    _app = Starlette()
    admin = Admin(engine, title="Test SQLModel Inline")
    admin.add_view(SMPostView(SMPost, key="sm-post"))
    admin.mount_to(_app)
    return _app


@pytest.fixture()
def app_auto(engine: Engine) -> Starlette:
    _app = Starlette()
    admin = Admin(engine, title="Test SQLModel Inline Auto")
    admin.add_view(SMPostViewAuto(SMPost, key="sm-post-auto"))
    admin.mount_to(_app)
    return _app


@pytest_asyncio.fixture()
async def client(app: Starlette) -> AsyncClient:
    async with csrf_async_client(app) as ac:
        yield ac


@pytest_asyncio.fixture()
async def client_auto(app_auto: Starlette) -> AsyncClient:
    async with csrf_async_client(app_auto) as ac:
        yield ac


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestSQLModelInline:
    async def test_create_page_renders(self, client: AsyncClient) -> None:
        resp = await client.get("/admin/sm-post/create")
        assert resp.status_code == 200
        assert "sm-comment" in resp.text

    async def test_create_with_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        resp = await client.post(
            "/admin/sm-post/create",
            data={
                "title": "My Post",
                "inlines.sm-comment.0.body": "Hello World! This is long enough.",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        posts = session.exec(select(SMPost)).all()
        assert len(posts) == 1
        comments = session.exec(select(SMComment)).all()
        assert len(comments) == 1
        assert comments[0].body == "Hello World! This is long enough."
        assert comments[0].post_id == posts[0].id

    async def test_create_empty_inline_row_skipped(
        self, client: AsyncClient, session: Session
    ) -> None:
        resp = await client.post(
            "/admin/sm-post/create",
            data={"title": "No Comments"},
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text
        assert session.exec(select(SMComment)).first() is None

    async def test_edit_page_renders_existing_inlines(
        self, client: AsyncClient, session: Session
    ) -> None:
        post = SMPost(title="Existing")
        session.add(post)
        session.flush()
        comment = SMComment(body="old comment that is long", post_id=post.id)
        session.add(comment)
        session.commit()
        post_id = post.id
        session.expire_all()

        resp = await client.get(f"/admin/sm-post/edit?pk={post_id}")
        assert resp.status_code == 200
        assert "old comment that is long" in resp.text

    async def test_edit_adds_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        post = SMPost(title="Draft")
        session.add(post)
        session.commit()
        post_id = post.id
        session.expire_all()

        resp = await client.post(
            f"/admin/sm-post/edit?pk={post_id}",
            data={
                "title": "Published",
                "inlines.sm-comment.0.body": "A new comment that is long enough.",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        comments = session.exec(select(SMComment)).all()
        assert len(comments) == 1
        assert comments[0].post_id == post_id

    async def test_edit_deletes_inline(
        self, client: AsyncClient, session: Session
    ) -> None:
        post = SMPost(title="With comment")
        session.add(post)
        session.flush()
        comment = SMComment(body="to delete this old comment", post_id=post.id)
        session.add(comment)
        session.commit()
        post_id = post.id
        comment_id = comment.id
        session.expire_all()

        resp = await client.post(
            f"/admin/sm-post/edit?pk={post_id}",
            data={
                "title": "With comment",
                "inlines.sm-comment.0.pk": str(comment_id),
                "inlines.sm-comment.0.body": "to delete this old comment",
                "inlines.sm-comment.0.DELETE": "on",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text
        assert session.exec(select(SMComment)).first() is None

    async def test_inline_validation_error(
        self, client: AsyncClient, session: Session
    ) -> None:
        """Body shorter than min_length=10 triggers 422 via Pydantic validation.

        The parent post may still be committed, but
        the invalid comment row must NOT be persisted.
        """
        resp = await client.post(
            "/admin/sm-post/create",
            data={
                "title": "My Post",
                "inlines.sm-comment.0.body": "short",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 422
        assert session.exec(select(SMComment)).first() is None


class TestSQLModelInlineAutoFK:
    """Same scenarios with auto-detected fk_attr."""

    async def test_auto_detect_create(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        resp = await client_auto.post(
            "/admin/sm-post-auto/create",
            data={
                "title": "Auto Post",
                "inlines.sm-comment.0.body": "Auto comment that is long enough.",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text

        posts = session.exec(select(SMPost)).all()
        assert len(posts) == 1
        comments = session.exec(select(SMComment)).all()
        assert len(comments) == 1
        assert comments[0].post_id == posts[0].id

    async def test_auto_detect_edit_page_renders(
        self, client_auto: AsyncClient, session: Session
    ) -> None:
        post = SMPost(title="Auto Draft")
        session.add(post)
        session.flush()
        comment = SMComment(body="auto comment that is long enough", post_id=post.id)
        session.add(comment)
        session.commit()
        post_id = post.id
        session.expire_all()

        resp = await client_auto.get(f"/admin/sm-post-auto/edit?pk={post_id}")
        assert resp.status_code == 200
        assert "auto comment that is long enough" in resp.text
