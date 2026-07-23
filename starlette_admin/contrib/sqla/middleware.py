from typing import cast

import anyio.to_thread
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from starlette_admin.contrib.sqla.types import (
    AsyncSessionProvider,
    SessionProvider,
    SyncSessionProvider,
)
from starlette_admin.helpers import run_on_commit_callbacks
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


def is_async_session_provider(session_provider: SessionProvider) -> bool:
    return isinstance(session_provider, (AsyncEngine, async_sessionmaker))


class DBSessionMiddleware(BaseHTTPMiddleware):
    """Provide a database session per request at `request.state.session`.

    The session is committed when the request produces a success response,
    and rolled back when the request raises, returns an error response
    (status >= 400), or the commit itself fails. Commit failures are
    re-raised so the client never receives a success response for data
    that was not persisted.

    ``session_provider`` may also be a ``sessionmaker`` / ``async_sessionmaker``,
    in which case it is called to obtain each request's session instead of
    constructing a plain ``Session``/``AsyncSession`` from an engine. This
    lets callers configure the session (custom ``class_``, ``autoflush``,
    binds, etc.) instead of relying on the default configuration.
    """

    def __init__(self, app: ASGIApp, session_provider: SessionProvider) -> None:
        super().__init__(app)
        self.session_provider = session_provider

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if isinstance(self.session_provider, (AsyncEngine, async_sessionmaker)):
            return await self._dispatch_async(
                request,
                call_next,
                cast(AsyncSessionProvider, self.session_provider),
            )
        return await self._dispatch_sync(
            request, call_next, cast(SyncSessionProvider, self.session_provider)
        )

    @staticmethod
    async def _dispatch_async(
        request: Request,
        call_next: RequestResponseEndpoint,
        session_provider: AsyncSessionProvider,
    ) -> Response:
        _log.debug(
            "DBSessionMiddleware: opening async session for %s %s",
            request.method,
            request.url.path,
        )
        session: AsyncSession = (
            cast(AsyncSession, session_provider())
            if isinstance(session_provider, async_sessionmaker)
            else AsyncSession(session_provider, expire_on_commit=False)
        )
        async with session:
            request.state.session = session
            try:
                response = await call_next(request)
            except Exception:
                _log.exception(
                    "DBSessionMiddleware: rolling back async session due to error"
                )
                await session.rollback()
                raise
            if response.status_code >= 400:
                # e.g. form validation failure: the transaction may hold a
                # failed flush, so it must not be committed.
                await session.rollback()
                return response
            try:
                await session.commit()
                _log.debug(
                    "DBSessionMiddleware: committed async session for %s %s",
                    request.method,
                    request.url.path,
                )
            except Exception:
                _log.exception(
                    "DBSessionMiddleware: commit failed, rolling back async session"
                )
                await session.rollback()
                raise
            await run_on_commit_callbacks(request)
            return response

    @staticmethod
    async def _dispatch_sync(
        request: Request,
        call_next: RequestResponseEndpoint,
        session_provider: SyncSessionProvider,
    ) -> Response:
        _log.debug(
            "DBSessionMiddleware: opening sync session for %s %s",
            request.method,
            request.url.path,
        )
        # Session() does not connect until first use, so it is safe to
        # construct here; all blocking calls below run in a worker thread.
        session: Session = (
            cast(Session, session_provider())
            if isinstance(session_provider, sessionmaker)
            else Session(session_provider, expire_on_commit=False)
        )
        try:
            request.state.session = session
            try:
                response = await call_next(request)
            except Exception:
                _log.exception(
                    "DBSessionMiddleware: rolling back sync session due to error"
                )
                await anyio.to_thread.run_sync(session.rollback)
                raise
            if response.status_code >= 400:
                # e.g. form validation failure: the transaction may hold a
                # failed flush, so it must not be committed.
                await anyio.to_thread.run_sync(session.rollback)
                return response
            try:
                await anyio.to_thread.run_sync(session.commit)
                _log.debug(
                    "DBSessionMiddleware: committed sync session for %s %s",
                    request.method,
                    request.url.path,
                )
            except Exception:
                _log.exception(
                    "DBSessionMiddleware: commit failed, rolling back sync session"
                )
                await anyio.to_thread.run_sync(session.rollback)
                raise
            await run_on_commit_callbacks(request)
            return response
        finally:
            await anyio.to_thread.run_sync(session.close)
