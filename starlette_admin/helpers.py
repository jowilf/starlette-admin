import decimal
import inspect
import json
import os
import re
from collections.abc import Awaitable, Callable, Collection
from typing import (
    Any,
    TypeVar,
)
from urllib.parse import urlencode, urlparse, urlsplit, urlunsplit

from markupsafe import Markup, escape
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse as _StarletteJSONResponse
from starlette.responses import Response
from starlette_admin.exceptions import FormValidationError
from starlette_admin.logging import get_logger
from starlette_admin.types import RequestAction

_log = get_logger(__name__)

HTTP_422 = (
    status.HTTP_422_UNPROCESSABLE_CONTENT
    if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT")
    else status.HTTP_422_UNPROCESSABLE_ENTITY
)


def field_error_payload(exc: Exception) -> Any:
    """Extracts the error payload carried by a field validation exception.

    `ListField`/`CollectionField` raise `ValueError` with a `dict` (keyed by
    index or sub-field name) as the sole argument so the form can render
    nested errors; plain field validators raise `ValueError` with a plain
    message. Using `exc.args[0]` instead of `str(exc)` preserves the dict
    in the former case while remaining identical to `str(exc)` in the latter.
    """
    return exc.args[0] if exc.args else str(exc)


def safe_redirect_url(next_url: str, request: Request, fallback: str) -> str:
    """Return `next_url` only if it is a safe redirect target, otherwise return `fallback`.

    Accepts relative paths that start with exactly one slash and absolute http(s)
    URLs that match the request origin. Rejects protocol-relative (`//`) and
    backslash-trick (`/\\`) URLs, non-http(s) schemes, and cross-origin absolute
    URLs.
    """
    parsed = urlparse(next_url)
    if parsed.scheme:
        # Deny javascript:, data:, vbscript:, and any other non-http(s) scheme.
        if parsed.scheme not in ("http", "https"):
            return fallback
        base = urlparse(str(request.base_url))
        if parsed.scheme == base.scheme and parsed.netloc == base.netloc:
            return next_url
        return fallback
    # Relative URL: must start with exactly one /; reject // and /\
    if not next_url.startswith("/"):
        return fallback
    if len(next_url) > 1 and next_url[1] in ("/", "\\"):
        return fallback
    return next_url


def prettify_class_name(name: str) -> str:
    return re.sub(r"(?<=.)([A-Z])", r" \1", name)


def slugify_class_name(name: str) -> str:
    return "".join(["-" + c.lower() if c.isupper() else c for c in name]).lstrip("-")


def is_empty_file(file: Any) -> bool:
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(pos)
    return size == 0


def is_empty_value(value: Any) -> bool:
    """Whether a parsed form value counts as "not provided" for the
    `required` check. `False` and `0` are real values, not empty ones."""
    return (
        value is None
        or value == ""
        or (isinstance(value, (list, tuple, dict)) and len(value) == 0)
    )


