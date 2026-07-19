"""CSV exporter: produces a UTF-8 encoded ``.csv`` file."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any

from starlette_admin.export.base import BaseExporter
from starlette_admin.export.helpers import escape_formula

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField


class CsvExporter(BaseExporter):
    content_type = "text/csv"
    extension = "csv"

    def __init__(self, escape_formulas: bool = True) -> None:
        """
        Args:
            escape_formulas: When ``True`` (the default), cell values starting
                with ``=``, ``+``, ``-`` or ``@`` are prefixed with a single
                quote to prevent formula injection when the CSV is opened in
                a spreadsheet application.
        """
        self.escape_formulas = escape_formulas

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([f.label or f.name for f in fields])
        for row in rows:
            values = [row.get(f.name, "") for f in fields]
            if self.escape_formulas:
                values = [
                    escape_formula(v) if isinstance(v, str) else v for v in values
                ]
            writer.writerow(values)
        return output.getvalue().encode("utf-8")
