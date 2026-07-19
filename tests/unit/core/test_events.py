"""Unit tests for starlette_admin.events."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette_admin.events import (
    AdminEvent,
    AdminEventBus,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    AfterExportContext,
    AfterImportContext,
    BeforeCreateContext,
    BeforeDeleteContext,
    BeforeEditContext,
    BeforeExportContext,
    BeforeImportContext,
    EventBus,
    EventContext,
    on,
)
from starlette_admin.export import CsvExporter
from starlette_admin.importers import CsvImporter

CSV_EXPORTER = CsvExporter()
CSV_IMPORTER = CsvImporter()

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/admin/create",
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


def _ctx(event: AdminEvent = AdminEvent.BEFORE_CREATE) -> EventContext:
    return EventContext(event=event, request=_make_request(), resource="test")


# ── EventBus.on ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_handler_is_called():
    bus = EventBus()
    called = []

    async def h(ctx: EventContext) -> None:
        called.append(ctx.event)

    bus.on(AdminEvent.BEFORE_CREATE, h)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert called == [AdminEvent.BEFORE_CREATE]


@pytest.mark.asyncio
async def test_on_decorator_form():
    bus = EventBus()
    called = []

    @bus.on(AdminEvent.AFTER_CREATE)
    async def h(ctx: EventContext) -> None:
        called.append(True)

    await bus.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert called == [True]


@pytest.mark.asyncio
async def test_on_handlers_not_called_for_different_event():
    bus = EventBus()
    called = []

    async def h(ctx: EventContext) -> None:
        called.append(True)

    bus.on(AdminEvent.BEFORE_CREATE, h)
    await bus.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert called == []


@pytest.mark.asyncio
async def test_on_priority_order():
    """Higher priority handlers run first."""
    bus = EventBus()
    order = []

    async def h_low(ctx: EventContext) -> None:
        order.append("low")

    async def h_high(ctx: EventContext) -> None:
        order.append("high")

    bus.on(AdminEvent.BEFORE_CREATE, h_low, priority=0)
    bus.on(AdminEvent.BEFORE_CREATE, h_high, priority=10)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert order == ["high", "low"]


# ── EventBus.off ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_off_removes_handler():
    bus = EventBus()
    called = []

    async def h(ctx: EventContext) -> None:
        called.append(True)

    bus.on(AdminEvent.BEFORE_CREATE, h)
    bus.off(AdminEvent.BEFORE_CREATE, h)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert called == []


# ── Exception handling ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exception_in_after_handler_propagates():
    bus = EventBus()

    async def h(ctx: EventContext) -> None:
        raise ValueError("oops")

    bus.on(AdminEvent.AFTER_CREATE, h)
    with pytest.raises(ValueError, match="oops"):
        await bus.emit(_ctx(AdminEvent.AFTER_CREATE))


@pytest.mark.asyncio
async def test_exception_in_before_handler_propagates():
    bus = EventBus()

    async def h(ctx: EventContext) -> None:
        raise RuntimeError("fail")

    bus.on(AdminEvent.BEFORE_CREATE, h)
    with pytest.raises(RuntimeError, match="fail"):
        await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))


# ── AdminEventSubscriber / subscribe ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_registers_handlers():
    bus = EventBus()
    calls: list[str] = []

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {
                AdminEvent.BEFORE_CREATE: self.on_before,
                AdminEvent.AFTER_CREATE: (self.on_after, 5),
            }

        async def on_before(self, ctx):
            calls.append("before")

        async def on_after(self, ctx):
            calls.append("after")

    sub = MySub()
    bus.subscribe(sub)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    await bus.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert calls == ["before", "after"]


@pytest.mark.asyncio
async def test_unsubscribe_removes_all_handlers():
    bus = EventBus()
    calls: list = []

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.BEFORE_CREATE: self.h}

        async def h(self, ctx):
            calls.append(True)

    sub = MySub()
    bus.subscribe(sub)
    bus.unsubscribe(sub)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == []


# ── AdminEventBus: view lifecycle delegation ─────────────────────────────────


@pytest.mark.asyncio
async def test_admin_bus_delegates_to_view_bus():
    admin_bus = AdminEventBus()
    view_bus = EventBus()
    calls: list = []

    async def h(ctx):
        calls.append(True)

    admin_bus.on(AdminEvent.BEFORE_CREATE, h)
    admin_bus._register_view("order", view_bus)
    await view_bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == [True]


@pytest.mark.asyncio
async def test_admin_bus_delegates_after_view_registered():
    """Subscriptions added *after* a view is registered still propagate."""
    admin_bus = AdminEventBus()
    view_bus = EventBus()
    calls: list = []

    admin_bus._register_view("order", view_bus)

    async def h(ctx):
        calls.append(True)

    admin_bus.on(AdminEvent.BEFORE_CREATE, h)
    await view_bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == [True]


@pytest.mark.asyncio
async def test_admin_bus_key_filter():
    """keys= restricts which views receive the handler."""
    admin_bus = AdminEventBus()
    bus_order = EventBus()
    bus_product = EventBus()
    calls: list[str] = []

    async def h(ctx):
        calls.append("fired")

    admin_bus.on(AdminEvent.BEFORE_CREATE, h, keys=["order"])
    admin_bus._register_view("order", bus_order)
    admin_bus._register_view("product", bus_product)

    await bus_order.emit(_ctx(AdminEvent.BEFORE_CREATE))
    await bus_product.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == ["fired"]  # only once, from order


@pytest.mark.asyncio
async def test_admin_bus_subscribe_delegates():
    admin_bus = AdminEventBus()
    view_bus = EventBus()
    calls: list = []

    class AuditSub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.AFTER_CREATE: self.record}

        async def record(self, ctx):
            calls.append("audit")

    admin_bus.subscribe(AuditSub())
    admin_bus._register_view("order", view_bus)
    await view_bus.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert calls == ["audit"]


@pytest.mark.asyncio
async def test_admin_bus_off_removes_from_all_views():
    admin_bus = AdminEventBus()
    bus1, bus2 = EventBus(), EventBus()
    calls: list = []

    async def h(ctx):
        calls.append(True)

    admin_bus.on(AdminEvent.BEFORE_CREATE, h)
    admin_bus._register_view("a", bus1)
    admin_bus._register_view("b", bus2)
    admin_bus.off(AdminEvent.BEFORE_CREATE, h)

    await bus1.emit(_ctx(AdminEvent.BEFORE_CREATE))
    await bus2.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == []


@pytest.mark.asyncio
async def test_admin_bus_unsubscribe_removes_from_all_views():
    """AdminEventBus.unsubscribe purges handlers from every registered view bus."""
    admin_bus = AdminEventBus()
    bus1, bus2 = EventBus(), EventBus()
    calls: list = []

    class AuditSub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.AFTER_CREATE: self.record}

        async def record(self, ctx):
            calls.append(True)

    sub = AuditSub()
    admin_bus.subscribe(sub)
    admin_bus._register_view("a", bus1)
    admin_bus._register_view("b", bus2)
    admin_bus.unsubscribe(sub)

    await bus1.emit(_ctx(AdminEvent.AFTER_CREATE))
    await bus2.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert calls == []


# ── BaseModelView._emit_* integration ────────────────────────────────────────


@pytest.mark.asyncio
async def test_emit_before_create_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.before_create = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.BEFORE_CREATE, emitted.append)

    await BaseModelView._emit_before_create(
        view, _make_request(), {"title": "x"}, object()
    )
    view.before_create.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, BeforeCreateContext)
    assert ctx.event == AdminEvent.BEFORE_CREATE
    assert ctx.resource == "article"
    assert ctx.data == {"title": "x"}


@pytest.mark.asyncio
async def test_emit_after_create_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.after_create = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.AFTER_CREATE, emitted.append)

    obj = object()
    await BaseModelView._emit_after_create(view, _make_request(), obj)
    view.after_create.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, AfterCreateContext)
    assert ctx.event == AdminEvent.AFTER_CREATE
    assert ctx.resource == "article"
    assert ctx.obj is obj


@pytest.mark.asyncio
async def test_emit_before_edit_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.before_edit = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.BEFORE_EDIT, emitted.append)

    obj = object()
    await BaseModelView._emit_before_edit(
        view, _make_request(), {"name": "y"}, obj, pk=42, old_data={"name": "x"}
    )
    view.before_edit.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, BeforeEditContext)
    assert ctx.event == AdminEvent.BEFORE_EDIT
    assert ctx.resource == "article"
    assert ctx.pk == 42
    assert ctx.data == {"name": "y"}
    assert ctx.old_data == {"name": "x"}
    assert ctx.obj is obj


@pytest.mark.asyncio
async def test_emit_after_edit_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.after_edit = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.AFTER_EDIT, emitted.append)

    obj = object()
    await BaseModelView._emit_after_edit(
        view, _make_request(), obj, pk=42, old_data={"name": "x"}
    )
    view.after_edit.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, AfterEditContext)
    assert ctx.event == AdminEvent.AFTER_EDIT
    assert ctx.resource == "article"
    assert ctx.pk == 42
    assert ctx.old_data == {"name": "x"}
    assert ctx.obj is obj


@pytest.mark.asyncio
async def test_emit_before_delete_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.before_delete = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.BEFORE_DELETE, emitted.append)

    obj = object()
    await BaseModelView._emit_before_delete(view, _make_request(), 99, obj)
    view.before_delete.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, BeforeDeleteContext)
    assert ctx.event == AdminEvent.BEFORE_DELETE
    assert ctx.resource == "article"
    assert ctx.pk == 99
    assert ctx.obj is obj


@pytest.mark.asyncio
async def test_emit_after_delete_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.after_delete = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.AFTER_DELETE, emitted.append)

    obj = object()
    await BaseModelView._emit_after_delete(view, _make_request(), 99, obj)
    view.after_delete.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, AfterDeleteContext)
    assert ctx.event == AdminEvent.AFTER_DELETE
    assert ctx.resource == "article"
    assert ctx.pk == 99
    assert ctx.obj is obj


@pytest.mark.asyncio
async def test_emit_before_export_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.before_export = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.BEFORE_EXPORT, emitted.append)

    export_ctx = MagicMock()
    items = [object(), object()]
    await BaseModelView._emit_before_export(
        view, _make_request(), CSV_EXPORTER, items, export_ctx
    )
    view.before_export.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, BeforeExportContext)
    assert ctx.event == AdminEvent.BEFORE_EXPORT
    assert ctx.resource == "article"
    assert ctx.export_type is CSV_EXPORTER
    assert ctx.items is items
    assert ctx.export_ctx is export_ctx


@pytest.mark.asyncio
async def test_emit_after_export_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.after_export = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.AFTER_EXPORT, emitted.append)

    export_ctx = MagicMock()
    items = [object(), object(), object()]
    await BaseModelView._emit_after_export(
        view, _make_request(), CSV_EXPORTER, items, export_ctx
    )
    view.after_export.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, AfterExportContext)
    assert ctx.event == AdminEvent.AFTER_EXPORT
    assert ctx.resource == "article"
    assert ctx.export_type is CSV_EXPORTER
    assert ctx.items is items
    assert ctx.row_count == 3
    assert ctx.export_ctx is export_ctx


@pytest.mark.asyncio
async def test_emit_before_import_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.before_import = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.BEFORE_IMPORT, emitted.append)

    import_ctx = MagicMock()
    await BaseModelView._emit_before_import(
        view, _make_request(), CSV_IMPORTER, import_ctx
    )
    view.before_import.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, BeforeImportContext)
    assert ctx.event == AdminEvent.BEFORE_IMPORT
    assert ctx.resource == "article"
    assert ctx.import_type is CSV_IMPORTER
    assert ctx.import_ctx is import_ctx


@pytest.mark.asyncio
async def test_emit_after_import_calls_hook_and_emits():
    from starlette_admin.views import BaseModelView

    view = MagicMock(spec=BaseModelView)
    view.key = "article"
    view.events = EventBus()
    view.after_import = AsyncMock()

    emitted: list[EventContext] = []
    view.events.on(AdminEvent.AFTER_IMPORT, emitted.append)

    import_ctx = MagicMock()
    result = MagicMock()
    result.rows_total = 5
    result.errors = ["err1", "err2"]
    await BaseModelView._emit_after_import(
        view, _make_request(), CSV_IMPORTER, result, import_ctx
    )
    view.after_import.assert_awaited_once()
    assert len(emitted) == 1
    ctx = emitted[0]
    assert isinstance(ctx, AfterImportContext)
    assert ctx.event == AdminEvent.AFTER_IMPORT
    assert ctx.resource == "article"
    assert ctx.import_type is CSV_IMPORTER
    assert ctx.row_count == 5
    assert ctx.error_count == 2
    assert ctx.import_ctx is import_ctx


# ── List spec in subscriptions ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_list_spec():
    """A list value in subscriptions() registers multiple handlers for one event."""
    bus = EventBus()
    calls: list[str] = []

    class Multi(AdminEventSubscriber):
        def subscriptions(self):
            return {
                AdminEvent.BEFORE_CREATE: [self.h1, (self.h2, 5)],
            }

        async def h1(self, ctx):
            calls.append("h1")

        async def h2(self, ctx):
            calls.append("h2")

    bus.subscribe(Multi())
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert set(calls) == {"h1", "h2"}


# ── @on decorator on subscriber methods ──────────────────────────────────────


@pytest.mark.asyncio
async def test_on_decorator_basic():
    """@on marks a method; subscriptions() discovers it automatically."""
    bus = EventBus()
    calls: list[str] = []

    class MyHandler(AdminEventSubscriber):
        @on(AdminEvent.BEFORE_CREATE)
        async def handle(self, _):
            calls.append("fired")

    bus.subscribe(MyHandler())
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == ["fired"]


@pytest.mark.asyncio
async def test_on_decorator_multiple_events():
    """A single method can be decorated for multiple events."""
    bus = EventBus()
    calls: list[AdminEvent] = []

    class MyHandler(AdminEventSubscriber):
        @on(AdminEvent.BEFORE_CREATE, AdminEvent.BEFORE_EDIT)
        async def handle(self, ctx):
            calls.append(ctx.event)

    bus.subscribe(MyHandler())
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    await bus.emit(_ctx(AdminEvent.BEFORE_EDIT))
    assert calls == [AdminEvent.BEFORE_CREATE, AdminEvent.BEFORE_EDIT]


@pytest.mark.asyncio
async def test_on_decorator_priority():
    """priority= on @on is respected by the bus."""
    bus = EventBus()
    order: list[str] = []

    class MyHandler(AdminEventSubscriber):
        @on(AdminEvent.BEFORE_CREATE, priority=10)
        async def high(self, _):
            order.append("high")

        @on(AdminEvent.BEFORE_CREATE)
        async def low(self, _):
            order.append("low")

    bus.subscribe(MyHandler())
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert order == ["high", "low"]


@pytest.mark.asyncio
async def test_on_decorator_not_fired_for_other_event():
    """Handler decorated for one event is not called for another."""
    bus = EventBus()
    calls: list = []

    class MyHandler(AdminEventSubscriber):
        @on(AdminEvent.BEFORE_CREATE)
        async def handle(self, _):
            calls.append(True)

    bus.subscribe(MyHandler())
    await bus.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert calls == []


@pytest.mark.asyncio
async def test_on_decorator_unsubscribe():
    """Handlers registered via @on are removed when the subscriber is unsubscribed."""
    bus = EventBus()
    calls: list = []

    class MyHandler(AdminEventSubscriber):
        @on(AdminEvent.BEFORE_CREATE)
        async def handle(self, _):
            calls.append(True)

    sub = MyHandler()
    bus.subscribe(sub)
    bus.unsubscribe(sub)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == []


# ── coverage gaps ─────────────────────────────────────────────────────────────


def test_eventbus_unsubscribe_noop_when_not_subscribed():
    """EventBus.unsubscribe returns early without error if subscriber not registered."""
    bus = EventBus()

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {}

    bus.unsubscribe(MySub())  # must not raise


@pytest.mark.asyncio
async def test_eventbus_unsubscribe_tuple_spec():
    """EventBus.unsubscribe handles (handler, priority) tuple specs."""
    bus = EventBus()
    calls: list = []

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.BEFORE_CREATE: (self.h, 5)}

        async def h(self, ctx):
            calls.append(True)

    sub = MySub()
    bus.subscribe(sub)
    bus.unsubscribe(sub)
    await bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == []


@pytest.mark.asyncio
async def test_admin_bus_on_decorator_form():
    """AdminEventBus.on used as a decorator (no handler arg) returns a decorator."""
    admin_bus = AdminEventBus()
    view_bus = EventBus()
    calls: list = []

    @admin_bus.on(AdminEvent.BEFORE_CREATE)
    async def h(ctx):
        calls.append(True)

    admin_bus._register_view("order", view_bus)
    await view_bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == [True]


@pytest.mark.asyncio
async def test_admin_bus_subscribe_tuple_spec():
    """AdminEventBus.subscribe handles (handler, priority) tuple specs."""
    admin_bus = AdminEventBus()
    view_bus = EventBus()
    calls: list = []

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.BEFORE_CREATE: (self.h, 5)}

        async def h(self, ctx):
            calls.append(True)

    admin_bus.subscribe(MySub())
    admin_bus._register_view("order", view_bus)
    await view_bus.emit(_ctx(AdminEvent.BEFORE_CREATE))
    assert calls == [True]


@pytest.mark.asyncio
async def test_admin_bus_unsubscribe_tuple_spec():
    """AdminEventBus.unsubscribe handles (handler, priority) tuple specs."""
    admin_bus = AdminEventBus()
    bus1, bus2 = EventBus(), EventBus()
    calls: list = []

    class MySub(AdminEventSubscriber):
        def subscriptions(self):
            return {AdminEvent.AFTER_CREATE: (self.h, 5)}

        async def h(self, ctx):
            calls.append(True)

    sub = MySub()
    admin_bus.subscribe(sub)
    admin_bus._register_view("a", bus1)
    admin_bus._register_view("b", bus2)
    admin_bus.unsubscribe(sub)

    await bus1.emit(_ctx(AdminEvent.AFTER_CREATE))
    await bus2.emit(_ctx(AdminEvent.AFTER_CREATE))
    assert calls == []