def to_form_entry(value: Any) -> str:
    """Stringify a serialized value the same way a submitted form field
    would, staying `parse_form_data`-friendly for every field type."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    return json.dumps(value)


def get_file_icon(mime_type: str) -> str:
    mapping = {
        "image": "fa-file-image",
        "audio": "fa-file-audio",
        "video": "fa-file-video",
        "application/pdf": "fa-file-pdf",
        "application/msword": "fa-file-word",
        "application/vnd.ms-word": "fa-file-word",
        "application/vnd.oasis.opendocument.text": "fa-file-word",
        "application/vnd.openxmlformatsfficedocument.wordprocessingml": "fa-file-word",
        "application/vnd.ms-excel": "fa-file-excel",
        "application/vnd.openxmlformatsfficedocument.spreadsheetml": "fa-file-excel",
        "application/vnd.oasis.opendocument.spreadsheet": "fa-file-excel",
        "application/vnd.ms-powerpoint": "fa-file-powerpoint",
        "application/vnd.openxmlformatsfficedocument.presentationml": (
            "fa-file-powerpoint"
        ),
        "application/vnd.oasis.opendocument.presentation": "fa-file-powerpoint",
        "text/plain": "fa-file-text",
        "text/html": "fa-file-code",
        "text/csv": "fa-file-csv",
        "application/json": "fa-file-code",
        "application/gzip": "fa-file-archive",
        "application/zip": "fa-file-archive",
    }
    icon = "fa-file"
    if mime_type:
        for key, _ in mapping.items():
            if key in mime_type:
                icon = mapping[key]
                break
    return f"fa-solid fa-fw {icon}"


def html_params(kwargs: dict[str, Any]) -> str:
    """Convert a dictionary of HTML attribute name-value pairs into an HTML attribute string."""
    params = []
    for k, v in kwargs.items():
        if v is None or v is False:
            continue
        if v is True:
            params.append(k)
        else:
            params.append('{}="{}"'.format(str(k).replace("_", "-"), escape(v)))
    return " ".join(params)


def _path_and_query(url: Any) -> str:
    """Return `url`'s path and query string, dropping scheme and host."""
    return url.path + (f"?{url.query}" if url.query else "")


def _carry_origin(request: Request) -> str | None:
    """Return the `_origin` to carry to the next page, if any.

    Propagates an `_origin` already on the current request (so a detail page
    reached from a filtered list keeps pointing back to that list). If none
    is set yet, synthesizes one from the current request URL, but only when
    the current request is itself a page a user could sensibly return to
    (a list or detail page) -- not an internal API call such as a relation
    lookup, which has no meaningful "back" destination.

    `request.state.origin_override`, when set, wins over both: it lets an
    endpoint that borrows the `LIST`/`DETAIL` action for rendering purposes
    (e.g. the inline-edit-row fragment) supply the real page URL instead of
    its own API URL.
    """
    override = getattr(request.state, "origin_override", None)
    if override:
        return override
    action = getattr(request.state, "action", None)
    if action in (RequestAction.LIST, RequestAction.DETAIL):
        return _path_and_query(request.url)
    origin = request.query_params.get("_origin")
    if origin:
        return origin
    return None


def detail_url(request: Request, key: str, pk: Any) -> str:
    """Build a detail-page URL for the given key and pk using ?pk= query param.

    Carries forward `_origin` so the page can be returned to later.
    """
    route_name = request.app.state.ROUTE_NAME
    url = request.url_for(route_name + ":detail", key=key).include_query_params(
        pk=str(pk)
    )
    origin = _carry_origin(request)
    if origin:
        url = url.include_query_params(_origin=origin)
    return str(url)


def edit_url(request: Request, key: str, pk: Any) -> str:
    """Build an edit-page URL for the given key and pk using ?pk= query param.

    Carries forward `_origin` so a successful save can return to it.
    """
    route_name = request.app.state.ROUTE_NAME
    url = request.url_for(route_name + ":edit", key=key).include_query_params(
        pk=str(pk)
    )
    origin = _carry_origin(request)
    if origin:
        url = url.include_query_params(_origin=origin)
    return str(url)


def create_url(request: Request, key: str) -> str:
    """Build a create-page URL for the given key.

    Carries forward `_origin` so a successful save can return to it.
    """
    route_name = request.app.state.ROUTE_NAME
    url = request.url_for(route_name + ":create", key=key)
    origin = _carry_origin(request)
    if origin:
        url = url.include_query_params(_origin=origin)
    return str(url)


def back_url(request: Request, key: str) -> str:
    """Build the URL to return to when cancelling or completing an operation.

    Honors a safe `_origin` query param on the current request when present,
    otherwise falls back to the plain list URL for the given key.
    """
    route_name = request.app.state.ROUTE_NAME
    fallback = str(request.url_for(route_name + ":list", key=key))
    origin = request.query_params.get("_origin")
    return safe_redirect_url(origin, request, fallback) if origin else fallback


