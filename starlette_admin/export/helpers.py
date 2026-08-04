"""Stand-alone helper functions shared by the export package."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any

from starlette.requests import Request
from starlette_admin.exceptions import ExportError

if TYPE_CHECKING:
    from starlette_admin.export.base import ExportConfig


def is_allowed_url(url: str, request: Request) -> bool:
    """Return ``True`` if *url* is safe to fetch without a custom validator.

    Allowed origins:
    * Same origin as the admin (URL starts with ``request.base_url``).
    """
    base = str(request.base_url).rstrip("/")
    return url.startswith(base + "/") or url.rstrip("/") == base


def resolve_download_url(
    url: str,
    config: ExportConfig,
    request: Request,
) -> str | None:
    """Return the URL to fetch, or ``None`` if it should be blocked.

    Resolution order:
    1. If ``config.safe_download_url`` is set, delegate entirely to it.
    2. If ``config.restrict_url_download`` is ``True``, apply the built-in
       allow-list (same origin + AWS S3).
    3. Otherwise allow the URL as-is.
    """
    if config.safe_download_url is not None:
        return config.safe_download_url(url, request)
    if config.restrict_url_download:
        return url if is_allowed_url(url, request) else None
    return url


def is_file_dict(value: Any) -> bool:
    """Return ``True`` if *value* looks like a ``FileInfo.to_dict()`` result."""
    return (
        isinstance(value, dict)
        and bool(value.get("storage"))
        and bool(value.get("key"))
    )


def is_url_file_dict(value: Any) -> bool:
    """Return ``True`` if *value* is a URL-only file reference with no storage backend."""
    return (
        isinstance(value, dict) and bool(value.get("url")) and not value.get("storage")
    )


def safe_cd_filename(name: str) -> str:
    """Sanitize a string for use in a Content-Disposition filename= parameter.

    Strips ``"``, ``\\``, CR and LF characters that would break the header or
    allow header injection.
    """
    return re.sub(r'["\\\r\n]', "_", name)


def safe_zip_name(name: str, field: str = "name") -> str:
    """Sanitize a single ZIP path component via os.path.basename and reject '..'."""
    safe = os.path.basename(name.replace("\\", "/"))
    if safe == "..":
        raise ExportError(f"Unsafe ZIP {field}: {name!r}")
    return safe or "_"


def safe_zip_key(key: str) -> str:
    """Sanitize a slash-delimited storage key; reject '..' path segments."""
    normalized = key.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise ExportError(f"Unsafe ZIP key contains '..': {key!r}")
    return normalized


_FORMULA_TRIGGER_CHARS = frozenset("=+-@")
_LEADING_WHITESPACE = " \t\r\n\x0b\x0c"


def escape_formula(value: str) -> str:
    """Prefix *value* with a single quote if it is or starts with a formula
    trigger character (``=``, ``+``, ``-``, ``@``, tab, or CR).

    Spreadsheet applications (Excel, LibreOffice, Google Sheets) treat cells
    starting with these characters as formulas, and trim leading whitespace
    before checking, so ``" =cmd|'/c calc'!A1"`` is still evaluated. Without
    escaping, such attacker-controlled strings can execute arbitrary commands
    when the file is opened.
    """
    if not value:
        return value
    if value[0] in "\t\r":
        return "'" + value
    if value.lstrip(_LEADING_WHITESPACE)[:1] in _FORMULA_TRIGGER_CHARS:
        return "'" + value
    return value
