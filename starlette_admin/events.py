from __future__ import annotations

import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, cast

from starlette.requests import Request

if TYPE_CHECKING:
    from starlette_admin.actions import ActionSelection
    from starlette_admin.auth.base import AdminUser
    from starlette_admin.export import BaseExporter, ExportContext
    from starlette_admin.importers import BaseImporter, ImportContext

logger = logging.getLogger(__name__)


class AdminEvent(StrEnum):
    # Record lifecycle
    BEFORE_CREATE = "before_create"
    AFTER_CREATE = "after_create"
    AFTER_CREATE_COMMITTED = "after_create_committed"
    BEFORE_EDIT = "before_edit"
    AFTER_EDIT = "after_edit"
    AFTER_EDIT_COMMITTED = "after_edit_committed"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"
    AFTER_DELETE_COMMITTED = "after_delete_committed"

    # Actions
    BEFORE_ACTION = "before_action"
    AFTER_ACTION = "after_action"

    # Export / Import
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    BEFORE_IMPORT = "before_import"
    AFTER_IMPORT = "after_import"

    # Auth
    AFTER_LOGIN = "after_login"


@dataclass
class EventContext:
    """Base context present on every event."""

    event: AdminEvent | str
    request: Request
    view_key: str
    extra: dict = field(default_factory=dict)


# Record lifecycle


@dataclass
class BeforeCreateContext(EventContext):
    data: dict = field(default_factory=dict)
    obj: Any = None


@dataclass
class AfterCreateContext(EventContext):
    pk: Any = None
    obj: Any = None


@dataclass
class BeforeEditContext(EventContext):
    pk: Any = None
    data: dict = field(default_factory=dict)
    obj: Any = None
    old_data: dict = field(default_factory=dict)


@dataclass
class AfterEditContext(EventContext):
    pk: Any = None
    obj: Any = None
    old_data: dict = field(default_factory=dict)


@dataclass
class BeforeDeleteContext(EventContext):
    pk: Any = None
    obj: Any = None


@dataclass
class AfterDeleteContext(EventContext):
    pk: Any = None
    obj: Any = None


# Bulk operations


@dataclass
class BeforeBulkDeleteContext(EventContext):
    pks: list[Any] = field(default_factory=list)


@dataclass
class AfterBulkDeleteContext(EventContext):
    pks: list[Any] = field(default_factory=list)
    deleted_count: int = 0


# Actions


@dataclass
class BeforeActionContext(EventContext):
    """`selection.pks()` (and `.rows()`, `.count()`) are async and resolved lazily:
    call them from a handler only if you need the target rows, since a select-all
    action can otherwise skip materializing them entirely."""

    action_name: str = ""
    selection: ActionSelection | None = None


@dataclass
class AfterActionContext(EventContext):
    """See `BeforeActionContext` for `selection`'s lazy-resolution contract."""

    action_name: str = ""
    selection: ActionSelection | None = None
    success: bool = True
    error: str | None = None


# Export / Import


@dataclass
class BeforeExportContext(EventContext):
    export_type: BaseExporter | None = None
    items: Sequence[Any] = field(default_factory=list)
    export_ctx: ExportContext | None = None


@dataclass
class AfterExportContext(EventContext):
    export_type: BaseExporter | None = None
    items: Sequence[Any] = field(default_factory=list)
    row_count: int = 0
    export_ctx: ExportContext | None = None


@dataclass
class BeforeImportContext(EventContext):
    import_type: BaseImporter | None = None
    import_ctx: ImportContext | None = None


@dataclass
class AfterImportContext(EventContext):
    import_type: BaseImporter | None = None
    row_count: int = 0
    error_count: int = 0
    import_ctx: ImportContext | None = None


# Auth


@dataclass
class AfterLoginContext(EventContext):
    """`view_key` is always empty: login is not tied to any view."""

    user: AdminUser | None = None


EventHandler = Callable[["EventContext"], Awaitable[None]]
HandlerSpec = (
    EventHandler  # bare handler, priority=0
    | tuple[EventHandler, int]  # (handler, priority)
)

_ADMIN_EVENTS_ATTR = "_admin_events"


def on(*events: AdminEvent | str, priority: int = 0) -> Callable:
    """Decorator that marks a subscriber method as a handler for one or more events.

    Usage::

        class MyHandler(AdminEventSubscriber):
            @on(AdminEvent.BEFORE_CREATE, priority=10)
            async def handle(self, ctx):
                ...
    """

    def decorator(fn: Callable) -> Callable:
        if not hasattr(fn, _ADMIN_EVENTS_ATTR):
            fn._admin_events = []  # ty: ignore[invalid-assignment]
        for event in events:
            fn._admin_events.append((event, priority))  # ty: ignore[unresolved-attribute]
        return fn

    return decorator


