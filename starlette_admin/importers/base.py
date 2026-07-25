"""Base import machinery: dry-run scaffolding and per-row error reporting."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette_admin.fields import BaseField
    from starlette_admin.views import BaseModelView


@dataclass
class ImportConfig:
    """Security and capacity limits applied by the import endpoint.

    Attributes:
        max_upload_size: Maximum accepted file size in bytes (default: 10 MB).
            Checked before any parsing begins.
        max_rows: Maximum number of rows that may be imported in a single
            request (default: 100,000). The file is counted in a pre-pass
            before any record is created; when it holds more rows, the
            endpoint returns HTTP 400 so no partial import happens. Set to
            ``None`` to disable the cap entirely.
    """

    max_upload_size: int = 10 * 1024 * 1024
    max_rows: int | None = 100_000


@dataclass
class ImportRowError:
    """A validation or processing error for a single row.

    Attributes:
        row: The 1-based row number in the source file. Use ``0`` for file-level errors (e.g., unrecognized format, missing required column).
        field: The name of the offending field, or ``None`` for row-level errors.
        message: A human-readable description of the problem.
    """

    row: int
    field: str | None
    message: str


@dataclass
class ImportResult:
    """Summary returned after a (live or dry-run) import operation.

    Attributes:
        rows_total: The total number of data rows parsed from the source file.
        rows_created: The number of records successfully created (always 0 during a dry-run).
        rows_updated: The number of records updated in upsert mode (always 0 during a dry-run).
        rows_skipped: The number of valid rows that were intentionally skipped (e.g., unchanged in upsert mode).
        errors: Per-row validation and processing errors collected during the operation.
        dry_run: Indicates whether no data was actually committed.
    """

    rows_total: int = 0
    rows_created: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    errors: list[ImportRowError] = dc_field(default_factory=list)
    dry_run: bool = False

    @property
    def has_errors(self) -> bool:
        """Returns True if any row produced an error."""
        return bool(self.errors)

    @property
    def rows_ok(self) -> int:
        """The number of rows processed without error (created + updated + skipped)."""
        return self.rows_created + self.rows_updated + self.rows_skipped


@dataclass
class ImportContext:
    """Everything an importer needs to process one upload.

    Attributes:
        fields: Importable fields on the view (the same set used for export, resolved to the ``IMPORT`` request action).
        content: The raw bytes of the main data file (CSV, XLSX, JSON, etc.).
        view: The model view performing the import.
        request: The originating HTTP request.
        dry_run: When ``True``, the operation will parse and validate without committing any records. In this mode, :attr:`ImportResult.rows_created` and :attr:`ImportResult.rows_updated` will be 0.
        selected_fields: Field names to read from the uploaded file, or ``None`` for all of ``fields``. Columns for any other field are dropped before validation.
        update_existing: When ``True``, a row whose primary key matches an existing record updates it instead of creating a new one.
    """

    fields: list[BaseField]
    content: bytes
    view: BaseModelView
    request: Request
    dry_run: bool = False
    selected_fields: list[str] | None = None
    update_existing: bool = False


class BaseImporter(ABC):
    """Base class for all import-format implementations.

    Subclasses implement :meth:`parse` to yield parsed row dictionaries from the raw format bytes.

    **Minimal subclass example**::

        class CsvImporter(BaseImporter):
            extension = "csv"

            async def parse(
                self, ctx: ImportContext
            ) -> AsyncGenerator[dict[str, Any], None]:
                text = ctx.content.decode()
                reader = csv.DictReader(io.StringIO(text))
                for row in reader:
                    yield dict(row)

    File fields (:class:`~starlette_admin.fields.FileField`,
    :class:`~starlette_admin.fields.ImageField`) are always excluded from
    import; see ``exclude_from_import`` on :class:`~starlette_admin.fields.BaseField`.
    """

    extension: str = "bin"
    format_key: str = ""  # URL/form param value; defaults to extension when empty
    requires: str | None = None  # pip extra needed, or None if always available

    @abstractmethod
    def parse(
        self,
        ctx: ImportContext,
    ) -> AsyncGenerator[dict[str, Any]]:
        """Yield parsed row dictionaries from ``ctx.content``.

        Each yielded dictionary maps column headers (or field names) to raw string values.
        """
        raise NotImplementedError(
            "Sub-classes must implement parse()"
        )  # pragma: no cover
