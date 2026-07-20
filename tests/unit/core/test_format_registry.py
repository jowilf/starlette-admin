"""Unit tests for the export/import format registries: string resolution,
tsv wiring, missing-extra errors, and tablib round-trips per format."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from starlette_admin.export import (
    EXPORT_FORMATS,
    BaseExporter,
    is_extra_available,
    resolve_exporter,
)
from starlette_admin.export.csv import CsvExporter
from starlette_admin.export.tablib import TablibExporter
from starlette_admin.importers import (
    IMPORT_FORMATS,
    resolve_importer,
)
from starlette_admin.importers.base import ImportContext
from starlette_admin.importers.csv import CsvImporter


@dataclass
class _Field:
    name: str
    label: str | None = None


# ── string resolution ───────────────────────────────────────────────────────


def test_resolve_exporter_csv_returns_core_class():
    exporter = resolve_exporter("csv")
    assert isinstance(exporter, CsvExporter)
    assert exporter.extension == "csv"
    assert exporter.content_type == "text/csv"


def test_resolve_exporter_json_returns_core_class():
    from starlette_admin.export.json import JsonExporter

    assert isinstance(resolve_exporter("json"), JsonExporter)


def test_resolve_exporter_tablib_format():
    exporter = resolve_exporter("yaml")
    assert isinstance(exporter, TablibExporter)
    assert exporter.format == "yaml"
    assert exporter.content_type == "application/x-yaml"


def test_resolve_exporter_unknown_format_raises_value_error():
    with pytest.raises(ValueError, match="Unknown export format"):
        resolve_exporter("bogus")


def test_resolve_importer_unknown_format_raises_value_error():
    with pytest.raises(ValueError, match="Unknown import format"):
        resolve_importer("bogus")


def test_resolve_exporter_missing_extra_raises_import_error():
    with (
        patch("starlette_admin.export.is_extra_available", return_value=False),
        pytest.raises(ImportError, match="pip install tablib\\[xlsx\\]"),
    ):
        resolve_exporter("xlsx")


def test_resolve_importer_missing_extra_raises_import_error():
    with (
        patch("starlette_admin.importers.is_extra_available", return_value=False),
        pytest.raises(ImportError, match="pip install tablib\\[xlsx\\]"),
    ):
        resolve_importer("xlsx")


def test_resolve_exporter_bare_tablib_extra_names_tablib_in_message():
    with (
        patch("starlette_admin.export.is_extra_available", return_value=False),
        pytest.raises(ImportError, match="pip install tablib"),
    ):
        resolve_exporter("dbf")


# ── tsv wiring ───────────────────────────────────────────────────────────────


def test_resolve_exporter_tsv_is_csv_exporter_with_tab_delimiter():
    exporter = resolve_exporter("tsv")
    assert isinstance(exporter, CsvExporter)
    assert exporter.extension == "tsv"
    assert exporter.content_type == "text/tab-separated-values"
    assert exporter.fmtparams == {"delimiter": "\t"}


def test_resolve_importer_tsv_is_csv_importer_with_tab_delimiter():
    importer = resolve_importer("tsv")
    assert isinstance(importer, CsvImporter)
    assert importer.extension == "tsv"
    assert importer.fmtparams == {"delimiter": "\t"}


@pytest.mark.asyncio
async def test_tsv_roundtrip():
    exporter = resolve_exporter("tsv")
    importer = resolve_importer("tsv")
    fields = [_Field("name", "Name"), _Field("city", "City")]
    rows = [{"name": "Alice", "city": "Paris"}]

    data = await exporter.generate(fields, rows)
    assert b"\t" in data

    ctx = ImportContext(fields=[], content=data, view=None, request=None)
    parsed = [row async for row in importer.parse(ctx)]
    assert parsed == [{"Name": "Alice", "City": "Paris"}]


# ── csv/tsv **fmtparams ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_csv_exporter_custom_delimiter():
    exporter = CsvExporter(delimiter=";")
    fields = [_Field("a", "A"), _Field("b", "B")]
    data = await exporter.generate(fields, [{"a": "1", "b": "2"}])
    assert data == b"A;B\r\n1;2\r\n"


@pytest.mark.asyncio
async def test_csv_importer_custom_delimiter():
    importer = CsvImporter(delimiter=";")
    ctx = ImportContext(fields=[], content=b"A;B\r\n1;2\r\n", view=None, request=None)
    rows = [row async for row in importer.parse(ctx)]
    assert rows == [{"A": "1", "B": "2"}]


# ── EXPORT_FORMATS / IMPORT_FORMATS coverage ────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", sorted(EXPORT_FORMATS))
async def test_every_export_format_generates_bytes(fmt):
    exporter = resolve_exporter(fmt)
    assert isinstance(exporter, BaseExporter)
    fields = [_Field("title", "Title")]
    data = await exporter.generate(fields, [{"title": "Hello"}])
    assert isinstance(data, bytes)
    assert len(data) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", sorted(IMPORT_FORMATS))
async def test_every_import_format_roundtrips(fmt):
    exporter = resolve_exporter(fmt)
    importer = resolve_importer(fmt)
    fields = [_Field("title", "Title")]
    data = await exporter.generate(fields, [{"title": "Hello"}])

    ctx = ImportContext(fields=[], content=data, view=None, request=None)
    rows = [row async for row in importer.parse(ctx)]
    assert len(rows) == 1
    # dbf upper-cases headers (10-char field name limit); accept either case.
    value = rows[0].get("Title") or rows[0].get("TITLE")
    assert value == "Hello"


# ── formula escaping on tablib spreadsheet formats ──────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", ["xlsx", "ods"])
async def test_tablib_spreadsheet_formats_escape_formulas(fmt):
    exporter = TablibExporter(fmt)
    importer = resolve_importer(fmt)
    fields = [_Field("cmd", "Cmd")]
    data = await exporter.generate(fields, [{"cmd": "=cmd|'/c calc'!A1"}])

    ctx = ImportContext(fields=[], content=data, view=None, request=None)
    rows = [row async for row in importer.parse(ctx)]
    assert rows[0]["Cmd"] == "'=cmd|'/c calc'!A1"


@pytest.mark.asyncio
async def test_tablib_non_spreadsheet_format_does_not_escape_formulas():
    """yaml/json/html/latex/dbf are not opened as spreadsheets, so a leading
    '=' must not be corrupted with an extra leading quote."""
    exporter = TablibExporter("yaml")
    fields = [_Field("cmd", "Cmd")]
    data = await exporter.generate(fields, [{"cmd": "=SUM(A1)"}])
    assert b"'=SUM(A1)" not in data
    assert b"=SUM(A1)" in data


@pytest.mark.asyncio
async def test_tablib_exporter_escape_formulas_disabled():
    """With escaping off, a leading '=' reaches the sheet as a literal
    formula (xlsx's own semantics) instead of being prefixed with a
    protective quote. tablib's importer always opens with `data_only=True`
    (no cached result for a freshly written formula), so this is checked by
    reading the formula text back via openpyxl directly, not by round-
    tripping through `resolve_importer`.
    """
    import io

    import openpyxl

    exporter = TablibExporter("xlsx", escape_formulas=False)
    fields = [_Field("cmd", "Cmd")]
    data = await exporter.generate(fields, [{"cmd": "=SUM(A1)"}])

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=False)
    value = next(wb.active.iter_rows(values_only=True, min_row=2))[0]
    assert value == "=SUM(A1)"


# ── is_extra_available ──────────────────────────────────────────────────────


def test_is_extra_available_true_for_installed_tablib():
    assert is_extra_available("tablib") is True


def test_is_extra_available_false_for_unknown_module():
    assert is_extra_available("definitely-not-a-real-package") is False
