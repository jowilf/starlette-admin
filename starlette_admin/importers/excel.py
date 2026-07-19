"""Excel importer: parses an ``.xlsx`` workbook via *openpyxl*."""

import io
from collections.abc import AsyncGenerator
from typing import Any

from starlette_admin.importers.base import BaseImporter, ImportContext
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


class ExcelImporter(BaseImporter):
    extension = "xlsx"
    format_key = "excel"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        _log.debug("Excel parse starting: %d bytes", len(ctx.content))
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "The 'openpyxl' package is required for Excel import. "
                "Install it with: pip install starlette-admin[excel]"
            ) from exc

        wb = openpyxl.load_workbook(
            io.BytesIO(ctx.content), read_only=True, data_only=True
        )
        ws = wb.active
        if ws is None:
            _log.warning("Excel workbook has no active sheet; no rows to import")
            return
        rows = ws.iter_rows(values_only=True)
        try:
            raw_headers = next(rows)
        except StopIteration:  # pragma: no cover
            _log.warning("Excel sheet is empty; no rows to import")
            return
        headers = [str(h) if h is not None else "" for h in raw_headers]
        _log.debug("Excel headers: %s", headers)
        row_count = 0
        for row in rows:
            row_count += 1
            yield {
                headers[i]: (str(v) if v is not None else "") for i, v in enumerate(row)
            }
        _log.debug("Excel parse complete: %d row(s) yielded", row_count)
