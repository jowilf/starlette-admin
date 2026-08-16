"""Import format registry: maps a format string to its importer instance.

Every non-core format goes through `tablib`, an optional dependency. csv,
tsv and json are implemented in core with the standard library, so the
default configuration (`importers = ["csv", "json"]`) needs no extra.
"""

from __future__ import annotations

from starlette_admin.export import is_extra_available
from starlette_admin.importers.base import (
    BaseImporter,
    ImportConfig,
    ImportContext,
    ImportResult,
    ImportRowError,
)
from starlette_admin.importers.csv import CsvImporter, TsvImporter
from starlette_admin.importers.json import JsonImporter
from starlette_admin.importers.tablib import TablibImporter

# Extension -> importer instance. Each importer is stateless after
# construction (parse() never writes to self), so one shared instance
# per format is safe to reuse across requests.
IMPORT_FORMATS: dict[str, BaseImporter] = {
    "csv": CsvImporter(),
    "tsv": TsvImporter(),
    "json": JsonImporter(),
    "yaml": TablibImporter("yaml"),
    "xlsx": TablibImporter("xlsx"),
    "xls": TablibImporter("xls"),
    "ods": TablibImporter("ods"),
    "dbf": TablibImporter("dbf"),
    "html": TablibImporter("html"),
}


def register_import_format(name: str, importer: BaseImporter) -> None:
    """Register `importer` under `name` in `IMPORT_FORMATS`. Plugin API.

    Registration only makes the format available; a view still opts in via
    its own `importers` list.
    """
    IMPORT_FORMATS[name] = importer


def resolve_importer(importer: str | BaseImporter) -> BaseImporter:
    """Resolve `importer` to a ready-to-use, availability-checked instance.

    Accepts either a registered format name (looked up in `IMPORT_FORMATS`) or
    an already-instantiated `BaseImporter` (e.g. a bare `TablibImporter("xlsx")`).
    This is the single place import availability is enforced, so callers
    never need to check `requires` themselves.

    Raises:
        ValueError: `importer` is a string that is not a known format.
        ImportError: the resolved importer's required package isn't installed.
    """
    instance = (
        importer if isinstance(importer, BaseImporter) else IMPORT_FORMATS.get(importer)
    )
    if instance is None:
        raise ValueError(
            f"Unknown import format {importer!r}. Available: {sorted(IMPORT_FORMATS)}"
        )
    if instance.requires and not is_extra_available(instance.requires):
        name = instance.format_key or instance.extension
        raise ImportError(
            f"{name!r} import requires {instance.requires!r}, which is not "
            f"installed. Install it with: pip install {instance.requires}"
        )
    return instance


__all__ = [
    "IMPORT_FORMATS",
    "BaseImporter",
    "CsvImporter",
    "ImportConfig",
    "ImportContext",
    "ImportResult",
    "ImportRowError",
    "JsonImporter",
    "TablibImporter",
    "TsvImporter",
    "register_import_format",
    "resolve_importer",
]