def view_list_url(request: Request, key: str) -> str:
    """Build a plain list-page URL for the given key with no query params."""
    route_name = request.app.state.ROUTE_NAME
    return str(request.url_for(route_name + ":list", key=key))


def breadcrumb_list_url(request: Request, key: str) -> str:
    """Build the URL for the view-level crumb of a breadcrumb trail.

    Unlike [`back_url`][starlette_admin.helpers.back_url], this never points at
    another view's page: a breadcrumb labelled with `key`'s menu label must link
    to `key`'s own list page. It reuses `_origin` only when that origin *is*
    `key`'s list page, so a detail page reached from a sorted/filtered list
    still links back to that exact list state; when the origin belongs to a
    different view (e.g. a related object's detail page reached from another
    view's list), it falls back to the plain list URL.
    """
    fallback = view_list_url(request, key)
    origin = request.query_params.get("_origin")
    if not origin:
        return fallback
    candidate = safe_redirect_url(origin, request, fallback)
    route_name = request.app.state.ROUTE_NAME
    list_path = request.url_for(route_name + ":list", key=key).path
    return candidate if urlparse(candidate).path == list_path else fallback


def list_page_origin(request: Request, key: str) -> str:
    """Build the real list-page path for `key`, carrying the current request's
    query params (sort, filters, page, ...) but dropping `pk`.

    Used by endpoints that render list-page fragments -- like the
    inline-edit-row swap -- under their own URL, so `request.url` doesn't leak
    that internal API URL as the row's `_origin` (see `_carry_origin`).
    """
    items = [(k, v) for k, v in request.query_params.multi_items() if k != "pk"]
    qs = urlencode(items)
    route_name = request.app.state.ROUTE_NAME
    path = request.url_for(route_name + ":list", key=key).path
    return f"{path}?{qs}" if qs else path


def index_url(request: Request) -> str:
    """Build the admin's index-page URL."""
    route_name = request.app.state.ROUTE_NAME
    return str(request.url_for(route_name + ":index"))


def import_url(request: Request, key: str) -> str:
    """Build the import POST URL for the given view key."""
    route_name = request.app.state.ROUTE_NAME
    return str(request.url_for(route_name + ":import", key=key))


def static_url(request: Request, path: str, v: Any = None) -> str:
    """Build a URL for a static asset served by the admin's static mount."""
    route_name = request.app.state.ROUTE_NAME
    url = request.url_for(route_name + ":static", path=path)
    if v is not None:
        url = url.include_query_params(v=v)
    return str(url)


def list_url(request: Request, **overrides: Any) -> str:
    """Build a list-page URL that keeps the current query params and applies
    `overrides` on top of them.

    Passing `None` for a key drops it from the resulting query string. This is
    used to reset `page` back to its default whenever sort, search, or page size
    changes. List values are expanded into repeated params, e.g.
    ``sort=["name__asc", "date__desc"]`` becomes ``?sort=name__asc&sort=date__desc``.

    Exposed as the `list_url` Jinja2 global so list templates can build
    sort/pagination/search links as plain `<a href="...">` / `<form method="GET">`
    navigations, with no JavaScript fetch calls involved.
    """
    override_keys = set(overrides.keys())
    base_items = [
        (k, v) for k, v in request.query_params.multi_items() if k not in override_keys
    ]
    extra_items: list[tuple[str, str]] = []
    for k, v in overrides.items():
        if v is None:
            pass
        elif isinstance(v, list):
            for item in v:
                extra_items.append((k, str(item)))
        else:
            extra_items.append((k, str(v)))
    all_items = base_items + extra_items
    qs = urlencode(all_items)
    parts = urlsplit(str(request.url))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, qs, ""))


