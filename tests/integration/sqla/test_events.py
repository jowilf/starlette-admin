"""Integration tests for event firing through the SQLAlchemy ModelView.

Uses SQLite (both sync and async in-memory engines) to avoid container
dependencies.  Tests verify the full path: HTTP request →
sqla.ModelView.create/edit/delete → _emit_* helpers → EventBus.emit →
registered handlers.  AdminEventBus delegation to per-view buses is also
verified.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx2 import AsyncClient
from sqlalchemy import Integer, String, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView
from starlette_admin.events import (
    AdminEvent,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    BeforeCreateContext,
    BeforeDeleteContext,
    BeforeEditContext,
    EventContext,
)
from starlette_admin.exceptions import FormValidationError

from tests.utils import csrf_async_client


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "post_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))


class PostView(ModelView):
    pass


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(params=["sync", "async"])
async def engine(request):
    """SQLite in-memory engine, both sync and async, with tables + seed row."""
    if request.param == "sync":
        from sqlalchemy import create_engine

        eng: Engine | AsyncEngine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(eng)
        with Session(eng) as s:
            s.add(Post(title="Original"))
            s.commit()
        yield eng
        Base.metadata.drop_all(eng)
    else:
        eng = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSession(eng) as s:
            s.add(Post(title="Original"))
            await s.commit()
        yield eng
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest.fixture
def admin(engine: Engine | AsyncEngine):
    adm = Admin(engine)
    adm.add_view(PostView(Post))
    return adm


@pytest.fixture
def app(admin: Admin):
    application = Starlette()
    admin.mount_to(application)
    return application


@pytest.fixture
async def client(app):
    async with csrf_async_client(app) as c:
        yield c


def _seed_pk(engine: Engine | AsyncEngine) -> int:
    """Return the pk of the seeded 'Original' row."""
    if isinstance(engine, AsyncEngine):
        raise RuntimeError("use the async helper instead")
    with Session(engine) as s:
        return s.execute(select(Post.id)).scalar_one()


async def _seed_pk_async(engine: AsyncEngine) -> int:
    async with AsyncSession(engine) as s:
        return (await s.execute(select(Post.id))).scalar_one()


async def _get_pk(engine: Engine | AsyncEngine) -> int:
    if isinstance(engine, AsyncEngine):
        return await _seed_pk_async(engine)
    return _seed_pk(engine)


async def _count(engine: Engine | AsyncEngine) -> int:
    if isinstance(engine, AsyncEngine):
        async with AsyncSession(engine) as s:
            return (await s.execute(select(func.count(Post.id)))).scalar_one()
    with Session(engine) as s:
        return s.execute(select(func.count(Post.id))).scalar_one()


# ── BEFORE_CREATE / AFTER_CREATE ──────────────────────────────────────────────


async def test_create_fires_before_and_after_events(admin: Admin, client: AsyncClient):
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_CREATE, collected.append)
    admin.events.on(AdminEvent.AFTER_CREATE, collected.append)

    resp = await client.post(
        "/admin/post/create",
        data={"title": "New Post"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeCreateContext)
    assert before.event == AdminEvent.BEFORE_CREATE
    assert before.view_key == "post"
    assert before.data["title"] == "New Post"

    assert isinstance(after, AfterCreateContext)
    assert after.event == AdminEvent.AFTER_CREATE
    assert after.view_key == "post"
    assert after.obj.title == "New Post"


async def test_before_create_obj_pk_is_none(admin: Admin, client: AsyncClient):
    """BEFORE_CREATE fires before the DB assigns the PK (obj.id is None)."""
    pk_at_before: list[Any] = []

    admin.events.on(
        AdminEvent.BEFORE_CREATE, lambda ctx: pk_at_before.append(ctx.obj.id)
    )

    await client.post(
        "/admin/post/create",
        data={"title": "x"},
        follow_redirects=False,
    )

    assert pk_at_before == [None]


async def test_after_create_obj_has_pk(admin: Admin, client: AsyncClient):
    """AFTER_CREATE fires after DB insert + refresh so obj.id is assigned."""
    pk_at_after: list[Any] = []

    admin.events.on(AdminEvent.AFTER_CREATE, lambda ctx: pk_at_after.append(ctx.obj.id))

    await client.post(
        "/admin/post/create",
        data={"title": "y"},
        follow_redirects=False,
    )

    assert len(pk_at_after) == 1
    assert pk_at_after[0] is not None


# ── BEFORE_EDIT / AFTER_EDIT ──────────────────────────────────────────────────


async def test_edit_fires_before_and_after_events(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_EDIT, collected.append)
    admin.events.on(AdminEvent.AFTER_EDIT, collected.append)

    pk = await _get_pk(engine)
    resp = await client.post(
        f"/admin/post/edit?pk={pk}",
        data={"title": "Updated"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeEditContext)
    assert before.event == AdminEvent.BEFORE_EDIT
    assert before.view_key == "post"
    assert int(before.pk) == pk  # raw pk arrives as string from URL
    assert before.data["title"] == "Updated"
    assert before.old_data["title"] == "Original"

    assert isinstance(after, AfterEditContext)
    assert after.event == AdminEvent.AFTER_EDIT
    assert after.view_key == "post"
    assert int(after.pk) == pk
    assert after.obj.title == "Updated"
    assert after.old_data["title"] == "Original"


async def test_before_update_sees_old_data(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    """BEFORE_EDIT context carries the pre-update field values in old_data."""
    old_titles: list[str] = []

    admin.events.on(
        AdminEvent.BEFORE_EDIT,
        lambda ctx: old_titles.append(ctx.old_data.get("title", "")),
    )

    pk = await _get_pk(engine)
    await client.post(
        f"/admin/post/edit?pk={pk}",
        data={"title": "Changed"},
        follow_redirects=False,
    )

    assert old_titles == ["Original"]


async def test_after_update_obj_has_new_title(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    """AFTER_EDIT fires after commit so obj carries the persisted new value."""
    new_titles: list[str] = []

    admin.events.on(
        AdminEvent.AFTER_EDIT,
        lambda ctx: new_titles.append(ctx.obj.title),
    )

    pk = await _get_pk(engine)
    await client.post(
        f"/admin/post/edit?pk={pk}",
        data={"title": "Changed"},
        follow_redirects=False,
    )

    assert new_titles == ["Changed"]


# ── BEFORE_DELETE / AFTER_DELETE ──────────────────────────────────────────────


async def test_delete_fires_before_and_after_events(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_DELETE, collected.append)
    admin.events.on(AdminEvent.AFTER_DELETE, collected.append)

    pk = await _get_pk(engine)
    resp = await client.post(
        "/admin/_api/post/action",
        params={"name": "delete", "pks": [str(pk)]},
    )
    assert resp.status_code == 200
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeDeleteContext)
    assert before.event == AdminEvent.BEFORE_DELETE
    assert before.view_key == "post"
    assert before.obj.id == pk

    assert isinstance(after, AfterDeleteContext)
    assert after.event == AdminEvent.AFTER_DELETE
    assert after.view_key == "post"
    assert after.obj.id == pk


async def test_before_delete_fires_before_db_removal(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    """BEFORE_DELETE fires before session.delete(obj) is called."""
    count_at_before: list[int] = []

    async def capture(ctx: EventContext) -> None:
        count_at_before.append(await _count(engine))

    admin.events.on(AdminEvent.BEFORE_DELETE, capture)

    pk = await _get_pk(engine)
    await client.post(
        "/admin/_api/post/action",
        params={"name": "delete", "pks": [str(pk)]},
    )

    assert count_at_before == [1]


async def test_after_delete_fires_after_db_removal(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    """AFTER_DELETE fires after the commit that removes the record."""
    count_at_after: list[int] = []

    async def capture(ctx: EventContext) -> None:
        count_at_after.append(await _count(engine))

    admin.events.on(AdminEvent.AFTER_DELETE, capture)

    pk = await _get_pk(engine)
    await client.post(
        "/admin/_api/post/action",
        params={"name": "delete", "pks": [str(pk)]},
    )

    assert count_at_after == [0]


# ── AFTER_DELETE_COMMITTED ────────────────────────────────────────────────────


async def test_delete_fires_committed_event(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    """AFTER_DELETE_COMMITTED fires after AFTER_DELETE, with the row gone."""
    order: list[str] = []
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.AFTER_DELETE, lambda ctx: order.append("after"))

    def on_committed(ctx: EventContext) -> None:
        order.append("committed")
        collected.append(ctx)

    admin.events.on(AdminEvent.AFTER_DELETE_COMMITTED, on_committed)

    pk = await _get_pk(engine)
    resp = await client.post(
        "/admin/_api/post/action",
        params={"name": "delete", "pks": [str(pk)]},
    )
    assert resp.status_code == 200
    assert order == ["after", "committed"]

    (ctx,) = collected
    assert isinstance(ctx, AfterDeleteContext)
    assert ctx.event == AdminEvent.AFTER_DELETE_COMMITTED
    assert ctx.view_key == "post"
    assert int(ctx.pk) == pk
    # The object was expunged before commit, so reading an already-loaded
    # attribute here must not trigger a re-SELECT of the now-deleted row.
    assert ctx.obj.title == "Original"
    assert await _count(engine) == 0


async def test_committed_event_not_fired_on_commit_failure_after_delete(
    admin: Admin,
    client: AsyncClient,
    engine: Engine | AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
):
    """delete() itself succeeds (AFTER_DELETE fires, the commit callback is
    registered), but the middleware's final session.commit() then fails.
    AFTER_DELETE_COMMITTED must not fire since the transaction was rolled
    back, not committed."""
    after_delete: list[EventContext] = []
    committed: list[EventContext] = []
    admin.events.on(AdminEvent.AFTER_DELETE, after_delete.append)
    admin.events.on(AdminEvent.AFTER_DELETE_COMMITTED, committed.append)

    commit_cls = AsyncSession if isinstance(engine, AsyncEngine) else Session

    def _raise_integrity_error(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("COMMIT", {}, Exception("simulated commit failure"))

    async def _raise_integrity_error_async(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("COMMIT", {}, Exception("simulated commit failure"))

    monkeypatch.setattr(
        commit_cls,
        "commit",
        _raise_integrity_error_async
        if isinstance(engine, AsyncEngine)
        else _raise_integrity_error,
    )

    pk = await _get_pk(engine)
    with pytest.raises(IntegrityError):
        await client.post(
            "/admin/_api/post/action",
            params={"name": "delete", "pks": [str(pk)]},
        )

    assert len(after_delete) == 1
    assert committed == []


# ── AFTER_CREATE_COMMITTED / AFTER_EDIT_COMMITTED ────────────────────────────


async def test_create_fires_committed_event_after_flush_event(
    admin: Admin, client: AsyncClient
):
    """AFTER_CREATE_COMMITTED fires after AFTER_CREATE, with the same context data."""
    order: list[str] = []
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.AFTER_CREATE, lambda ctx: order.append("after"))

    def on_committed(ctx: EventContext) -> None:
        order.append("committed")
        collected.append(ctx)

    admin.events.on(AdminEvent.AFTER_CREATE_COMMITTED, on_committed)

    resp = await client.post(
        "/admin/post/create",
        data={"title": "Committed Post"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert order == ["after", "committed"]

    (ctx,) = collected
    assert isinstance(ctx, AfterCreateContext)
    assert ctx.event == AdminEvent.AFTER_CREATE_COMMITTED
    assert ctx.view_key == "post"
    assert ctx.obj.title == "Committed Post"
    assert ctx.pk is not None


async def test_edit_fires_committed_event(
    admin: Admin, client: AsyncClient, engine: Engine | AsyncEngine
):
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.AFTER_EDIT_COMMITTED, collected.append)

    pk = await _get_pk(engine)
    resp = await client.post(
        f"/admin/post/edit?pk={pk}",
        data={"title": "Committed Edit"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    (ctx,) = collected
    assert isinstance(ctx, AfterEditContext)
    assert ctx.event == AdminEvent.AFTER_EDIT_COMMITTED
    assert ctx.view_key == "post"
    assert int(ctx.pk) == pk
    assert ctx.obj.title == "Committed Edit"
    assert ctx.old_data["title"] == "Original"


async def test_committed_event_not_fired_on_validation_error(
    admin: Admin, client: AsyncClient
):
    """A rolled-back request (422) must not emit AFTER_CREATE_COMMITTED."""
    fired: list[EventContext] = []

    admin.events.on(AdminEvent.AFTER_CREATE_COMMITTED, fired.append)

    view = next(v for v in admin._views if getattr(v, "key", None) == "post")

    async def failing_validate(request: Any, data: dict[str, Any]) -> None:
        raise FormValidationError({"title": "always invalid"})

    view.validate = failing_validate

    resp = await client.post(
        "/admin/post/create",
        data={"title": "Never persisted"},
        follow_redirects=False,
    )
    assert resp.status_code == 422
    assert fired == []


async def test_committed_event_not_fired_on_session_error_during_create(
    admin: Admin,
    client: AsyncClient,
    engine: Engine | AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
):
    """A flush failure inside create() (e.g., a database constraint violation) must not
    emit AFTER_CREATE or AFTER_CREATE_COMMITTED. The row was never persisted."""
    after_create: list[EventContext] = []
    committed: list[EventContext] = []
    admin.events.on(AdminEvent.AFTER_CREATE, after_create.append)
    admin.events.on(AdminEvent.AFTER_CREATE_COMMITTED, committed.append)

    flush_cls = AsyncSession if isinstance(engine, AsyncEngine) else Session

    def _raise_integrity_error(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("INSERT", {}, Exception("simulated constraint violation"))

    async def _raise_integrity_error_async(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("INSERT", {}, Exception("simulated constraint violation"))

    monkeypatch.setattr(
        flush_cls,
        "flush",
        _raise_integrity_error_async
        if isinstance(engine, AsyncEngine)
        else _raise_integrity_error,
    )

    with pytest.raises(IntegrityError):
        await client.post(
            "/admin/post/create",
            data={"title": "Doomed"},
            follow_redirects=False,
        )

    assert after_create == []
    assert committed == []


async def test_committed_event_not_fired_on_commit_failure_after_create(
    admin: Admin,
    client: AsyncClient,
    engine: Engine | AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
):
    """create() itself succeeds (AFTER_CREATE fires, the commit callback is
    registered), but the middleware's final session.commit() then fails; for example, due to
    a deferred constraint violation. AFTER_CREATE_COMMITTED must not fire
    since the transaction was rolled back, not committed."""
    after_create: list[EventContext] = []
    committed: list[EventContext] = []
    admin.events.on(AdminEvent.AFTER_CREATE, after_create.append)
    admin.events.on(AdminEvent.AFTER_CREATE_COMMITTED, committed.append)

    commit_cls = AsyncSession if isinstance(engine, AsyncEngine) else Session

    def _raise_integrity_error(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("COMMIT", {}, Exception("simulated commit failure"))

    async def _raise_integrity_error_async(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("COMMIT", {}, Exception("simulated commit failure"))

    monkeypatch.setattr(
        commit_cls,
        "commit",
        _raise_integrity_error_async
        if isinstance(engine, AsyncEngine)
        else _raise_integrity_error,
    )

    with pytest.raises(IntegrityError):
        await client.post(
            "/admin/post/create",
            data={"title": "Doomed at commit"},
            follow_redirects=False,
        )

    assert len(after_create) == 1
    assert committed == []


# ── AdminEventBus wiring ──────────────────────────────────────────────────────


async def test_admin_bus_handler_fires_for_sqla_view(admin: Admin, client: AsyncClient):
    """Handlers on admin.events propagate to the sqla ModelView's event bus."""
    fired: list[bool] = []

    admin.events.on(AdminEvent.AFTER_CREATE, lambda ctx: fired.append(True))

    await client.post(
        "/admin/post/create",
        data={"title": "Bus test"},
        follow_redirects=False,
    )

    assert fired == [True]


async def test_view_bus_handler_fires_directly(
    admin: Admin, app: Starlette, client: AsyncClient
):
    """Handlers registered on the view's own EventBus also fire."""
    fired: list[str] = []

    view = next(v for v in admin._views if getattr(v, "key", None) == "post")
    view.events.on(AdminEvent.AFTER_CREATE, lambda ctx: fired.append(ctx.obj.title))

    await client.post(
        "/admin/post/create",
        data={"title": "Direct bus"},
        follow_redirects=False,
    )

    assert fired == ["Direct bus"]
