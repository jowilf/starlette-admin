"""Excel exporter: produces an ``.xlsx`` workbook via *openpyxl*."""

from __future__ import annotations

import io
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any

from starlette_admin.export.base import BaseExporter
from starlette_admin.export.helpers import escape_formula

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField

_EXCEL_NATIVE = (str, int, float, bool, datetime, date, time, timedelta, type(None))


def _to_cell(value: Any, escape_formulas: bool = False) -> Any:
    if isinstance(value, _EXCEL_NATIVE):
        if escape_formulas and isinstance(value, str):
            return escape_formula(value)
        return value
    if isinstance(value, (list, tuple)):
        joined = ", ".join(str(v) for v in value)
        return escape_formula(joined) if escape_formulas else joined
    text = str(value)
    return escape_formula(text) if escape_formulas else text


class ExcelExporter(BaseExporter):
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    extension = "xlsx"
    format_key = "excel"

    def __init__(self, escape_formulas: bool = True) -> None:
        """
        Args:
            escape_formulas: When ``True`` (the default), cell values starting
                with ``=``, ``+``, ``-`` or ``@`` are prefixed with a single
                quote to prevent formula injection when the workbook is
                opened in a spreadsheet application.
        """
        self.escape_formulas = escape_formulas

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "The 'openpyxl' package is required for Excel export. "
                "Install it with: pip install starlette-admin[excel]"
            ) from exc

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append([f.label or f.name for f in fields])
        for row in rows:
            ws.append([_to_cell(row.get(f.name), self.escape_formulas) for f in fields])

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