class AdminEventSubscriber:
    def subscriptions(self) -> dict[AdminEvent | str, HandlerSpec | list[HandlerSpec]]:
        """Return event → handler(s) mapping.

        The default implementation discovers methods decorated with ``@on``.
        Override to use the explicit dict API instead.
        """
        result: dict[AdminEvent | str, list[HandlerSpec]] = defaultdict(list)
        seen: set[str] = set()
        for cls in type(self).__mro__:
            for name, fn in cls.__dict__.items():
                if name in seen or not callable(fn):
                    continue
                seen.add(name)
                specs = getattr(fn, _ADMIN_EVENTS_ATTR, None)
                if specs:
                    method = getattr(self, name)
                    for event, priority in specs:
                        result[event].append(
                            (method, priority) if priority != 0 else method
                        )
        return dict(result)


class EventBus:
    """Per-view event bus. This is the only bus type that emits events directly;
    [AdminEventBus][starlette_admin.events.AdminEventBus] delegates lifecycle
    events to the matching view's `EventBus` instead of emitting them itself.
    """

    def __init__(self) -> None:
        # Maps event name to a list of (priority, handler) pairs.
        self._handlers: dict[str, list[tuple[int, Callable]]] = defaultdict(list)
        self._subscribers: list[AdminEventSubscriber] = []

    def on(
        self,
        event: AdminEvent | str,
        handler: Callable[[EventContext], Awaitable[None]] | None = None,
        *,
        priority: int = 0,
    ) -> Callable:
        """Register a handler. Usable as a decorator or a direct call."""
        key = event.value if isinstance(event, AdminEvent) else event

        def _register(fn: Callable) -> Callable:
            self._handlers[key].append((priority, fn))
            self._handlers[key].sort(key=lambda x: x[0], reverse=True)
            logger.debug(
                "EventBus: registered handler %s for event %r (priority=%d)",
                fn.__qualname__,  # ty: ignore[unresolved-attribute]
                key,
                priority,
            )
            return fn

        if handler is not None:
            _register(handler)
            return handler
        return _register

    def subscribe(self, subscriber: AdminEventSubscriber) -> None:
        """Register a subscriber object for multiple events at once."""
        logger.debug("EventBus: subscribing %s", type(subscriber).__qualname__)
        self._subscribers.append(subscriber)
        for event, spec in subscriber.subscriptions().items():
            items = spec if isinstance(spec, list) else [spec]
            for item in items:
                if isinstance(item, tuple):
                    fn, prio = cast("tuple[EventHandler, int]", item)
                    self.on(event, fn, priority=prio)
                else:
                    self.on(event, cast(EventHandler, item))

    def off(self, event: AdminEvent | str, handler: Callable) -> None:
        """Remove a handler for an event."""
        key = event.value if isinstance(event, AdminEvent) else event
        self._handlers[key] = [(p, h) for (p, h) in self._handlers[key] if h != handler]

    def unsubscribe(self, subscriber: AdminEventSubscriber) -> None:
        """Remove all handlers registered by a subscriber."""
        if subscriber not in self._subscribers:
            return
        self._subscribers.remove(subscriber)
        for event, spec in subscriber.subscriptions().items():
            items = spec if isinstance(spec, list) else [spec]
            for item in items:
                if isinstance(item, tuple):
                    fn, _ = cast("tuple[EventHandler, int]", item)
                    self.off(event, fn)
                else:
                    self.off(event, cast(EventHandler, item))

    async def emit(self, ctx: EventContext) -> None:
        """Fire all registered handlers in priority order."""
        key = ctx.event.value if isinstance(ctx.event, AdminEvent) else ctx.event
        handlers = self._handlers.get(key, [])
        logger.debug("EventBus: emitting %r to %d handler(s)", key, len(handlers))

        for _priority, handler in handlers:
            logger.debug(
                "EventBus: calling %s (priority=%d)",
                handler.__qualname__,  # ty: ignore[unresolved-attribute]
                _priority,
            )
            result = handler(ctx)
            if inspect.isawaitable(result):
                await result


