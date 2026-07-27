# File Storage

`FileField` and `ImageField` store uploaded files through a storage backend configured via the field's `storage` parameter.

A storage backend is created once and reused across all fields that should persist files in the same location.


## Minimal example

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

Uploading a cover through the admin:

* saves the file to `uploads/covers/`
* stores a JSON metadata object in the `cover` column

The database never stores the file itself, a filesystem path, or binary data.


## What gets stored in the database

File uploads are represented by a serialized [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) object stored in the model field.

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename`: sanitized original filename used for display
* `content_type`: MIME type detected at upload time
* `size`: file size in bytes
* `storage`: registered backend name used to resolve the file location for URL generation and deletion
* `key`: storage-relative path or object key
* `url`: cached public URL

`LocalStorage` stores an empty `url` value because URLs depend on the active request. `S3Storage` may store a public or pre-signed URL depending on configuration.

Regardless of the backend, `FileField` regenerates the URL at render time using `storage.url()` rather than relying on stored values.

`ImageField` adds `width` and `height`.

All filenames are sanitized using `secure_filename` before storage. Path components are removed and characters outside `[A-Za-z0-9_.-]` are replaced with `_`. See [Security](security.md) for details.


## Storage backends

### Local storage

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parameter  | Type | Default | Description |                                                                                              |
| ---------- | ---- | ------- | ----------- | -------------------------------------------------------------------------------------------- |
| `base_dir` | `str | Path`   | required    | Root directory for stored files. Created automatically if it does not exist.                 |
| `name`     | `str | None`   | `"local"`   | Registry name used to identify the backend. Must be unique when multiple instances are used. |

Files are served through the admin route:

```
/_files/{storage}/{path}
```

No additional static file configuration is required.

`LocalStorage.url()` constructs URLs dynamically from the current request context, so the stored `url` field is always empty and recomputed on demand.

!!! note
    See [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) for a code example.

### Amazon S3 storage

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

Install optional dependencies:

```bash
pip install starlette-admin[s3]
```

This installs `aiobotocore`.

| Parameter                   | Type   | Default       | Description                                                            |                                                                      |
| --------------------------- | ------ | ------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `bucket`                    | `str`  | required      | S3 bucket name                                                         |                                                                      |
| `prefix`                    | `str`  | `"uploads/"`  | Key prefix applied to all stored objects                               |                                                                      |
| `region`                    | `str`  | `"us-east-1"` | AWS region used for signing and URL generation                         |                                                                      |
| `access_key` / `secret_key` | `str   | None`         | `None`                                                                 | Optional credentials. Falls back to the default AWS credential chain |
| `public`                    | `bool` | `True`        | If `True`, returns a public URL. If `False`, generates pre-signed URLs |                                                                      |
| `expires`                   | `int`  | `3600`        | Expiration time for pre-signed URLs in seconds                         |                                                                      |
| `endpoint_url`              | `str   | None`         | `None`                                                                 | Custom S3-compatible endpoint (MinIO, R2, B2, etc.)                  |
| `name`                      | `str   | None`         | `"s3"`                                                                 | Registry name used to identify the backend                           |

When `endpoint_url` is provided, URLs are constructed as:

```
{endpoint_url}/{bucket}/{key}
```

instead of the AWS virtual-hosted format.


!!! warning
    File fields must map to a JSON-capable database column. Only metadata is stored in the database. The storage backend stores the file itself.


## Multiple files (`multiple=True`)

Set `multiple=True` on a `FileField` or `ImageField` to allow multiple uploads in a single field.

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

The database stores a JSON list of `FileInfo` objects.

Each file is processed independently through validation and storage.


!!! warning
    Saving the form replaces the entire file list with the submitted files. Individual add or remove operations are not supported.
    ```
    For per-file lifecycle management, use an inline model with its own `FileField`.
    ```

!!! important

    `ListField(FileField(...))` is not supported.
    Use `multiple=True` for simple collections. Use inline models for structured file data.

## Validation

Validation runs in the following order:

1. `accept`
2. `max_size`
3. custom `validators`

Custom validators are callables that receive the request, the field, an `UploadFile`, and the full submitted form values. They must either return `None` or raise `ValueError`.

The following example validates the actual file contents using the `filetype` library:

```python
import filetype
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import BaseField

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile, form_values: dict
) -> None:
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)

    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )
```

!!! important "File Pointer Reset"
    Always reset the file pointer with `seek(0)` before and after inspection so the storage layer can read the full file.

!!! note
    Validators are executed per file. For `multiple=True`, each file is validated independently.
    `ImageField` applies its own image validation before any custom validators.


!!! tip "Best Practices"
    Use `accept` and `max_size` for lightweight validation.

    Use custom validators when you need to inspect file contents or enforce application-specific rules.

    **Do not** rely on file extensions or `Content-Type` headers for security-sensitive validation. Use a content-based inspection library such as `filetype` or `python-magic`.


## File Cleanup Limitations

While `starlette-admin` uploads files to the storage backend and writes `FileInfo` metadata to the database, it does not automatically execute cleanup operations during failures or deletions. Specifically, you should be aware of the following behaviors:

* **Failed Transactions:** If a database transaction rolls back after an upload completes, the file remains in the storage backend. There is no automatic rollback mechanism for storage writes.
* **Deletions and Updates:** Deleting a row or replacing an existing file removes the `FileInfo` reference from the database. However, the legacy file is not deleted from the underlying `LocalStorage` or `S3Storage`.

This design keeps the storage layer simple and prevents application-level errors from triggering destructive operations. The tradeoff is that orphaned files will accumulate over time. To prevent unbounded storage growth, you must reconcile these files manually. A common pattern is to implement a periodic background job that diffs the actual keys in your storage backend against the active `FileInfo` references in your database.

### Transactional Alternative

If your application requires file storage operations to be strictly transactional with database writes, you should use a library that ties file storage to the SQLAlchemy unit of work.

Instead of relying on the `storage=` parameter on the field, you can use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). This library stores files as part of the ORM flush and rollback cycle, ensuring that a failed transaction or a row deletion automatically undoes the corresponding file write. For a working example, refer to [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## What's next

* **[Fields](fields.md):** `FileField` and `ImageField` reference.
* **[Export & Import](export-import.md):** How files are included in export bundles.
* **[Security](security.md):** Automatic sanitization and validation behavior.
