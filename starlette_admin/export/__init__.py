"""Export format registry: maps a format string to its exporter instance.

Every non-core format goes through `tablib`, an optional dependency. csv,
tsv and json are implemented in core with the standard library, so the
default configuration (`exporters = ["csv", "json"]`) needs no extra.
"""

from __future__ import annotations

import importlib.util

from starlette_admin.export.base import BaseExporter, ExportConfig, ExportContext
from starlette_admin.export.csv import CsvExporter, TsvExporter
from starlette_admin.export.json import JsonExporter
from starlette_admin.export.pdf import PdfExporter
from starlette_admin.export.tablib import TablibExporter

# A `requires` string maps to the modules that must all be importable for it
# to be considered available. Distinct from the pip extra name because a
# tablib format extra (e.g. "tablib[xlsx]") installs a different top-level
# module (openpyxl) than tablib itself.
_EXTRA_MODULES: dict[str, tuple[str, ...]] = {
    "tablib": ("tablib",),
    "tablib[xlsx]": ("tablib", "openpyxl"),
    "tablib[yaml]": ("tablib", "yaml"),
    "tablib[xls]": ("tablib", "xlrd", "xlwt"),
    "tablib[ods]": ("tablib", "odf"),
    "reportlab": ("reportlab",),
}


def is_extra_available(requires: str) -> bool:
    """Return `True` if every module behind a `requires` string (e.g. `"tablib[xlsx]"`) is importable."""
    modules = _EXTRA_MODULES.get(requires, (requires.split("[", 1)[0],))
    return all(importlib.util.find_spec(m) is not None for m in modules)


# Extension -> exporter instance. Each exporter is stateless after
# construction (generate() never writes to self), so one shared instance
# per format is safe to reuse across requests.
EXPORT_FORMATS: dict[str, BaseExporter] = {
    "csv": CsvExporter(),
    "tsv": TsvExporter(),
    "json": JsonExporter(),
    "yaml": TablibExporter("yaml"),
    "xlsx": TablibExporter("xlsx"),
    "xls": TablibExporter("xls"),
    "ods": TablibExporter("ods"),
    "dbf": TablibExporter("dbf"),
    "html": TablibExporter("html"),
    "latex": TablibExporter("latex"),
    "jira": TablibExporter("jira"),
    "rst": TablibExporter("rst"),
    "pdf": PdfExporter(),
}


def register_export_format(name: str, exporter: BaseExporter) -> None:
    """Register `exporter` under `name` in `EXPORT_FORMATS`. Plugin API.

    Registration only makes the format available; a view still opts in via
    its own `exporters` list.
    """
    EXPORT_FORMATS[name] = exporter


def resolve_exporter(exporter: str | BaseExporter) -> BaseExporter:
    """Resolve `exporter` to a ready-to-use, availability-checked instance.

    Accepts either a registered format name (looked up in `EXPORT_FORMATS`) or
    an already-instantiated `BaseExporter` (e.g. a bare `TablibExporter("xlsx")`).
    This is the single place export availability is enforced, so callers
    never need to check `requires` themselves.

    Raises:
        ValueError: `exporter` is a string that is not a known format.
        ImportError: the resolved exporter's required package isn't installed.
    """
    instance = (
        exporter if isinstance(exporter, BaseExporter) else EXPORT_FORMATS.get(exporter)
    )
    if instance is None:
        raise ValueError(
            f"Unknown export format {exporter!r}. Available: {sorted(EXPORT_FORMATS)}"
        )
    if instance.requires and not is_extra_available(instance.requires):
        name = instance.format_key or instance.extension
        raise ImportError(
            f"{name!r} export requires {instance.requires!r}, which is not "
            f"installed. Install it with: pip install {instance.requires}"
        )
    return instance


__all__ = [
    "EXPORT_FORMATS",
    "BaseExporter",
    "CsvExporter",
    "ExportConfig",
    "ExportContext",
    "JsonExporter",
    "PdfExporter",
    "TablibExporter",
    "TsvExporter",
    "is_extra_available",
    "register_export_format",
    "resolve_exporter",
]
