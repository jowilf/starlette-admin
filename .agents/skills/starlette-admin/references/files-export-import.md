# File storage, export, and import

## File storage

`FileField` and `ImageField` with a `storage=` backend save the upload and store a JSON `FileInfo` object in the column (`filename`, `content_type`, `size`, `storage`, `key`, `url`; `ImageField` adds `width`/`height` when Pillow is installed). The column MUST be JSON-capable; the file itself never enters the database.

```python
from starlette_admin import ImageField
from starlette_admin.storage import LocalStorage

covers = LocalStorage(base_dir="uploads/covers", name="covers")  # name must be unique


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=covers, upload_folder="covers",
                   max_size=5 * 1024 * 1024),
    ]
```

Backends:

- `LocalStorage(base_dir=, name=)`: serves files at `/_files/{storage}/{path}`, no static config needed. URLs are computed per request.
- `S3Storage(bucket=, prefix=, region=, access_key=, secret_key=, public=, expires=, endpoint_url=, name=)`: `pip install starlette-admin[s3]`. `public=False` generates pre-signed URLs; `endpoint_url` supports MinIO/R2/B2.
- Custom: subclass `BaseStorage`; instances register by their `name`.

Multiple files: `multiple=True` stores a JSON list of `FileInfo`. Saving replaces the whole list; per-file management needs an inline child model. `ListField(FileField(...))` is not supported.

Validation runs once per uploaded file: `max_size`, then `accept`, then custom `validators` (callables `(request, field, upload)` raising `ValueError`; see [fields.md](fields.md)). `accept` checks only the client-supplied extension/content-type; for security, inspect magic bytes (with `filetype` or `python-magic`) in a validator and `seek(0)` before and after reading. `ImageField` defaults to `accept="image/*"` and prepends the `valid_image()` validator, which verifies the upload decodes as a real image via Pillow. Filenames are always sanitized with `secure_filename`.

Cleanup limitations: a rolled-back transaction leaves the uploaded file in storage; deleting or replacing a row leaves the old file behind. Reconcile orphans with a periodic job, or use sqlalchemy-file for transactional storage tied to the SQLAlchemy unit of work (see below).

### ORM-native file columns

- MongoEngine `FileField`/`ImageField` work out of the box via GridFS: list the field by name, no `storage=`.
- SQLAlchemy via sqlalchemy-file: declare its `FileField`/`ImageField` column types, configure `StorageManager` (Libcloud containers); starlette-admin detects them, renders the field, serves the files, and uploads participate in the session transaction (rollback discards the file). Example: `examples/13-sqlachemy-file`.
- A `FileField` with no `storage=` hands your backend a raw `(UploadFile | list | None, delete_flag)` tuple on create/edit and expects `url`/`filename`/`content_type` for display; this is the contract the ORM integrations plug into.

Runnable example: `examples/04-filestorage`.

## Export

```python
from starlette_admin.export import CsvExporter, ExcelExporter, JsonExporter, PdfExporter


class ProductView(ModelView):
    exporters = [CsvExporter(), ExcelExporter(), JsonExporter()]

    def can_export(self, request) -> bool:
        return request.state.admin_user.is_staff
```

- Default: `[CsvExporter(), JsonExporter()]`. Excel needs `starlette-admin[excel]` (openpyxl), PDF needs `starlette-admin[pdf]` (reportlab); missing packages fail at startup.
- Exports preserve the active `q`, `filter`, and `sort`: what the user sees is what exports.
- Fields with `exclude_from_export=True` are skipped.
- Row cap: `Admin(..., export_config=ExportConfig(max_rows=50_000))`; default 100,000, over the cap returns HTTP 400, `None` disables.
- Formula injection: CSV/Excel exporters prefix `=`, `+`, `-`, `@` cells with a quote by default; `CsvExporter(escape_formulas=False)` disables.
- Views with storage-backed file fields export a ZIP: the data file plus an `assets/<storage-name>/<key>` tree; the file column holds the ZIP-relative path.

Custom exporter: subclass `BaseExporter`, set `content_type` and `extension`, implement `async def generate(self, fields, rows) -> bytes`. File values arrive pre-replaced by ZIP-relative path strings.

## Import

```python
from starlette_admin.importers import CsvImporter, ExcelImporter, JsonImporter


class ProductView(ModelView):
    importers = [CsvImporter(), ExcelImporter()]

    def can_import(self, request) -> bool:
        return request.state.admin_user.is_admin
```

- Default: `[CsvImporter(), JsonImporter()]`.
- The upload modal offers dry-run (validate everything, write nothing, report per-row errors) and skip-primary-key (drop the PK column so auto-generating backends do not choke on stale ids).
- Import strictly calls `create()` per row; there is no upsert. Header row matches on the field `label` or `name`; unknown columns are ignored, missing ones become `None`.
- ZIP archives are not accepted; `FileField`/`ImageField` are always `exclude_from_import=True`.
- Upload cap: `Admin(..., import_config=ImportConfig(max_upload_size=5 * 1024 * 1024))`; default 10 MB.

Custom importer: subclass `BaseImporter`, set `extension`, implement `async def parse(self, ctx: ImportContext)` as an async generator yielding one dict per row (`ctx.content` holds the raw bytes).
