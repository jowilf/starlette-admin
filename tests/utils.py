"""Shared test utilities."""

import re
from contextlib import asynccontextmanager

from httpx2 import ASGITransport, AsyncClient
from starlette.testclient import TestClient


def has_invalid_feedback(html: str, message: str) -> bool:
    """Checks for an invalid-feedback div with the given message, regardless of its id attribute."""
    pattern = rf'<div class="invalid-feedback"[^>]*>{re.escape(message)}</div>'
    return re.search(pattern, html) is not None


def _get_csrf_cookie(client) -> str:
    """Returns the signed CSRF cookie value, fetching one if necessary."""
    token = client.cookies.get("starlette_admin_csrftoken", "")
    if not token:
        client.get("/admin/")
        token = client.cookies.get("starlette_admin_csrftoken", "")
    return token


class CsrfTestClient(TestClient):
    """Drop-in replacement for `TestClient` that automatically handles CSRF.

    Upon construction, the admin index is accessed, prompting the server to set a signed `starlette_admin_csrftoken` cookie. Every mutating request (POST, PUT, PATCH, or DELETE) then receives an `X-CSRFToken` header set to this same signed value, satisfying the double-submit cookie check without requiring tests to manually manage the token."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._csrf_token = _get_csrf_cookie(self)

    def _csrf_headers(self, extra: dict | None) -> dict:
        hdrs = dict(extra or {})
        hdrs.setdefault("X-CSRFToken", self._csrf_token)
        return hdrs

    def post(self, url, **kwargs):
        kwargs["headers"] = self._csrf_headers(kwargs.pop("headers", None))
        return super().post(url, **kwargs)

    def put(self, url, **kwargs):
        kwargs["headers"] = self._csrf_headers(kwargs.pop("headers", None))
        return super().put(url, **kwargs)

    def patch(self, url, **kwargs):
        kwargs["headers"] = self._csrf_headers(kwargs.pop("headers", None))
        return super().patch(url, **kwargs)

    def delete(self, url, **kwargs):
        kwargs["headers"] = self._csrf_headers(kwargs.pop("headers", None))
        return super().delete(url, **kwargs)


async def make_csrf_async_client(
    app, base_url: str = "http://testserver"
) -> AsyncClient:
    """Returns an `httpx2 AsyncClient` with a server-signed CSRF cookie.

    The client initially accesses the admin index to obtain a signed `starlette_admin_csrftoken` cookie. Subsequently, it attaches an `X-CSRFToken` to every non-safe request."""
    token_holder = {"value": ""}

    async def _attach_csrf(request):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            request.headers["X-CSRFToken"] = token_holder["value"]

    client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url=base_url,
        event_hooks={"request": [_attach_csrf]},
    )
    await client.get("/admin/")
    token_holder["value"] = client.cookies.get("starlette_admin_csrftoken", "")
    return client


@asynccontextmanager
async def csrf_async_client(app, base_url: str = "http://testserver"):
    """Asynchronous context-manager variant that seeds a signed CSRF cookie."""
    token_holder = {"value": ""}

    async def _attach_csrf(request):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            request.headers["X-CSRFToken"] = token_holder["value"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=base_url,
        event_hooks={"request": [_attach_csrf]},
    ) as client:
        await client.get("/admin/")
        token_holder["value"] = client.cookies.get("starlette_admin_csrftoken", "")
        yield client
