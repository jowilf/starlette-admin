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

    def __init__(self, escape_formulas: bool = False, **fmtparams: Any) -> None:
        """
        Args:
            escape_formulas: When ``True``, cell values starting with ``=``,
                ``+``, ``-`` or ``@`` are prefixed with a single quote to
                prevent formula injection when the CSV is opened in a
                spreadsheet application. Disabled by default; enable it when
                exported data can contain user-supplied strings.
            fmtparams: Forwarded to ``csv.writer`` (``delimiter``,
                ``quotechar``, ``quoting``, ``lineterminator``,
                ``escapechar``, ``doublequote``, ...).
        """
        self.escape_formulas = escape_formulas
        self.fmtparams = fmtparams

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output, **self.fmtparams)
        writer.writerow([f.label or f.name for f in fields])
        for row in rows:
            values = [row.get(f.name, "") for f in fields]
            if self.escape_formulas:
                values = [
                    escape_formula(v) if isinstance(v, str) else v for v in values
                ]
            writer.writerow(values)
        return output.getvalue().encode("utf-8")


class TsvExporter(CsvExporter):
    content_type = "text/tab-separated-values"
    extension = "tsv"

    def __init__(self, escape_formulas: bool = False, **fmtparams: Any) -> None:
        """
        Args:
            escape_formulas: See :class:`CsvExporter`.
            fmtparams: Forwarded to ``csv.writer``. ``delimiter`` defaults to
                a tab and may be overridden.
        """
        fmtparams.setdefault("delimiter", "\t")
        super().__init__(escape_formulas=escape_formulas, **fmtparams)
