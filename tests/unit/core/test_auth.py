"""Unit tests for starlette_admin.auth helpers."""

from unittest.mock import MagicMock

import pytest
from httpx2 import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette_admin.auth.base import AdminUser, AuthMiddleware, BaseAuthProvider
from starlette_admin.helpers import safe_redirect_url


class _MinimalAuthProvider(BaseAuthProvider):
    async def authenticate(self, _request: Request) -> AdminUser | None:
        return AdminUser()


def test_base_auth_provider_get_routes_returns_empty():
    provider = _MinimalAuthProvider()
    assert provider.get_routes(templates=None) == []  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_emit_after_login_noop_without_events():
    """No admin has wired `events` onto the provider; the call must be a safe no-op."""
    provider = _MinimalAuthProvider()
    assert provider.events is None
    await provider._emit_after_login(MagicMock(spec=Request), AdminUser())


def test_safe_redirect_url_relative_url():
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/admin/"
    assert (
        safe_redirect_url("/admin/post/list", request, "/admin/") == "/admin/post/list"
    )


def test_safe_redirect_url_cross_origin_url():
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/admin/"
    assert (
        safe_redirect_url("http://evil.com/admin/post/list", request, "/admin/")
        == "/admin/"
    )


@pytest.mark.parametrize(
    "bad_url",
    [
        "//evil.com",  # protocol-relative
        "/\\evil.com",  # backslash trick
        "///evil.com",  # triple-slash
        "javascript:alert(1)",  # non-http(s) scheme
        "data:text/html,<h1>",  # data: scheme
        "vbscript:msgbox(1)",  # vbscript: scheme
        "evil.com/path",  # no leading slash
        "",  # empty
    ],
)
def test_safe_redirect_url_rejects_unsafe(bad_url: str):
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/"
    assert safe_redirect_url(bad_url, request, "/fallback/") == "/fallback/"


@pytest.mark.asyncio
async def test_auth_middleware_raises_on_non_admin_user():
    """authenticate() returning a non-AdminUser object must raise TypeError."""

    class _BadProvider(BaseAuthProvider):
        async def authenticate(self, request: Request):  # type: ignore[override]
            return object()  # not an AdminUser

    async def homepage(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(AuthMiddleware, provider=_BadProvider())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with pytest.raises(
            TypeError, match="authenticate\\(\\) must return an AdminUser"
        ):
            await client.get("/")


def test_safe_redirect_url_same_origin_absolute():
    request = MagicMock(spec=Request)
    request.base_url = "http://testserver/"
    assert (
        safe_redirect_url("http://testserver/admin/post/list", request, "/admin/")
        == "http://testserver/admin/post/list"
    )
