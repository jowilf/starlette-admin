# Export & Import

Every list page allows users to export data to a file and import data from a file without requiring you to write custom routes.

## Overview

* Export data from any list view via the **Export** dropdown.
* Import data via the **Import** button.
* Support for CSV, JSON, Excel, PDF and custom formats.
* Full integration with filtering, sorting, and storage-backed fields.
* Zero custom endpoints required.

## Minimal Example

```python hl_lines="4 5 25 26"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.export import CsvExporter, ExcelExporter, JsonExporter
from starlette_admin.importers import CsvImporter, ExcelImporter

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
    exporters = [CsvExporter(), ExcelExporter(), JsonExporter()]
    importers = [CsvImporter(), ExcelImporter()]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ProductView` now displays an **Export** dropdown and an **Import** button in the list toolbar. These menus provide the exact formats listed in the `exporters` and `importers` lists.

## Enabling Export

The `exporters` attribute accepts a list of exporter *instances*. This design allows you to configure each format at the point of enablement:

```python hl_lines="1 5"
from starlette_admin.export import CsvExporter, ExcelExporter, JsonExporter


class ProductView(ModelView):
    exporters = [CsvExporter(), ExcelExporter(), JsonExporter()]
```

The default is `[CsvExporter(), JsonExporter()]`. CSV and JSON support ship with no extra dependencies. `ExcelExporter` requires `openpyxl` (`pip install starlette-admin[excel]`) and `PdfExporter` requires `reportlab` (`pip install starlette-admin[pdf]`). `ProductView` raises an error at startup if you include one of these exporters without installing the matching package.

Export functionality is active by default. The **Export** dropdown appears in the UI as long as the `exporters` list is non-empty. To restrict export access, override the `can_export(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

### Filter State is Preserved

The export link carries the list page's current `q`, `filter`, and `sort` query parameters. If you apply a search, filter, or column sort, the export action targets that exact view. The resulting file contains the filtered rows in the active sort order. Clear the filters first to export the entire dataset.

Every field listed in the `fields` attribute is included in the exported file, except those explicitly marked with `exclude_from_export=True` (see [Fields](fields.md)).

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

The `ExportConfig.max_rows` setting defaults to `100_000`. The cap applies to the number of rows the export would actually produce: the full filtered result set for a full export, or the rows on the requested page for a page-scoped export. When that count exceeds the limit, the export endpoint flashes an error message and redirects back to the list page instead of generating the file. This prevents broad, unfiltered exports on large tables from hanging the request. Set `max_rows=None` to remove the limit entirely.

You configure `ExportConfig` once on the `Admin` instance. See [Security](security.md%23export-limits) for details on the remaining options (`restrict_url_download`, `max_download_size`, `safe_download_url`).

## Enabling Import

Import functionality is enabled by registering importer instances:

```python hl_lines="1 5"
from starlette_admin.importers import CsvImporter, ExcelImporter


class ProductView(ModelView):
    importers = [CsvImporter(), ExcelImporter()]
```

Import functionality is active by default. The **Import** button appears in the UI as long as the `importers` list is non-empty. Out of the box, this defaults to `[CsvImporter(), JsonImporter()]`. To restrict import access, override the `can_import(request)` method:

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

Clicking the import button opens a modal that prompts the user to select a format, upload a file, and configure two settings:

* **Dry run (validate without saving):** Parses and validates every row without calling `create()`. The response reports the expected outcome, including parsed rows, skipped rows, and validation errors. No data is written to the database.
* **Skip primary key column:** Removes the primary key column from every row before validation. This prevents a backend that auto-generates primary keys from failing due to stale IDs contained in an export file. This feature is disabled by default. If your file includes an `id` column and your model requires it, leave this unchecked.

!!! note
The import endpoint strictly calls `create()` for each row and does not support upsert operations. Re-importing a file containing primary keys from a prior export will either create duplicate rows or fail validation if your backend rejects duplicate keys.


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

The import endpoint mirrors the export row cap. `ImportConfig.max_rows` defaults to `100_000` and is enforced before any record is created: the uploaded file is counted in a pre-pass, and a file holding more rows is rejected with an HTTP 400 error so no partial import happens. Set `max_rows=None` to remove the limit entirely. Uploads are also capped at 10 MB by default via `ImportConfig.max_upload_size`; see [Security](security.md%23import-limits) for details.

### CSV and Excel Formatting

The system expects the header row to match your field's `label` or its `name`. The import process checks incoming columns against both attributes. For example, a file containing the column `Name` and another containing `name` will both correctly map to a field named `name`. The importer ignores columns that do not match any field and assigns `None` to any fields missing a corresponding column in the file.

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

The `photo` column in `export.csv` contains the file's ZIP-relative path (`assets/<storage-name>/<key>`), keeping the CSV readable in standard spreadsheet software. The system fetches every referenced file from its storage backend (`LocalStorage`, `S3Storage`, or a [custom backend](../advanced/extension-points.md)) and packages them within the `assets/` directory.

Import does not accept ZIP archives. `FileField` and `ImageField` are always excluded from import (`exclude_from_import=True` by default), so the `photo` column in the example above is ignored on upload. Re-import a plain `.csv`/`.xlsx`/`.json` file and attach files through the create/edit forms instead.

## Writing a Custom Exporter

To create a custom exporter, subclass `BaseExporter` and implement the `generate` method. The base class automatically handles ZIP wrapping, file downloads, and response headers:

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField


class TsvExporter(BaseExporter):
    content_type = "text/tab-separated-values"
    extension = "tsv"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        header = "\t".join(f.label or f.name for f in fields)
        lines = [header]
        for row in rows:
            lines.append("\t".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

The `rows` data arrives pre-cleaned. The system replaces any `FileField` or `ImageField` value with its ZIP-relative path string beforehand, meaning your `generate` method never needs to handle file dictionaries separately. Register `TsvExporter()` in your `exporters` list to display it in the dropdown alongside the built-in options.

## Writing a Custom Importer

To create a custom importer, subclass `BaseImporter` and implement the `parse` method as an asynchronous generator that yields one dictionary per row:

```python
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext


class TsvImporter(BaseImporter):
    extension = "tsv"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        lines = ctx.content.decode("utf-8").splitlines()
        header = lines[0].split("\t")
        for line in lines[1:]:
            values = line.split("\t")
            yield dict(zip(header, values))
```


---

## What's Next

* **[File Storage](file-storage.md):** Configure the storage backends referenced in the export ZIP bundle.
* **[Security](security.md):** Learn about export row caps and import upload size limits.
* **[Actions](actions.md):** Add bulk and row actions alongside the export and import features.