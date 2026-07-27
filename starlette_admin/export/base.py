"""Base export machinery: format-agnostic, with ZIP wrapping for file fields."""

from __future__ import annotations

import asyncio
import hashlib
import io
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.exceptions import ExportError
from starlette_admin.export.helpers import (
    is_file_dict,
    is_url_file_dict,
    resolve_download_url,
    safe_cd_filename,
    safe_zip_key,
    safe_zip_name,
)
from starlette_admin.logging import get_logger

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField
    from starlette_admin.views import BaseModelView

_log = get_logger(__name__)


@dataclass
class ExportConfig:
    """Capacity and security limits for the export endpoint.

    Attributes:
        max_rows: Maximum number of rows that may be exported in a single
            request (default: 100,000). When the filtered row count exceeds
            this limit, the endpoint returns HTTP 400 so you can narrow your
            filter or request a scheduled export instead. Set to ``None`` to
            disable the cap entirely.
        restrict_url_download: When ``True`` (the default) and no
            ``safe_download_url`` is provided, only URL-only file references
            whose origin matches the admin's ``base_url`` are downloaded into
            the export ZIP. All other URLs are silently skipped. Set to
            ``False`` to disable the built-in restriction (not recommended
            unless you fully control the data).
        max_download_size: Maximum number of bytes to accept from a single
            URL-only file download (default: 20 MB). Files whose response body
            exceeds this limit are silently skipped with a warning so the export
            still completes. Set to ``None`` to disable the cap entirely.
            Example: ``10 * 1024 * 1024`` for a 10 MB cap per file.
        safe_download_url: Optional callback ``(url, request) -> str | None``
            called for every URL-only file reference before download. Return
            the URL to fetch (may be a transformed/signed URL), or ``None`` to
            skip. When provided, ``restrict_url_download`` is ignored; the
            callback has full control.

            Typical use-cases:

            * Libraries like ``sqlalchemy_file`` that serve files through the
              admin itself: return the URL unchanged (it already starts with
              ``base_url``).
            * Third-party CDNs: validate the domain and/or exchange the public
              URL for a time-limited signed URL before returning it.
    """

    max_rows: int | None = 100_000
    restrict_url_download: bool = True
    max_download_size: int | None = 20 * 1024 * 1024  # 20 MB
    safe_download_url: Callable[[str, Request], str | None] | None = None


@dataclass
class ExportContext:
    """Everything an exporter needs to produce its output.

    Attributes:
        fields: Fields to export, in column order.
        rows: Pre-serialized row dicts returned by
            :meth:`~starlette_admin.views.BaseModelView.serialize`.
            Each dict contains ``{field.name: serialized_value}`` plus a
            ``_meta`` key that exporters must ignore.
        view: The model view performing the export.
        request: The originating HTTP request.
        filename: Base name for the download, without extension (default
            ``"export"``).
        export_config: URL-download security and row-limit settings. Defaults
            to :class:`ExportConfig` with all defaults (``restrict_url_download``
            enabled).
    """

    fields: list[BaseField]
    rows: list[dict[str, Any]]
    view: BaseModelView
    request: Request
    filename: str = "export"
    export_config: ExportConfig = dc_field(default_factory=ExportConfig)