def pydantic_error_to_form_validation_errors(
    exc: Any, key_map: dict[str, str] | None = None
) -> FormValidationError:
    """Convert a Pydantic `ValidationError` into a `FormValidationError`.

    Each error's `loc` tuple becomes a nested path of dict keys, so an error at
    `loc=("address", "zip_code")` ends up as `errors["address"]["zip_code"]`.

    `key_map` renames the first path segment (e.g. a model column that has no
    matching form field) to the name of the form field the error should be
    attached to (e.g. `{"company_id": "company"}`).
    """
    from pydantic import ValidationError

    assert isinstance(exc, ValidationError)
    errors: dict[str | int, Any] = {}
    for pydantic_error in exc.errors():
        loc: tuple[int | str, ...] = pydantic_error["loc"]
        if key_map and loc and isinstance(loc[0], str) and loc[0] in key_map:
            loc = (key_map[loc[0]], *loc[1:])
        _d = errors
        for i in range(len(loc)):
            if i == len(loc) - 1:
                _d[loc[i]] = pydantic_error["msg"]
            elif loc[i] not in _d:
                _d[loc[i]] = {}
            _d = _d[loc[i]]
    return FormValidationError(errors)


def wrap_endpoint_with_kwargs(
    endpoint: Callable[..., Awaitable[Response]], **kwargs: Any
) -> Callable[[Request], Awaitable[Response]]:
    """Wrap `endpoint` so it is called with `kwargs` merged into every request."""

    async def wrapper(request: Request) -> Response:
        return await endpoint(request=request, **kwargs)

    return wrapper


async def maybe_async(value: Any) -> Any:
    """Await `value` if it is awaitable, otherwise return it unchanged.

    Lets a call site accept a sync-or-async callable's result without an
    `inspect.isawaitable` check of its own.
    """
    return await value if inspect.isawaitable(value) else value


def on_commit(request: Request, callback: Callable[[], Any]) -> None:
    """Register a callback to run after the request's transaction is committed.

    Callbacks run in registration order once the session middleware has
    successfully committed the request session (see ``DBSessionMiddleware``).
    They never run when the request fails or is rolled back. Sync and async
    callables are both accepted.

    By the time a callback runs, the data is durably committed, so callbacks
    must not write through ``request.state.session``: anything flushed there
    starts a new transaction that is discarded when the session closes. Use
    external I/O or a self-managed session instead.

    Args:
        request: The request being processed.
        callback: Zero-argument callable, optionally returning an awaitable.
    """
    callbacks = getattr(request.state, "on_commit_callbacks", None)
    if callbacks is None:
        callbacks = []
        request.state.on_commit_callbacks = callbacks
    callbacks.append(callback)


async def run_on_commit_callbacks(request: Request) -> None:
    """Run the callbacks registered with [on_commit][starlette_admin.helpers.on_commit].

    Called by the session middleware after a successful commit. Callbacks are
    not wrapped in error handling: if one raises, the exception propagates
    and aborts the response even though the data is already committed.
    """
    for callback in getattr(request.state, "on_commit_callbacks", []):
        await maybe_async(callback())
        _log.debug(
            "on_commit callback %r completed for %s %s",
            callback,
            request.method,
            request.url,
        )


T = TypeVar("T")


def not_none(value: T | None) -> T:
    """Return `value` unchanged, raising if it is `None`.

    Args:
        value: The value to check.

    Returns:
        The value, guaranteed not to be `None`.

    Raises:
        ValueError: If `value` is `None`.
    """
    if value is not None:
        return value
    raise ValueError("Value can not be None")  # pragma: no cover


_URL_ALLOWED_SCHEMES = frozenset(
    {"http", "https", "mailto", "tel", "ftp", "ftps", "sms"}
)


def safe_url(url: Any, allowed_schemes: Collection[str] = _URL_ALLOWED_SCHEMES) -> str:
    """Return `url` only if its scheme is in `allowed_schemes` (http, https, mailto,
    tel, ftp, ftps, sms by default).

    Relative URLs (no scheme) pass through unchanged. Any other scheme
    (javascript:, data:, vbscript:, etc.) is replaced with an empty string.
    """
    try:
        scheme = urlparse(str(url)).scheme.lower()
    except Exception:
        return ""
    if not scheme or scheme in allowed_schemes:
        return str(url)
    return ""


