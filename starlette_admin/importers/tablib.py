"""Generic importer for every tablib-backed format (xlsx, xls, ods, yaml, dbf, html)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from starlette_admin.importers.base import BaseImporter, ImportContext
from starlette_admin.logging import get_logger

_log = get_logger(__name__)

# pip extra required for each format; formats needing only bare tablib fall
# back to "tablib" via .get() below.
_REQUIRES = {
    "yaml": "tablib[yaml]",
    "xlsx": "tablib[xlsx]",
    "xls": "tablib[xls]",
    "ods": "tablib[ods]",
}

# tablib's HTML import_set() feeds the stream straight into stdlib
# HTMLParser, which requires str and raises TypeError on bytes. Every other
# supported format accepts raw bytes.
_TEXT_FORMATS = frozenset({"html"})


class TablibImporter(BaseImporter):
    """Parses through ``tablib.Dataset`` for any format tablib supports."""

    def __init__(self, format: str, **import_kwargs: Any) -> None:
        """
        Args:
            format: A tablib import format name (``"xlsx"``, ``"yaml"``, ...).
            import_kwargs: Forwarded to ``tablib.Dataset.load()``.
        """
        self.format = format
        self.extension = format
        self.requires = _REQUIRES.get(format, "tablib")
        self.import_kwargs = import_kwargs

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any]]:
        try:
            import tablib
        except ImportError as exc:
            raise ImportError(
                f"The 'tablib' package is required for {self.format!r} import. "
                f"Install it with: pip install {self.requires}"
            ) from exc

        _log.debug("%s parse starting: %d bytes", self.format, len(ctx.content))
        content: bytes | str = ctx.content
        if self.format in _TEXT_FORMATS:
            content = ctx.content.decode("utf-8")
        dataset = tablib.Dataset()
        dataset.load(content, format=self.format, **self.import_kwargs)
        row_count = 0
        for row in dataset:
            row_count += 1
            yield dict(zip(dataset.headers, row))
        _log.debug("%s parse complete: %d row(s) yielded", self.format, row_count)
