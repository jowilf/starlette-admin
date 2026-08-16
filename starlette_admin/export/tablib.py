"""Generic exporter for every tablib-backed format (xlsx, xls, ods, yaml, dbf, html, latex, jira, rst)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette_admin.export.base import BaseExporter
from starlette_admin.export.helpers import escape_formula

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField

# Formats opened directly in a spreadsheet application, where a leading
# =/+/-/@ is interpreted as a formula. yaml/json/html/latex/dbf are not, so
# escaping there would corrupt the data instead of protecting it.
_SPREADSHEET_FORMATS = frozenset({"xlsx", "xls", "ods"})

_CONTENT_TYPES = {
    "yaml": "application/x-yaml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "dbf": "application/x-dbf",
    "html": "text/html",
    "latex": "application/x-latex",
    "jira": "text/plain",
    "rst": "text/x-rst",
}

# pip extra required for each format; formats needing only bare tablib fall
# back to "tablib" via .get() below.
_REQUIRES = {
    "yaml": "tablib[yaml]",
    "xlsx": "tablib[xlsx]",
    "xls": "tablib[xls]",
    "ods": "tablib[ods]",
}


class TablibExporter(BaseExporter):
    """Exports through ``tablib.Dataset`` for any format tablib supports."""

    def __init__(
        self, format: str, escape_formulas: bool = False, **export_kwargs: Any
    ) -> None:
        """
        Args:
            format: A tablib export format name (``"xlsx"``, ``"yaml"``, ...).
            escape_formulas: When ``True`` and *format* is a spreadsheet
                format (xlsx, xls, ods), cell values starting with ``=``,
                ``+``, ``-`` or ``@`` are prefixed with a single quote to
                prevent formula injection. Disabled by default; enable it
                when exported data can contain user-supplied strings.
            export_kwargs: Forwarded to ``tablib.Dataset.export()``.
        """
        self.format = format
        self.extension = format
        self.content_type = _CONTENT_TYPES.get(format, "application/octet-stream")
        self.requires = _REQUIRES.get(format, "tablib")
        self.escape_formulas = escape_formulas
        self.export_kwargs = export_kwargs

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        try:
            import tablib
        except ImportError as exc:
            raise ImportError(
                f"The 'tablib' package is required for {self.format!r} export. "
                f"Install it with: pip install {self.requires}"
            ) from exc

        dataset = tablib.Dataset(headers=[f.label or f.name for f in fields])
        should_escape_formulas = (
            self.escape_formulas and self.format in _SPREADSHEET_FORMATS
        )
        for row in rows:
            values = [row.get(f.name, "") for f in fields]
            if should_escape_formulas:
                values = [
                    escape_formula(v) if isinstance(v, str) else v for v in values
                ]
            dataset.append(values)

        output = dataset.export(self.format, **self.export_kwargs)
        return output.encode("utf-8") if isinstance(output, str) else output
