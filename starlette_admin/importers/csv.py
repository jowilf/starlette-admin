"""CSV importer: parses a UTF-8 encoded ``.csv`` file."""

from __future__ import annotations

import csv
import io
from collections.abc import AsyncGenerator
from typing import Any

from starlette_admin.importers.base import BaseImporter, ImportContext
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


class CsvImporter(BaseImporter):
    extension = "csv"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        _log.debug("CSV parse starting: %d bytes", len(ctx.content))
        # utf-8-sig strips the BOM written by Excel
        text = ctx.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        row_count = 0
        for row in reader:
            row_count += 1
            yield dict(row)
        _log.debug("CSV parse complete: %d row(s) yielded", row_count)