_TINYMCE_ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        "a",
        "abbr",
        "b",
        "blockquote",
        "br",
        "caption",
        "cite",
        "code",
        "col",
        "colgroup",
        "dd",
        "del",
        "div",
        "dl",
        "dt",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "ins",
        "kbd",
        "li",
        "ol",
        "p",
        "pre",
        "q",
        "s",
        "samp",
        "small",
        "span",
        "strike",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
        "var",
    }
)

_TINYMCE_ALLOWED_ATTRS: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "width", "height"},
    "td": {"align", "valign", "colspan", "rowspan"},
    "th": {"align", "valign", "colspan", "rowspan", "scope"},
    "col": {"span"},
    "colgroup": {"span"},
    "blockquote": {"cite"},
    "*": {"class"},  # "style" removed: allows CSS injection via url()/expression()
}


def sanitize_html(html: Any) -> Markup:
    """Sanitize arbitrary HTML and return a safe Markup string.

    Uses nh3 (Rust ammonia) to strip disallowed tags/attributes while keeping
    the rich-text structure produced by TinyMCE. URL attributes (href, src) are
    restricted to http, https, mailto, tel, ftp, ftps, and sms schemes.
    ``data:`` URIs are intentionally excluded: nh3 strips any href or src
    carrying a ``data:`` scheme, preventing data-URI-based XSS vectors.
    """
    try:
        import nh3
    except ImportError:  # pragma: no cover
        raise ImportError(
            "nh3 is required for TinyMCEEditorField. "
            'Install it with: pip install "starlette-admin[tinymce]"'
        ) from None
    cleaned = nh3.clean(
        str(html),
        tags=_TINYMCE_ALLOWED_TAGS,
        attributes=_TINYMCE_ALLOWED_ATTRS,
        url_schemes=_URL_ALLOWED_SCHEMES,
    )
    return Markup(cleaned)


def json_dumps(data: Any, **kwargs: Any) -> str:
    """``json.dumps`` that coerces non-serializable values, including lazy i18n
    proxies from ``lazy_gettext``, to their string representation via
    ``default=str``.
    """
    return json.dumps(data, default=str, **kwargs)


class JSONResponse(_StarletteJSONResponse):
    """``JSONResponse`` that automatically coerces lazy i18n proxies (and any
    other non-serializable value) to ``str`` via :func:`json_dumps`.
    """

    def render(self, content: Any) -> bytes:
        return json_dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


_JSON_HTML_ESCAPES = str.maketrans(
    {
        "&": "\\u0026",
        "<": "\\u003c",
        ">": "\\u003e",
        "'": "\\u0027",
    }
)


def html_safe_json(data: Any) -> Markup:
    """JSON-encode *data* and escape characters that break ``<script>`` blocks.

    Python's ``json.dumps`` does not escape ``<``, ``>``, ``&``, or ``'``, so a
    value containing ``</script>`` injected into an HTML page via ``| tojson |
    safe`` would close the enclosing ``<script>`` tag and allow reflected XSS.

    The four dangerous code-points are replaced with their ``\\uXXXX``
    equivalents, which are semantically identical in JSON but harmless in HTML.
    The result is wrapped in :class:`~markupsafe.Markup` so Jinja2 treats it as
    already-escaped; ``| safe`` in templates becomes a harmless no-op.
    """
    return Markup(json_dumps(data).translate(_JSON_HTML_ESCAPES))


def _as_url_callable(
    value: str | Callable[[Request], str | None] | None,
) -> Callable[[Request], str | None]:
    """Wrap *value* so it is always callable as ``url(request) -> str | None``.

    A plain string or ``None`` is wrapped in a lambda that ignores the request
    and returns the value directly.  An existing callable is returned unchanged.
    """
    if value is None or isinstance(value, str):
        return lambda _request: value
    return value