class BaseExporter(ABC):
    """Base class for all export-format implementations.

    Sub-classes implement :meth:`generate` to produce format-specific bytes
    from already-cleaned row data.  This base class handles:

    * replacing ``FileInfo`` dict values with their ZIP-relative paths
      (``assets/<storage_name>/<key>``) when any visible field has stored files,
    * downloading those files from their storage backends via
      :meth:`~starlette_admin.storage.BaseStorage.read`,
    * wrapping the format bytes and downloaded files in a ZIP archive.

    **Minimal sub-class example**::

        class CsvExporter(BaseExporter):
            content_type = "text/csv"
            extension = "csv"

            async def generate(
                self,
                fields: list[BaseField],
                rows: list[dict[str, Any]],
            ) -> bytes:
                output = io.StringIO()
                writer = csv.DictWriter(
                    output, fieldnames=[f.label or f.name for f in fields]
                )
                writer.writeheader()
                for row in rows:
                    writer.writerow(
                        {(f.label or f.name): row.get(f.name, "") for f in fields}
                    )
                return output.getvalue().encode()

    **ZIP layout when file fields are present**::

        export.csv          ← the formatted data file
        assets/
          local/            ← storage name
            covers/photo.jpg
          s3/
            products/img.png
    """

    content_type: str = "application/octet-stream"
    extension: str = "bin"
    format_key: str = ""  # URL param value; defaults to extension when empty
    requires: str | None = None  # pip extra needed, or None if always available

    @abstractmethod
    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        """Produce format-specific bytes from cleaned export data.

        Parameters:
            fields: Visible fields in column order.  Use ``field.label or
                field.name`` for column headers and ``field.name`` as the key
                into each *rows* dict.
            rows: ``{field.name: serialized_value}`` dicts where file-field
                values have already been replaced with their ZIP-relative path
                strings (``assets/<storage>/<key>``), so implementations never
                need to special-case :class:`~starlette_admin.storage.FileInfo`
                dicts. All other values are the serialized values produced by
                :meth:`~starlette_admin.views.BaseModelView.serialize` for the
                ``EXPORT`` action.
        """
        raise NotImplementedError(
            "Sub-classes must implement generate()"
        )  # pragma: no cover

    # Internal helpers

    def _zip_path_for_file(
        self,
        value: dict[str, Any],
        file_map: dict[str, tuple[str, str]],
    ) -> str:
        """Convert one ``FileInfo`` dict to its ZIP-relative path and register
        it in *file_map* for later download.

        Returns the ZIP path string (``assets/<storage>/<key>``).
        """
        storage_name: str = safe_zip_name(value["storage"], "storage_name")
        key: str = safe_zip_key(value["key"])
        zip_path = f"assets/{storage_name}/{key}"
        file_map[zip_path] = (storage_name, key)
        return zip_path

    def _zip_path_for_url_file(
        self,
        value: dict[str, Any],
        url_file_map: dict[str, str],
    ) -> str:
        """Convert a URL-only file dict to its ZIP-relative path and register it
        in *url_file_map* for later download.

        The ZIP path is ``assets/url/<hash>_<filename>`` where the hash prefix
        prevents collisions between files with the same name from different URLs.
        """
        url: str = value["url"]
        filename: str = value.get("filename") or ""
        if not filename:
            parsed = urlparse(url)
            filename = parsed.path.rsplit("/", 1)[-1].split("?")[0] or "file"
        filename = safe_zip_name(filename, "filename")
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
        zip_path = f"assets/url/{url_hash}_{filename}"
        url_file_map[zip_path] = url
        return zip_path

    def _export_file_value(
        self,
        value: Any,
        file_map: dict[str, tuple[str, str]],
        url_file_map: dict[str, str],
    ) -> str:
        """Coerce one file-field value to its export string representation.

        Storage-backed ``FileInfo`` dicts are registered in *file_map*; URL-only
        dicts (no ``storage`` key) are registered in *url_file_map*.  Both return
        their ZIP-relative path.  Falls back to an empty string for ``None``.
        """
        if is_file_dict(value):
            return self._zip_path_for_file(value, file_map)
        if is_url_file_dict(value):
            return self._zip_path_for_url_file(value, url_file_map)
        if isinstance(value, dict):
            return str(value.get("url") or value.get("filename") or "")
        return str(value) if value is not None else ""

    def _preprocess_rows(
        self,
        fields: list[BaseField],
        raw_rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, tuple[str, str]], dict[str, str]]:
        """Replace ``FileInfo`` dicts with ZIP paths and collect file references.

        Returns:
            cleaned_rows: ``{field.name: serialized_value}`` dicts ready for
                :meth:`generate`.  ``_meta`` and unrecognised keys are dropped.
            file_map: ``{zip_path: (storage_name, key)}``: storage-backed files.
            url_file_map: ``{zip_path: url}``: URL-only files to fetch via HTTP.
        """
        from starlette_admin.fields import FileField

        file_map: dict[str, tuple[str, str]] = {}
        url_file_map: dict[str, str] = {}
        cleaned_rows: list[dict[str, Any]] = []

        for raw in raw_rows:
            cleaned: dict[str, Any] = {}
            for f in fields:
                value = raw.get(f.name)
                if isinstance(f, FileField):
                    if f.multiple and isinstance(value, list):
                        if f.storage is not None or any(
                            is_url_file_dict(v) for v in value if v
                        ):
                            parts = [
                                self._export_file_value(v, file_map, url_file_map)
                                for v in value
                                if v
                            ]
                            cleaned[f.name] = "\n".join(p for p in parts if p)
                        else:  # pragma: no cover
                            raise ExportError(
                                "Custom FileField implementation must return a valid "
                                "URL in the serialized value."
                            )
                    else:
                        if f.storage is not None or is_url_file_dict(value):
                            cleaned[f.name] = self._export_file_value(
                                value, file_map, url_file_map
                            )
                        else:  # pragma: no cover
                            raise ExportError(
                                "Custom FileField implementation must return a valid "
                                "URL in the serialized value."
                            )
                else:
                    cleaned[f.name] = value
            cleaned_rows.append(cleaned)

        return cleaned_rows, file_map, url_file_map

    async def _fetch_files(
        self,
        file_map: dict[str, tuple[str, str]],
    ) -> dict[str, bytes]:
        """Download all referenced files from their storage backends.

        Files that cannot be read (storage not registered, ``NotImplementedError``,
        ``FileNotFoundError``) are silently skipped; the export still proceeds
        with the remaining files.

        Returns:
            ``{zip_path: file_bytes}``
        """
        from starlette_admin.storage.base import UnknownStorageError, get_storage

        fetched: dict[str, bytes] = {}
        for zip_path, (storage_name, key) in file_map.items():
            _log.debug("export asset fetch: storage=%r key=%r", storage_name, key)
            try:
                storage = get_storage(storage_name)
                fetched[zip_path] = await storage.read(key)
                _log.debug(
                    "export asset fetched: %s (%d bytes)",
                    zip_path,
                    len(fetched[zip_path]),
                )
            except (UnknownStorageError, FileNotFoundError, NotImplementedError) as exc:
                _log.warning(
                    "export asset skipped: %s (%s: %s)",
                    zip_path,
                    type(exc).__name__,
                    exc,
                )
                continue
        return fetched

    async def _fetch_url_files(
        self,
        url_file_map: dict[str, str],
        config: ExportConfig,
        request: Request,
    ) -> dict[str, bytes]:
        """Download URL-only file references via HTTP.

        Each URL is first passed through :func:`resolve_download_url` using
        *config* and *request*.  URLs that resolve to ``None`` (blocked by the
        built-in allow-list or by ``config.safe_download_url``) are skipped
        with a warning.

        Failures (network errors, non-2xx responses) are also silently skipped
        so the export still completes with the remaining files.

        Returns:
            ``{zip_path: file_bytes}``
        """
        loop = asyncio.get_running_loop()
        fetched: dict[str, bytes] = {}
        for zip_path, url in url_file_map.items():
            effective_url = resolve_download_url(url, config, request)
            if effective_url is None:
                _log.warning(
                    "export url-asset blocked: %s; URL not permitted by export_config",
                    url,
                )
                continue
            scheme = urlparse(effective_url).scheme.lower()
            if scheme not in ("http", "https"):
                _log.warning(
                    "export url-asset blocked: %s; scheme %r not allowed (only http/https)",
                    effective_url,
                    scheme,
                )
                continue
            _log.debug("export url-asset fetch: url=%r -> %s", effective_url, zip_path)
            max_size = config.max_download_size
            try:

                def _download(u: str, limit: int | None = max_size) -> bytes:
                    with urllib.request.urlopen(u, timeout=30) as resp:
                        if limit is not None:
                            data = resp.read(limit + 1)
                            if len(data) > limit:
                                raise ValueError(
                                    f"response exceeds max_download_size ({limit} bytes)"
                                )
                            return data
                        return resp.read()

                fetched[zip_path] = await loop.run_in_executor(
                    None, _download, effective_url
                )
                _log.debug(
                    "export url-asset fetched: %s (%d bytes)",
                    zip_path,
                    len(fetched[zip_path]),
                )
            except Exception as exc:
                _log.warning(
                    "export url-asset skipped: %s (%s: %s)",
                    zip_path,
                    type(exc).__name__,
                    exc,
                )
                continue
        return fetched

    @staticmethod
    def _build_zip(
        format_bytes: bytes,
        format_filename: str,
        asset_files: dict[str, bytes],
    ) -> bytes:
        """Pack *format_bytes* and *asset_files* into an in-memory ZIP archive."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(format_filename, format_bytes)
            for zip_path, file_bytes in asset_files.items():
                zf.writestr(zip_path, file_bytes)
        return buf.getvalue()

    async def build_response(self, ctx: ExportContext) -> Response:
        """Build the HTTP :class:`~starlette_admin.responses.Response` for this export.

        When any visible :class:`~starlette_admin.fields.FileField` column
        carries stored file values, the response is a ``.zip`` archive with:

        * ``<filename>.<extension>``: the formatted data file,
        * ``assets/<storage>/<key>``: one entry per unique stored file.

        Otherwise, the format file is served directly with the appropriate
        ``Content-Type`` and ``Content-Disposition`` headers.
        """
        _log.debug(
            "export preprocess: %d row(s), %d field(s)",
            len(ctx.rows),
            len(ctx.fields),
        )
        cleaned_rows, file_map, url_file_map = self._preprocess_rows(
            ctx.fields, ctx.rows
        )
        _log.debug(
            "export preprocess complete: storage_assets=%d url_assets=%d",
            len(file_map),
            len(url_file_map),
        )
        _log.debug("export generating %s bytes", self.extension.upper())
        format_bytes = await self.generate(ctx.fields, cleaned_rows)
        _log.debug("export generate complete: %d bytes", len(format_bytes))

        if file_map or url_file_map:
            _log.debug(
                "export building ZIP: storage_assets=%d url_assets=%d",
                len(file_map),
                len(url_file_map),
            )
            asset_files = await self._fetch_files(file_map)
            url_files = await self._fetch_url_files(
                url_file_map, ctx.export_config, ctx.request
            )
            zip_bytes = self._build_zip(
                format_bytes,
                f"{safe_zip_name(ctx.filename, 'filename')}.{self.extension}",
                {**asset_files, **url_files},
            )
            _log.debug(
                "export ZIP built: %d bytes (fetched %d/%d storage, %d/%d url assets)",
                len(zip_bytes),
                len(asset_files),
                len(file_map),
                len(url_files),
                len(url_file_map),
            )
            safe_name = safe_cd_filename(ctx.filename)
            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": (f'attachment; filename="{safe_name}.zip"'),
                },
            )

        safe_name = safe_cd_filename(ctx.filename)
        _log.debug(
            "export response: %s %d bytes -> %s.%s",
            self.extension.upper(),
            len(format_bytes),
            ctx.filename,
            self.extension,
        )
        return Response(
            content=format_bytes,
            media_type=self.content_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{safe_name}.{self.extension}"'
                ),
            },
        )