# View lifecycle events delegated by AdminEventBus to the matching view's EventBus
_VIEW_LIFECYCLE_EVENTS: frozenset[str] = frozenset(
    {
        AdminEvent.BEFORE_CREATE,
        AdminEvent.AFTER_CREATE,
        AdminEvent.AFTER_CREATE_COMMITTED,
        AdminEvent.BEFORE_EDIT,
        AdminEvent.AFTER_EDIT,
        AdminEvent.AFTER_EDIT_COMMITTED,
        AdminEvent.BEFORE_DELETE,
        AdminEvent.AFTER_DELETE,
        AdminEvent.AFTER_DELETE_COMMITTED,
        AdminEvent.BEFORE_ACTION,
        AdminEvent.AFTER_ACTION,
        AdminEvent.BEFORE_EXPORT,
        AdminEvent.AFTER_EXPORT,
        AdminEvent.BEFORE_IMPORT,
        AdminEvent.AFTER_IMPORT,
    }
)


def _is_view_lifecycle(event: AdminEvent | str) -> bool:
    key = event.value if isinstance(event, AdminEvent) else event
    return key in _VIEW_LIFECYCLE_EVENTS


@dataclass
class _PendingOn:
    event: AdminEvent | str
    handler: Callable
    keys: list[str] | None
    priority: int


class AdminEventBus:
    """Admin-level event bus. Delegates view lifecycle events to view buses;
    handles admin-level events (e.g. `AFTER_LOGIN`) itself, since they are not
    tied to any view."""

    def __init__(self) -> None:
        self._pending_on: list[_PendingOn] = []
        # Maps view key to its EventBus, populated as views are registered.
        self._view_buses: dict[str, EventBus] = {}
        # Handles events that are not tied to any view.
        self._bus = EventBus()

    def _register_view(self, key: str, bus: EventBus) -> None:
        """Called when a view is added to the admin; propagates pending subscriptions."""
        logger.debug("AdminEventBus: registering view %r", key)
        self._view_buses[key] = bus
        for p in self._pending_on:
            if _is_view_lifecycle(p.event) and (p.keys is None or key in p.keys):
                bus.on(p.event, p.handler, priority=p.priority)

    def on(
        self,
        event: AdminEvent | str,
        handler: Callable[[EventContext], Awaitable[None]] | None = None,
        *,
        keys: list[str] | None = None,
        priority: int = 0,
    ) -> Callable:
        """Register a handler. For view lifecycle events, delegates to matching view buses.
        Admin-level events (e.g. `AFTER_LOGIN`) are handled directly and ignore `keys`.

        Args:
            event: The event to handle.
            handler: The callback to invoke. If omitted, returns a decorator.
            keys: Restricts the handler to views whose key is in this
                list. `None` (the default) registers it for all views.
                Has no effect for admin-level events.
            priority: Handlers with a higher priority run first.
        """

        def _register(fn: Callable) -> Callable:
            if _is_view_lifecycle(event):
                pending = _PendingOn(event, fn, keys, priority)
                self._pending_on.append(pending)
                for key, bus in self._view_buses.items():
                    if keys is None or key in keys:
                        bus.on(event, fn, priority=priority)
            else:
                self._bus.on(event, fn, priority=priority)
            return fn

        if handler is not None:
            return _register(handler)
        return _register

    async def emit(self, ctx: EventContext) -> None:
        """Fire handlers registered for an admin-level event (e.g. `AFTER_LOGIN`).

        View lifecycle events are emitted by the matching view's `EventBus`
        instead; this is only for events not tied to any view.
        """
        await self._bus.emit(ctx)

    def subscribe(
        self,
        subscriber: AdminEventSubscriber,
        *,
        keys: list[str] | None = None,
    ) -> None:
        """Delegate all subscriptions declared by subscriber to matching view buses."""
        for sub_event, spec in subscriber.subscriptions().items():
            items = spec if isinstance(spec, list) else [spec]
            for item in items:
                if isinstance(item, tuple):
                    fn, prio = cast("tuple[EventHandler, int]", item)
                    self.on(sub_event, fn, keys=keys, priority=prio)
                else:
                    self.on(sub_event, cast(EventHandler, item), keys=keys)

    def off(self, event: AdminEvent | str, handler: Callable) -> None:
        """Remove a handler from all view buses, or from the admin-level bus."""
        if _is_view_lifecycle(event):
            self._pending_on = [
                p
                for p in self._pending_on
                if not (p.event == event and p.handler is handler)
            ]
            for bus in self._view_buses.values():
                bus.off(event, handler)
        else:
            self._bus.off(event, handler)

    def unsubscribe(self, subscriber: AdminEventSubscriber) -> None:
        """Remove all handlers from a subscriber across all buses."""
        for sub_event, spec in subscriber.subscriptions().items():
            items = spec if isinstance(spec, list) else [spec]
            for item in items:
                if isinstance(item, tuple):
                    fn, _ = cast("tuple[EventHandler, int]", item)
                    self.off(sub_event, fn)
                else:
                    self.off(sub_event, cast(EventHandler, item))
