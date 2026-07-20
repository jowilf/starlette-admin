## Export and Import

Every list page lets users export data to a file and import data from a file directly, eliminating the need to write custom routes.

### Overview

* **Export:** Use the toolbar button to configure the scope, fields, format, and filename.
* **Import:** Use the toolbar button to launch a three-step wizard handling upload, preview, and results.
* **Formats:** Leverage built-in support for CSV, JSON, XLSX, ODS, YAML, PDF, and custom formats.
* **Upsert:** Update existing records matched by primary key optionally during import.
* **Integration:** Works seamlessly with filtering, sorting, row selection, and storage-backed fields.
* **Zero Overhead:** Deploy with no custom endpoints required.

### Minimal Example

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

`ProductView` now displays an **Export** button and an **Import** button in the list toolbar. Both dialogs offer exactly the formats listed in the `exporters` and `importers` arrays.

---

## Enabling Export

The `exporters` attribute lists the formats to expose as plain extension strings:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

The default is `["csv", "json"]`. The table below lists every built-in format and the package it requires. The `csv`, `tsv`, and `json` formats ship with no extra dependencies. Every other tabular format uses `tablib`, and `pdf` uses `reportlab`. Declaring an unknown format string or a format whose package is not installed raises an error at startup.

| Format | Install Requirement |
| --- | --- |
| `csv`, `tsv`, `json` | Included in core |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Overriding Format Options

Each format string resolves to a pre-configured exporter instance with sensible defaults. When a format needs non-default settings, pass an exporter instance instead of the string. Strings and instances mix freely in the same list:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` forwards keyword arguments to `csv.writer` and accepts an `escape_formulas` parameter. `TablibExporter(format, **kwargs)` covers every tablib format and forwards keyword arguments to `tablib.Dataset.export()`.

Export is active by default. The **Export** button appears in the toolbar as long as the `exporters` list is non-empty. To restrict export access, override the `can_export(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### The Export Dialog

Export is a built-in global action. Clicking **Export** opens a dialog where the user configures the export before downloading.

* **Scope:** Configures what to export. Options include "Selected rows" (default when rows are checked), "All matching rows" (when using the select-all banner), and "Current page" (default when nothing is selected).
* **Fields:** Displays one checkbox per exportable field. Uncheck a field to drop its column. Fields marked `exclude_from_export=True` never appear here.
* **Format:** Shows one entry per format configured in `exporters`.
* **Filename:** Defaults to the view key. The server appends the file extension automatically.

Every scope honors the list page's current search, filters, and sort order. What you see in the interface is what you export.

### The Row Cap

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

The `ExportConfig.max_rows` setting defaults to 100,000. This cap applies to the number of rows the export would actually produce for the chosen scope. The count is checked before any row is fetched. When it exceeds the limit, the system flashes an error message and redirects back to the list page instead of generating the file. This prevents broad, unfiltered exports on large tables from hanging the request. Set `max_rows=None` to remove the limit entirely.

---

## Enabling Import

The `importers` attribute works exactly like `exporters` by accepting format strings:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

The built-in import formats are `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf`, and `html`, with the same dependency requirements as their export counterparts. Pass an importer instance to override a format's defaults, such as `CsvImporter(delimiter=";")` from `starlette_admin.importers`.

Import is active by default and defaults to `["csv", "json"]`. The **Import** button appears in the toolbar as long as the `importers` list is non-empty. To restrict import access, override the `can_import(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### The Import Wizard

Clicking **Import** opens a three-step wizard. Nothing is written to the database before the final confirmation, and no file is stored server-side between steps. The browser holds the file and re-posts it for each step.

1. **Upload:** Pick a format, choose a file, and optionally check **Update existing records by primary key**. When checked, a row whose primary key matches an existing record updates that record instead of creating a new one. When unchecked, every row is created.
2. **Preview:** Submitting the upload runs a full validation pass without writing anything. It displays a summary, column mappings, sample rows, and a detailed error table.
3. **Result:** Commits the import and reports the final row counts for created, updated, and skipped records. Rows that failed validation in the preview are skipped.
!!! tip
    To let a backend auto-generate primary keys, uncheck the primary key column in the preview mapping. The imported rows then carry no key value, ensuring that re-importing a file produced by export creates fresh records instead of failing on stale IDs.

### Upload and Row Caps

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

The import endpoint mirrors the export row cap. `ImportConfig.max_rows` defaults to 100,000 and is enforced before any record is created. The uploaded file is counted in a pre-pass, and a file holding more rows is rejected with an HTTP 400 error. Set `max_rows=None` to remove the limit entirely. Uploads are also capped at 10 MB by default via `ImportConfig.max_upload_size`.

### Header Matching

The wizard matches each file header against your field's `label` and then its `name`. A file containing the column `Name` and another containing `name` will both map correctly to a field named `name`. Unmatched columns are ignored, and fields missing a corresponding column receive `None`.

## File Fields

Views containing a storage-backed `FileField` or `ImageField` export data as a ZIP archive. This packaging ensures the actual file contents travel alongside the row data:

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

Exporting `ProductView` to CSV produces `export.zip` with the following structure:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

The `photo` column in `export.csv` contains the file's ZIP-relative path (`assets/<storage-name>/<key>`), keeping the CSV readable in standard spreadsheet software. The system fetches every referenced file from its storage backend and packages them within the `assets/` directory.

Import does not accept ZIP archives. `FileField` and `ImageField` are always excluded from import (`exclude_from_import=True` by default), so the `photo` column is ignored on upload. Re-import a plain data file and attach files through the create or edit forms instead.


## Writing a Custom Exporter

To create a custom exporter, subclass `BaseExporter` and implement the `generate` method. The base class automatically handles ZIP wrapping, file downloads, and response headers:

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

The `rows` data arrives pre-cleaned. The system replaces any `FileField` or `ImageField` value with its ZIP-relative path string beforehand, meaning your `generate` method never needs to handle file dictionaries separately. Register `MarkdownExporter()` in your `exporters` list to display it in the format dropdown.

## Writing a Custom Importer

To create a custom importer, subclass `BaseImporter` and implement the `parse` method as an asynchronous generator that yields one dictionary per row:

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

## What's Next

* **[File Storage](file-storage.md):** Configure the storage backends referenced in the export ZIP bundle.
* **[Security](security.md):** Learn about export row caps and import upload size limits.
* **[Actions](actions.md):** Add bulk and row actions alongside the export and import features.
