"""Integration tests for the event system wired through a real BaseAdmin + TestClient.

These tests exercise the full path: HTTP request → base.py route handler →
TinydbModelView.create/edit/delete → _emit_* helpers → EventBus.emit →
registered handlers. The AdminEventBus delegation to per-view buses is also
verified here.
"""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette_admin import BaseAdmin, IntegerField, StringField
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

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient

# Fixtures


class Article(TinydbBaseModel):
    title: str
    body: str = ""


class ArticleView(TinydbModelView):
    key = "article"
    fields = [IntegerField("id"), StringField("title"), StringField("body")]


def _make_app() -> tuple[Starlette, BaseAdmin, ArticleView]:
    """Return a fresh (app, admin, view) triple with ArticleView registered."""
    admin = BaseAdmin()
    app = Starlette()
    view_instance = ArticleView(Article)
    admin.add_view(view_instance)
    admin.mount_to(app)
    return app, admin, view_instance


@pytest.fixture(autouse=True)
def _reset_db():
    ArticleView._db.truncate()
    ArticleView._db.insert(Article(title="Existing", body="old body").to_tinydb_doc())


# BEFORE_CREATE / AFTER_CREATE


def test_create_fires_before_and_after_events():
    app, admin, _ = _make_app()
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_CREATE, collected.append)
    admin.events.on(AdminEvent.AFTER_CREATE, collected.append)

    client = CsrfTestClient(app, base_url="http://testserver")
    resp = client.post(
        "/admin/article/create",
        data={"title": "New Post", "body": "some content"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeCreateContext)
    assert before.event == AdminEvent.BEFORE_CREATE
    assert before.resource == "article"
    assert before.data["title"] == "New Post"

    assert isinstance(after, AfterCreateContext)
    assert after.event == AdminEvent.AFTER_CREATE
    assert after.resource == "article"
    assert after.obj.title == "New Post"


def test_before_create_fires_before_db_insert():
    """The BEFORE_CREATE handler must run before the record is persisted."""
    app, admin, _ = _make_app()
    db_count_at_before: list[int] = []

    def capture(ctx: EventContext) -> None:
        db_count_at_before.append(ArticleView._len())

    admin.events.on(AdminEvent.BEFORE_CREATE, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/create", data={"title": "x", "body": ""})

    assert db_count_at_before == [
        1
    ]  # Before the operation, the count is 1 (only "Existing").


def test_after_create_fires_after_db_insert():
    """The AFTER_CREATE handler must run after the record is persisted."""
    app, admin, _ = _make_app()
    db_count_at_after: list[int] = []

    def capture(ctx: EventContext) -> None:
        db_count_at_after.append(ArticleView._len())

    admin.events.on(AdminEvent.AFTER_CREATE, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/create", data={"title": "x", "body": ""})

    assert db_count_at_after == [
        2
    ]  # The collection now includes "Existing" and the new record.


# BEFORE_EDIT / AFTER_EDIT


def test_edit_fires_before_and_after_events():
    app, admin, _ = _make_app()
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_EDIT, collected.append)
    admin.events.on(AdminEvent.AFTER_EDIT, collected.append)

    client = CsrfTestClient(app, base_url="http://testserver")
    resp = client.post(
        "/admin/article/edit?pk=1",
        data={"title": "Updated Title", "body": "new body"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeEditContext)
    assert before.event == AdminEvent.BEFORE_EDIT
    assert before.resource == "article"
    assert before.pk == 1
    assert before.data["title"] == "Updated Title"
    assert before.old_data["title"] == "Existing"

    assert isinstance(after, AfterEditContext)
    assert after.event == AdminEvent.AFTER_EDIT
    assert after.resource == "article"
    assert after.pk == 1
    assert after.obj.title == "Updated Title"
    assert after.old_data["title"] == "Existing"


def test_before_update_fires_before_db_write():
    """The BEFORE_EDIT handler sees the old stored value."""
    app, admin, _ = _make_app()
    title_seen_at_before: list[str] = []

    def capture(ctx: EventContext) -> None:
        stored = ArticleView._get(1)
        title_seen_at_before.append(stored.title if stored else "")

    admin.events.on(AdminEvent.BEFORE_EDIT, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/edit?pk=1", data={"title": "Changed", "body": ""})

    assert title_seen_at_before == ["Existing"]


def test_after_update_fires_after_db_write():
    """The AFTER_EDIT handler sees the new stored value."""
    app, admin, _ = _make_app()
    title_seen_at_after: list[str] = []

    def capture(ctx: EventContext) -> None:
        stored = ArticleView._get(1)
        title_seen_at_after.append(stored.title if stored else "")

    admin.events.on(AdminEvent.AFTER_EDIT, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/edit?pk=1", data={"title": "Changed", "body": ""})

    assert title_seen_at_after == ["Changed"]


# BEFORE_DELETE / AFTER_DELETE


def test_delete_fires_before_and_after_events():
    app, admin, _ = _make_app()
    collected: list[EventContext] = []

    admin.events.on(AdminEvent.BEFORE_DELETE, collected.append)
    admin.events.on(AdminEvent.AFTER_DELETE, collected.append)

    client = CsrfTestClient(app, base_url="http://testserver")
    resp = client.post(
        "/admin/_api/article/action",
        params={"name": "delete", "pks": ["1"]},
    )
    assert resp.status_code == 200
    assert len(collected) == 2

    before, after = collected
    assert isinstance(before, BeforeDeleteContext)
    assert before.event == AdminEvent.BEFORE_DELETE
    assert before.resource == "article"
    assert before.obj.id == 1

    assert isinstance(after, AfterDeleteContext)
    assert after.event == AdminEvent.AFTER_DELETE
    assert after.resource == "article"
    assert after.obj.id == 1


def test_before_delete_fires_before_db_removal():
    """The BEFORE_DELETE handler can still find the record in the DB."""
    app, admin, _ = _make_app()
    found_at_before: list[bool] = []

    def capture(ctx: EventContext) -> None:
        found_at_before.append(ArticleView._get(1) is not None)

    admin.events.on(AdminEvent.BEFORE_DELETE, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/_api/article/action", params={"name": "delete", "pks": ["1"]})

    assert found_at_before == [True]


def test_after_delete_fires_after_db_removal():
    """The AFTER_DELETE handler can no longer find the record in the DB."""
    app, admin, _ = _make_app()
    found_at_after: list[bool] = []

    def capture(ctx: EventContext) -> None:
        found_at_after.append(ArticleView._get(1) is not None)

    admin.events.on(AdminEvent.AFTER_DELETE, capture)

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/_api/article/action", params={"name": "delete", "pks": ["1"]})

    assert found_at_after == [False]


# AdminEventBus wiring


def test_admin_bus_handler_registered_after_view_still_fires():
    """Handlers added to admin.events after add_view() still propagate."""
    app, admin, _ = _make_app()
    fired: list[bool] = []

    # A handler registered after mounting must still reach the view bus.
    admin.events.on(AdminEvent.AFTER_CREATE, lambda ctx: fired.append(True))

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/create", data={"title": "t", "body": ""})

    assert fired == [True]


def test_admin_bus_keys_filter():
    """Handlers with keys= fire only for the matching view."""

    class PostModel(TinydbBaseModel):
        title: str

    class PostView(TinydbModelView):
        key = "post"
        fields = [IntegerField("id"), StringField("title")]

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.add_view(PostView(PostModel))
    admin.mount_to(app)

    article_events: list[str] = []
    post_events: list[str] = []

    admin.events.on(
        AdminEvent.AFTER_CREATE,
        lambda ctx: article_events.append(ctx.resource),
        keys=["article"],
    )
    admin.events.on(
        AdminEvent.AFTER_CREATE,
        lambda ctx: post_events.append(ctx.resource),
        keys=["post"],
    )

    client = CsrfTestClient(app, base_url="http://testserver")
    client.post("/admin/article/create", data={"title": "a", "body": ""})
    client.post("/admin/post/create", data={"title": "p"})

    assert article_events == ["article"]
    assert post_events == ["post"]
