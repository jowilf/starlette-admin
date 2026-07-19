"""Unit tests for starlette_admin.importers: base machinery and format importers."""

from __future__ import annotations

import csv
import io
import json
from typing import Any
from unittest.mock import MagicMock

import openpyxl
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.export.csv import CsvExporter
from starlette_admin.export.excel import ExcelExporter
from starlette_admin.export.json import JsonExporter
from starlette_admin.importers.base import ImportContext
from starlette_admin.importers.csv import CsvImporter
from starlette_admin.importers.excel import ExcelImporter
from starlette_admin.importers.json import JsonImporter

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_request() -> Request:
    Starlette()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


def _make_ctx(content: bytes) -> ImportContext:
    return ImportContext(
        fields=[],
        content=content,
        view=MagicMock(),
        request=_make_request(),
    )


def _csv_bytes(*rows: list[str]) -> bytes:
    out = io.StringIO()
    csv.writer(out).writerows(rows)
    return out.getvalue().encode("utf-8")


def _excel_bytes(headers: list[str], *rows: list[Any]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _json_bytes(data: list[dict]) -> bytes:
    return json.dumps(data).encode("utf-8")


async def _collect(gen) -> list[dict]:
    rows = []
    async for row in gen:
        rows.append(row)
    return rows


# ── CsvImporter ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_csv_importer_basic():
    importer = CsvImporter()
    raw = _csv_bytes(["Name", "Age"], ["Alice", "30"], ["Bob", "25"])
    ctx = _make_ctx(raw)

    rows = await _collect(importer.parse(ctx))

    assert rows == [{"Name": "Alice", "Age": "30"}, {"Name": "Bob", "Age": "25"}]


@pytest.mark.asyncio
async def test_csv_importer_empty_file():
    importer = CsvImporter()
    ctx = _make_ctx(b"Name,Age\n")  # header only, no data rows
    rows = await _collect(importer.parse(ctx))
    assert rows == []


@pytest.mark.asyncio
async def test_csv_importer_strips_bom():
    importer = CsvImporter()
    # utf-8-sig encoding adds the BOM prefix (\xef\xbb\xbf) before the content
    content = "Name,Age\nAlice,30\n".encode("utf-8-sig")
    ctx = _make_ctx(content)
    rows = await _collect(importer.parse(ctx))
    assert next(iter(rows[0].keys())) == "Name"  # BOM stripped, not "﻿Name"


# ── ExcelImporter ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_excel_importer_basic():
    importer = ExcelImporter()
    raw = _excel_bytes(["Name", "Score"], ["Alice", 95], ["Bob", 82])
    ctx = _make_ctx(raw)

    rows = await _collect(importer.parse(ctx))

    assert rows == [{"Name": "Alice", "Score": "95"}, {"Name": "Bob", "Score": "82"}]


@pytest.mark.asyncio
async def test_excel_importer_empty_workbook():
    importer = ExcelImporter()
    raw = _excel_bytes(["Name"])  # header only
    ctx = _make_ctx(raw)
    rows = await _collect(importer.parse(ctx))
    assert rows == []


@pytest.mark.asyncio
async def test_excel_importer_none_cells_become_empty_string():
    importer = ExcelImporter()
    raw = _excel_bytes(["Name", "Note"], ["Alice", None])
    ctx = _make_ctx(raw)
    rows = await _collect(importer.parse(ctx))
    assert rows[0]["Note"] == ""


# ── JsonImporter ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_json_importer_basic():
    importer = JsonImporter()
    raw = _json_bytes([{"Name": "Alice", "Age": "30"}, {"Name": "Bob", "Age": "25"}])
    ctx = _make_ctx(raw)

    rows = await _collect(importer.parse(ctx))

    assert rows == [{"Name": "Alice", "Age": "30"}, {"Name": "Bob", "Age": "25"}]


@pytest.mark.asyncio
async def test_json_importer_empty_array():
    importer = JsonImporter()
    ctx = _make_ctx(b"[]")
    rows = await _collect(importer.parse(ctx))
    assert rows == []


@pytest.mark.asyncio
async def test_json_importer_non_array_raises():
    importer = JsonImporter()
    ctx = _make_ctx(b'{"key": "value"}')
    with pytest.raises(ValueError, match="top-level array"):
        async for _ in importer.parse(ctx):
            pass


# ── Round-trip: export then import ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_csv_roundtrip():
    from starlette_admin.fields import BaseField

    exporter = CsvExporter()
    importer = CsvImporter()

    f1 = BaseField(name="name")
    f1.label = "Name"
    f2 = BaseField(name="city")
    f2.label = "City"
    fields = [f1, f2]

    original = [{"name": "Alice", "city": "Paris"}, {"name": "Bob", "city": "Lyon"}]
    export_bytes = await exporter.generate(fields, original)

    ctx = _make_ctx(export_bytes)
    imported = await _collect(importer.parse(ctx))

    assert imported == [
        {"Name": "Alice", "City": "Paris"},
        {"Name": "Bob", "City": "Lyon"},
    ]


@pytest.mark.asyncio
async def test_excel_roundtrip():
    from starlette_admin.fields import BaseField

    exporter = ExcelExporter()
    importer = ExcelImporter()

    f1 = BaseField(name="item")
    f1.label = "Item"
    f2 = BaseField(name="qty")
    f2.label = "Qty"
    fields = [f1, f2]

    original = [{"item": "Widget", "qty": 10}, {"item": "Gadget", "qty": 5}]
    export_bytes = await exporter.generate(fields, original)

    ctx = _make_ctx(export_bytes)
    imported = await _collect(importer.parse(ctx))

    # values are coerced to strings by ExcelImporter
    assert imported[0]["Item"] == "Widget"
    assert imported[0]["Qty"] == "10"


@pytest.mark.asyncio
async def test_json_roundtrip():
    from starlette_admin.fields import BaseField

    exporter = JsonExporter()
    importer = JsonImporter()

    f1 = BaseField(name="product")
    f1.label = "Product"
    f2 = BaseField(name="price")
    f2.label = "Price"
    fields = [f1, f2]

    original = [
        {"product": "Apple", "price": "1.50"},
        {"product": "Banana", "price": "0.75"},
    ]
    export_bytes = await exporter.generate(fields, original)

    ctx = _make_ctx(export_bytes)
    imported = await _collect(importer.parse(ctx))

    assert imported == [
        {"Product": "Apple", "Price": "1.50"},
        {"Product": "Banana", "Price": "0.75"},
    ]


# ── ImportResult.rows_ok ──────────────────────────────────────────────────────


def test_import_result_rows_ok():
    from starlette_admin.importers.base import ImportResult

    result = ImportResult(rows_created=2, rows_updated=1, rows_skipped=1)
    assert result.rows_ok == 4


# ── ExcelImporter empty workbook ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_excel_importer_truly_empty_workbook():
    """A workbook whose active sheet is None (e.g. all sheets hidden) yields no rows."""
    from unittest.mock import MagicMock, patch

    importer = ExcelImporter()
    mock_wb = MagicMock()
    mock_wb.active = None
    with patch("openpyxl.load_workbook", return_value=mock_wb):
        ctx = _make_ctx(b"fake-xlsx-bytes")
        rows = await _collect(importer.parse(ctx))
    assert rows == []


# ── BaseAdmin._parse_import_row edge-cases ────────────────────────────────────


@pytest.mark.asyncio
async def test_parse_import_row_fills_none_for_missing_field():
    """A field present in the view but absent from the import row gets None (base.py 825)."""
    from starlette_admin import BaseAdmin, StringField

    admin = BaseAdmin(secret_key="test-secret")
    name_field = StringField("name")
    extra_field = StringField("extra")
    fields = [name_field, extra_field]
    field_by_header = {"Name": name_field, "name": name_field}

    ctx = MagicMock()
    row = {"Name": "Alice"}
    data = await admin._parse_import_row(row, fields, field_by_header, False, None, ctx)

    assert data["name"] == "Alice"
    assert data["extra"] is None


@pytest.mark.asyncio
async def test_parse_import_row_skip_pk_nulls_pk_in_data():
    """skip_pk=True clears the pk value when it was parsed from the import row (base.py 827-828)."""
    from starlette_admin import BaseAdmin, IntegerField, StringField

    admin = BaseAdmin(secret_key="test-secret")
    id_field = IntegerField("id")
    name_field = StringField("name")
    fields = [id_field, name_field]
    field_by_header = {
        "Id": id_field,
        "id": id_field,
        "Name": name_field,
        "name": name_field,
    }

    ctx = MagicMock()
    row = {"Id": "999", "Name": "Alice"}
    data = await admin._parse_import_row(row, fields, field_by_header, True, "id", ctx)

    assert data["name"] == "Alice"
    assert data["id"] is None
