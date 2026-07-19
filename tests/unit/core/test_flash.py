import types

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette_admin.flash import FlashMiddleware, flash, get_flashed_messages


def _request():
    return types.SimpleNamespace(state=types.SimpleNamespace())


def test_flash_without_middleware_raises():
    request = _request()
    with pytest.raises(RuntimeError, match="FlashMiddleware"):
        flash(request, "test")


def test_get_flashed_messages_consumed_returns_empty():
    request = _request()
    request.state.admin_flash_consumed = True
    assert get_flashed_messages(request) == []


def test_get_flashed_messages_without_middleware_raises():
    request = _request()
    request.state.admin_flash_consumed = False
    with pytest.raises(RuntimeError, match="FlashMiddleware"):
        get_flashed_messages(request)


# ---------------------------------------------------------------------------
# Integration-style tests using a real FlashMiddleware stack.
#
# Flash messages follow the POST-Redirect-GET pattern: a message is queued on
# request N (stored in a signed cookie by FlashMiddleware), then consumed on
# request N+1 via get_flashed_messages().
# ---------------------------------------------------------------------------

_SECRET = "test-secret-key"


def _make_client(flash_handler, read_handler) -> TestClient:
    """Build a TestClient with two routes:
    POST /flash: queues flash messages
    GET  /read: returns them as JSON
    """
    app = Starlette(
        routes=[
            Route("/flash", flash_handler, methods=["POST"]),
            Route("/read", read_handler, methods=["GET"]),
        ],
        middleware=[Middleware(FlashMiddleware, secret_key=_SECRET)],
    )
    return TestClient(app, raise_server_exceptions=True)


def test_flash_category_stored_and_returned():
    async def do_flash(request: Request):
        flash(request, "saved!", "success")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        msgs = get_flashed_messages(request)
        return JSONResponse(msgs)

    client = _make_client(do_flash, do_read)
    client.post("/flash")
    data = client.get("/read").json()
    assert data == [{"message": "saved!", "category": "success"}]


def test_flash_default_category_is_info():
    async def do_flash(request: Request):
        flash(request, "hello")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        msgs = get_flashed_messages(request)
        return JSONResponse(msgs)

    client = _make_client(do_flash, do_read)
    client.post("/flash")
    data = client.get("/read").json()
    assert data[0]["category"] == "info"


def test_flash_multiple_messages_all_returned():
    async def do_flash(request: Request):
        flash(request, "first", "info")
        flash(request, "second", "warning")
        flash(request, "third", "error")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        msgs = get_flashed_messages(request)
        return JSONResponse([m["message"] for m in msgs])

    client = _make_client(do_flash, do_read)
    client.post("/flash")
    assert client.get("/read").json() == ["first", "second", "third"]


def test_flash_cookie_deleted_after_consumption():
    async def do_flash(request: Request):
        flash(request, "msg")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        get_flashed_messages(request)
        return PlainTextResponse("ok")

    client = _make_client(do_flash, do_read)
    client.post("/flash")
    assert "starlette_admin_flash" in client.cookies

    client.get("/read")  # consumes the cookie
    assert "starlette_admin_flash" not in client.cookies


def test_flash_second_read_on_same_request_returns_empty():
    """Calling get_flashed_messages twice on the same request returns an empty list the second time."""

    async def do_flash(request: Request):
        flash(request, "once")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        first = get_flashed_messages(request)
        second = get_flashed_messages(request)
        return JSONResponse({"first": len(first), "second": len(second)})

    client = _make_client(do_flash, do_read)
    client.post("/flash")
    data = client.get("/read").json()
    assert data["first"] == 1
    assert data["second"] == 0


def test_flash_cookie_has_httponly_flag():
    async def do_flash(request: Request):
        flash(request, "secure")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        return PlainTextResponse("ok")

    client = _make_client(do_flash, do_read)
    resp = client.post("/flash")
    set_cookie = resp.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()


def test_flash_cookie_has_max_age():
    async def do_flash(request: Request):
        flash(request, "ttl")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        return PlainTextResponse("ok")

    client = _make_client(do_flash, do_read)
    resp = client.post("/flash")
    set_cookie = resp.headers.get("set-cookie", "")
    assert "max-age=" in set_cookie.lower()


def test_flash_cookie_has_samesite_lax():
    async def do_flash(request: Request):
        flash(request, "same")
        return PlainTextResponse("ok")

    async def do_read(request: Request):
        return PlainTextResponse("ok")

    client = _make_client(do_flash, do_read)
    resp = client.post("/flash")
    set_cookie = resp.headers.get("set-cookie", "")
    assert "samesite=lax" in set_cookie.lower()


# ── flash() input validation ──────────────────────────────────────────────────


def test_flash_empty_string_raises():
    with pytest.raises(ValueError, match="non-empty string"):
        flash(types.SimpleNamespace(state=types.SimpleNamespace()), "", "info")


def test_flash_non_string_message_raises():
    with pytest.raises(ValueError, match="non-empty string"):
        flash(types.SimpleNamespace(state=types.SimpleNamespace()), 42, "info")  # type: ignore[arg-type]


def test_flash_invalid_category_raises():
    request = types.SimpleNamespace(state=types.SimpleNamespace(admin_flash_pending=[]))
    with pytest.raises(ValueError, match="Invalid flash category"):
        flash(request, "hello", "invalid_category")


# ── get_flashed_messages drains same-request pending queue ───────────────────


def test_get_flashed_messages_drains_pending():
    """Pending messages queued by flash() in the same request are returned by get_flashed_messages."""

    async def do_both(request: Request):
        flash(request, "pending msg", "warning")
        msgs = get_flashed_messages(request)
        return JSONResponse(msgs)

    app = Starlette(
        routes=[Route("/both", do_both, methods=["GET"])],
        middleware=[Middleware(FlashMiddleware, secret_key=_SECRET)],
    )
    client = TestClient(app, raise_server_exceptions=True)
    data = client.get("/both").json()
    assert data == [{"message": "pending msg", "category": "warning"}]
