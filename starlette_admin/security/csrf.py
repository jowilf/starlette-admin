import hmac
import secrets

from itsdangerous import BadSignature, URLSafeSerializer
from markupsafe import Markup, escape
from starlette.datastructures import FormData
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.types import ASGIApp
from starlette_admin.logging import get_logger

_log = get_logger(__name__)

_CSRF_SALT = "starlette-admin-csrf"


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection with signed cookies.

    Sets a signed ``starlette_admin_csrftoken`` cookie on safe responses;
    validates it on mutating requests by comparing the cookie value against
    either the ``X-CSRFToken`` request header (AJAX) or the ``csrftoken``
    hidden form field. The raw token value is signed with itsdangerous so
    clients cannot forge or tamper with it.

    The signed token is stored on ``request.state.csrf_token`` so templates
    can render it via ``{{ csrf_input(request) }}`` and JavaScript can read
    the same signed value from the cookie for AJAX requests.
    """

    cookie_name = "starlette_admin_csrftoken"
    header_name = "X-CSRFToken"
    field_name = "csrftoken"
    safe_methods = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

    def __init__(self, app: ASGIApp, secret_key: str) -> None:
        super().__init__(app)
        self._signer = URLSafeSerializer(secret_key, salt=_CSRF_SALT)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        cookie_signed = request.cookies.get(self.cookie_name)
        cookie_token: str | None = None
        need_set_cookie = False

        if cookie_signed:
            try:
                cookie_token = self._signer.loads(cookie_signed)
            except BadSignature:
                need_set_cookie = True
        else:
            need_set_cookie = True

        if need_set_cookie:
            cookie_token = secrets.token_hex(32)
            _log.debug(
                "CSRFMiddleware: issuing new csrf cookie for %s %s",
                request.method,
                request.url.path,
            )

        # Expose the signed token to templates / JS via request.state.
        request.state.csrf_token = self._signer.dumps(cookie_token)

        if request.method not in self.safe_methods:
            submitted_signed = await self._get_submitted_token(request)
            if not cookie_token or not submitted_signed:
                _log.warning(
                    "CSRFMiddleware: rejecting %s %s: token missing",
                    request.method,
                    request.url.path,
                )
                return PlainTextResponse("CSRF token missing", status_code=403)
            try:
                submitted_token = self._signer.loads(submitted_signed)
            except BadSignature:
                _log.warning(
                    "CSRFMiddleware: rejecting %s %s: signature invalid",
                    request.method,
                    request.url.path,
                )
                return PlainTextResponse("CSRF token invalid", status_code=403)
            if not hmac.compare_digest(submitted_token, cookie_token):
                _log.warning(
                    "CSRFMiddleware: rejecting %s %s: token mismatch",
                    request.method,
                    request.url.path,
                )
                return PlainTextResponse("CSRF token invalid", status_code=403)

            _log.debug(
                "CSRFMiddleware: token valid for %s %s",
                request.method,
                request.url.path,
            )

        response = await call_next(request)

        if need_set_cookie:
            response.set_cookie(
                self.cookie_name,
                self._signer.dumps(cookie_token),
                httponly=False,  # JS must read it to send X-CSRFToken header
                samesite="lax",
                secure=request.url.scheme == "https",
            )
            _log.debug(
                "CSRFMiddleware: set csrf cookie on response for %s %s",
                request.method,
                request.url.path,
            )

        return response

    async def _get_submitted_token(self, request: Request) -> str | None:
        # AJAX requests send the token via a custom header
        token = request.headers.get(self.header_name)
        if token is not None:
            return token

        # Regular form POSTs include the token as a hidden field
        content_type = request.headers.get("Content-Type", "")
        if (
            "multipart/form-data" in content_type
            or "application/x-www-form-urlencoded" in content_type
        ):
            # body() is called first so BaseHTTPMiddleware's _CachedRequest
            # buffers it; the inner app re-reads the same bytes fresh.
            await request.body()
            form: FormData = await request.form()
            return str(form.get(self.field_name) or "")

        return None


def csrf_input(request: Request) -> Markup:
    """Return an HTML hidden input carrying the signed CSRF token."""
    token = getattr(request.state, "csrf_token", "")
    field_name = CSRFMiddleware.field_name
    return Markup(
        f'<input type="hidden" name="{escape(field_name)}" value="{escape(token)}">'
    )
