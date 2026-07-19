from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from starlette_admin.cookies import SignedCookie
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


_FLASH_COOKIE = "starlette_admin_flash"
_FLASH_SALT = "starlette-admin-flash"

VALID_FLASH_CATEGORIES = {"success", "warning", "error", "info"}


class FlashMiddleware(BaseHTTPMiddleware):
    """Reads, clears, and writes signed flash-message cookies.

    Flash messages are stored in a dedicated signed cookie
    (``starlette_admin_flash``) so the framework does not depend on
    Starlette's ``SessionMiddleware`` for flash messaging. The cookie value
    is a JSON list signed with itsdangerous.
    """

    def __init__(self, app: ASGIApp, secret_key: str) -> None:
        super().__init__(app)
        self._cookie = SignedCookie(
            secret_key, salt=_FLASH_SALT, timed=True, max_age=300
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.admin_flash_cookie = self._cookie
        request.state.admin_flash_pending = []
        request.state.admin_flash_consumed = False

        response = await call_next(request)

        pending = getattr(request.state, "admin_flash_pending", [])
        consumed = getattr(request.state, "admin_flash_consumed", False)
        secure = request.url.scheme == "https"

        if pending:
            response.set_cookie(
                _FLASH_COOKIE,
                self._cookie.dumps(pending),
                httponly=True,
                samesite="lax",
                max_age=300,
                secure=secure,
            )
        elif consumed:
            response.delete_cookie(_FLASH_COOKIE)

        return response


def flash(request: Request, message: str, category: str = "info") -> None:
    """Queue a flash message to be rendered on the next page load.

    Args:
        request: The current request (FlashMiddleware must be active).
        message: Human-readable message text.
        category: One of ``"success"``, ``"warning"``, ``"error"``, ``"info"``.

    Raises:
        RuntimeError: If FlashMiddleware has not been installed.
        ValueError: If ``category`` is not one of the allowed values.
    """
    if not isinstance(message, str) or not message:
        raise ValueError("Flash message must be a non-empty string.")
    if category not in VALID_FLASH_CATEGORIES:
        raise ValueError(
            f"Invalid flash category {category!r}. "
            f"Must be one of: {', '.join(sorted(VALID_FLASH_CATEGORIES))}."
        )
    pending = getattr(request.state, "admin_flash_pending", None)
    if pending is None:
        raise RuntimeError(
            "FlashMiddleware is required to use flash(). "
            "It is added automatically by BaseAdmin."
        )
    pending.append({"message": message, "category": category})
    _log.debug("[%s] %s", category, message)


def get_flashed_messages(request: Request) -> list[dict]:
    """Pop and return all pending flash messages from the signed cookie.

    Consuming is destructive; subsequent calls on the same request return ``[]``.

    Raises:
        RuntimeError: If FlashMiddleware has not been installed.
    """
    if getattr(request.state, "admin_flash_consumed", False):
        return []

    cookie = getattr(request.state, "admin_flash_cookie", None)
    if cookie is None:
        raise RuntimeError(
            "FlashMiddleware is required to use get_flashed_messages(). "
            "It is added automatically by BaseAdmin."
        )

    raw = request.cookies.get(_FLASH_COOKIE)
    messages: list[dict] = []
    if raw:
        messages = cookie.loads(raw) or []

    # Also drain messages queued in the current request (e.g., validation errors
    # that flash() before rendering the same response rather than redirecting).
    pending = getattr(request.state, "admin_flash_pending", [])
    if pending:
        messages.extend(pending)
        request.state.admin_flash_pending = []

    request.state.admin_flash_consumed = True
    _log.debug("get_flashed_messages: returning %d message(s)", len(messages))
    return messages
