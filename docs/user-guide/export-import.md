---
title: Export and Import
description: Enable CSV, JSON, and PDF export functionality and bulk data imports with validation in starlette-admin.
---

# Export and Import

Every list page lets users export data to a file and import data from a file, so you don't have to write custom routes.

## Overview

* **Export:** Users select the toolbar button, then set the scope, fields, format, and filename.
* **Import:** Users select the toolbar button to open a three-step wizard: upload, preview, and results.
* **Formats:** CSV, JSON, XLSX, ODS, YAML, PDF, and custom formats are supported out of the box.
* **Upsert:** Imports can optionally update existing records matched by primary key.
* **Integration:** Both features work with filtering, sorting, row selection, and storage-backed fields.
* **No extra endpoints:** Everything ships with the view.

## Minimal example

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()

class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))

```

`ProductView` now shows an **Export** button and an **Import** button in the list toolbar. Each dialog offers exactly the formats you list in `exporters` and `importers`.

---

## Enabling export

The `exporters` attribute lists the formats to expose, as plain extension strings:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

The default is `["csv", "json"]`. The table below lists every built-in format and the package it needs. The `csv`, `tsv`, and `json` formats need no extra dependencies. Every other tabular format uses `tablib`, and `pdf` uses `reportlab`. An unknown format string, or a format whose package isn't installed, raises an error at startup.

| Format | Install requirement |
| --- | --- |
| `csv`, `tsv`, `json` | Included in core |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Overriding format options

Each format string resolves to a preconfigured exporter instance with sensible defaults. When a format needs different settings, pass an exporter instance instead of the string. You can mix strings and instances in the same list:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` forwards keyword arguments to `csv.writer` and accepts an `escape_formulas` parameter. `TablibExporter(format, **kwargs)` covers every tablib format and forwards keyword arguments to `tablib.Dataset.export()`.

!!! warning
    Formula escaping is off by default. If exported fields can contain user-supplied strings, set `escape_formulas=True` on `CsvExporter`, `TsvExporter`, or `TablibExporter` to prevent formula injection when someone opens the file in a spreadsheet application. See [Formula injection](security.md#formula-injection).

Export is on by default. The **Export** button appears in the toolbar whenever the `exporters` list isn't empty. To restrict who can export, override the `can_export(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### The export dialog

Export is a built-in global action. Selecting **Export** opens a dialog where the user sets up the export before downloading it.

* **Scope:** What to export. The options are "Selected rows", the default when rows are checked, "All matching rows", available from the select-all banner, and "Current page", the default when nothing is selected.
* **Fields:** One checkbox per exportable field. Clearing a checkbox drops that column. Fields marked `exclude_from_export=True` never appear here.
* **Format:** One entry per format in `exporters`.
* **Filename:** Defaults to the view key. The server appends the file extension.

Every scope honors the list page's current search, filters, and sort order, so what the user sees is what they export.

### The row cap

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)

```

`ExportConfig.max_rows` defaults to 100,000. The cap applies to the number of rows the chosen scope would actually produce, and the admin checks the count before it fetches any row. When the count goes over the limit, the admin flashes an error and redirects back to the list page instead of generating the file. This keeps a broad, unfiltered export on a large table from hanging the request. Set `max_rows=None` to remove the limit.

---

## Enabling import

The `importers` attribute works exactly like `exporters` and accepts format strings:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

The built-in import formats are `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf`, and `html`, with the same dependencies as their export counterparts. To override a format's defaults, pass an importer instance, such as `CsvImporter(delimiter=";")` from `starlette_admin.importers`.

Import is on by default, with `["csv", "json"]`. The **Import** button appears in the toolbar whenever the `importers` list isn't empty. To restrict who can import, override the `can_import(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### The import wizard

Selecting **Import** opens a three-step wizard. Nothing is written to the database before the final confirmation, and no file is stored on the server between steps: the browser holds the file and reposts it at each step.

1. **Upload:** Pick a format, choose a file, and optionally select **Update existing records by primary key**. When you select it, a row whose primary key matches an existing record updates that record instead of creating a new one. Otherwise, every row is created.
2. **Preview:** Submitting the upload runs a full validation pass without writing anything. The wizard shows a summary, the column mappings, sample rows, and a detailed error table.
3. **Result:** The wizard commits the import and reports the final counts for created, updated, and skipped records. Rows that failed validation in the preview are skipped.

!!! tip
    To let the backend generate primary keys, clear the primary key column in the preview mapping. The imported rows then carry no key value, so reimporting a file you exported creates fresh records instead of failing on stale IDs.

### Upload and row caps

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

The import endpoint mirrors the export row cap. `ImportConfig.max_rows` defaults to 100,000 and is enforced before any record is created. The admin counts the uploaded file in a pre-pass and rejects a file with more rows than the cap with an HTTP 400 error. Set `max_rows=None` to remove the limit. `ImportConfig.max_upload_size` also caps uploads at 10 MB by default.

### Header matching

The wizard matches each file header against your field's `label` first, then its `name`. A file with the column `Name` and a file with the column `name` both map to a field named `name`. Unmatched columns are ignored, and fields without a matching column receive `None`.

## File fields

A view with a storage-backed `FileField` or `ImageField` exports as a ZIP archive, so the file contents travel with the row data:

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

Exporting `ProductView` to CSV produces an `export.zip` with this structure:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

The `photo` column in `export.csv` holds the file's ZIP-relative path, `assets/<storage-name>/<key>`, which keeps the CSV readable in a spreadsheet application. The admin fetches every referenced file from its storage backend and packages it under `assets/`.

Import doesn't accept ZIP archives. `FileField` and `ImageField` are always excluded from import, because `exclude_from_import=True` by default, so the wizard ignores the `photo` column on upload. Reimport a plain data file, then attach files through the create or edit forms.


## Writing a custom exporter

To write a custom exporter, subclass `BaseExporter` and implement the `generate` method. The base class handles ZIP wrapping, file downloads, and response headers:

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField

class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

The `rows` data arrives pre-cleaned: the admin replaces each `FileField` and `ImageField` value with its ZIP-relative path string first, so your `generate` method never handles file dictionaries. Register `MarkdownExporter()` in your `exporters` list to show it in the format dropdown.

## Writing a custom importer

To write a custom importer, subclass `BaseImporter` and implement `parse` as an async generator that yields one dictionary per row:

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext

class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## What's next

* **[File Storage](file-storage.md):** Configure the storage backends referenced in the export ZIP bundle.
* **[Security](security.md):** Export row caps and import upload size limits.
* **[Actions](actions.md):** Add bulk and row actions alongside export and import.
