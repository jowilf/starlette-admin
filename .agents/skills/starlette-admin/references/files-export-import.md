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
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

    def can_export(self, request) -> bool:
        return request.state.admin_user.is_staff
```

- Formats are extension strings; default `["csv", "json"]`. Built-in: csv/tsv/json (core, no extra), yaml/xlsx/xls/ods/dbf/html/latex/jira/rst via tablib (`tablib[xlsx]`, `tablib[xls]`, `tablib[ods]`, `tablib[yaml]`; the rest need plain `tablib`), pdf via `starlette-admin[pdf]` (reportlab). Unknown formats or missing packages fail at startup.
- To override a format's defaults, pass an instance instead of the string, mixing freely: `exporters = [CsvExporter(delimiter=";"), "xlsx"]` (`CsvExporter` forwards kwargs to `csv.writer`; `TablibExporter(format, **kwargs)` forwards to `tablib.Dataset.export()`).
- Export is a built-in global action with its own toolbar button. The dialog offers: scope (selected rows, or current page when nothing is selected; "select all matching" exports every matching row), field checkboxes (all checked by default), format, and filename (defaults to the view key).
- Every scope honors the active `q`, `filter`, and `sort`: what the user sees is what exports.
- Fields with `exclude_from_export=True` are skipped and never appear in the dialog.
- Row cap: `Admin(..., export_config=ExportConfig(max_rows=50_000))`; default 100,000, checked per scope before fetching; over the cap flashes an error and redirects to the list page, `None` disables.
- Formula injection: escaping is off by default; `CsvExporter(escape_formulas=True)` or `TablibExporter("xlsx", escape_formulas=True)` prefixes `=`, `+`, `-`, `@` cells with a quote. Recommended whenever exported fields can contain user-supplied strings.
- Views with storage-backed file fields export a ZIP: the data file plus an `assets/<storage-name>/<key>` tree; the file column holds the ZIP-relative path.

Custom exporter: subclass `BaseExporter`, set `content_type` and `extension`, implement `async def generate(self, fields, rows) -> bytes`. File values arrive pre-replaced by ZIP-relative path strings.

## Import

```python
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

    def can_import(self, request) -> bool:
        return request.state.admin_user.is_admin
```

- Formats are extension strings; default `["csv", "json"]`. Built-in: csv/tsv/json/yaml/xlsx/xls/ods/dbf/html, same dependencies as export. Instances override defaults: `CsvImporter(delimiter=";")`, `TablibImporter(format, **kwargs)`.
- Import is a three-step wizard: upload (format, file, optional "Update existing records by primary key"), preview (full validation without writing: header mapping with per-column checkboxes, New/Update/Error counts, first 10 rows, error table), result. Nothing is written before the final confirmation; the browser re-posts the file each step.
- Upsert: with "update existing" checked, a row whose PK matches an existing record calls `edit()`, otherwise `create()`. Unchecked, every row is created.
- Unchecking the PK column in the preview mapping drops it, so auto-generating backends do not choke on stale ids (replaces the old skip-primary-key option).
- Header row matches on the field `label`, then `name`; unmatched columns are listed as ignored, missing ones become `None`.
- ZIP archives are not accepted; `FileField`/`ImageField` are always `exclude_from_import=True`.
- Upload cap: `Admin(..., import_config=ImportConfig(max_upload_size=5 * 1024 * 1024))`; default 10 MB.

Custom importer: subclass `BaseImporter`, set `extension`, implement `async def parse(self, ctx: ImportContext)` as an async generator yielding one dict per row (`ctx.content` holds the raw bytes).
