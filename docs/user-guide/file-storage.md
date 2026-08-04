---
title: File Storage
description: Manage file and image uploads in starlette-admin using LocalStorage or S3-compatible backend storage.
---

# File Storage

`FileField` and `ImageField` store uploaded files through a storage backend that you set with the field's `storage` parameter.

Create a storage backend once and reuse it across every field that keeps files in the same location.


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

When a user uploads a cover through the admin, the admin:

* saves the file to `uploads/covers/`
* stores a JSON metadata object in the `cover` column

The database never holds the file itself, a filesystem path, or binary data.


## What gets stored in the database

The admin represents a file upload as a serialized [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) object in the model field.

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

* `filename`: sanitized original filename, used for display
* `content_type`: MIME type detected at upload time
* `size`: file size in bytes
* `storage`: registered backend name, used to resolve the file location for URL generation and deletion
* `key`: storage-relative path or object key
* `url`: cached public URL

`LocalStorage` stores an empty `url` value, because URLs depend on the active request. `S3Storage` stores a public or presigned URL, depending on your configuration.

Whatever the backend, `FileField` regenerates the URL at render time with `storage.url()` instead of trusting the stored value.

`ImageField` adds `width` and `height`.

The admin sanitizes every filename with `secure_filename` before storing it: it strips path components and replaces characters outside `[A-Za-z0-9_.-]` with `_`. See [Security](security.md).


## Storage backends

### Local storage

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | required | Root directory for stored files. Created for you if it doesn't exist. |
| `name` | `str | None` | `"local"` | Registry name that identifies the backend. Must be unique when you use several instances. |

The admin serves files through this route:

```
/_files/{storage}/{path}
```

You don't need any extra static file configuration.

`LocalStorage.url()` builds URLs from the current request context, so the stored `url` field stays empty and is recomputed on demand.

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

Install the optional dependencies:

```bash
pip install starlette-admin[s3]
```

This installs `aiobotocore`.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `bucket` | `str` | required | S3 bucket name. |
| `prefix` | `str` | `"uploads/"` | Key prefix applied to every stored object. |
| `region` | `str` | `"us-east-1"` | AWS region used for signing and URL generation. |
| `access_key` and `secret_key` | `str | None` | `None` | Optional credentials. Falls back to the default AWS credential chain. |
| `public` | `bool` | `True` | When `True`, returns a public URL. When `False`, generates presigned URLs. |
| `expires` | `int` | `3600` | Expiration time for presigned URLs, in seconds. |
| `endpoint_url` | `str | None` | `None` | Custom S3-compatible endpoint, such as MinIO, R2, or B2. |
| `name` | `str | None` | `"s3"` | Registry name that identifies the backend. |

When you provide `endpoint_url`, the admin builds URLs as:

```
{endpoint_url}/{bucket}/{key}
```

instead of using the AWS virtual-hosted format.


!!! important
    File fields must map to a JSON-capable database column. The database holds only the metadata. The storage backend holds the file itself.


## Multiple files (`multiple=True`)

Set `multiple=True` on a `FileField` or `ImageField` to accept several uploads in one field.

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

The database stores a JSON list of `FileInfo` objects, and the admin processes each file independently through validation and storage.


!!! warning
    Saving the form replaces the whole file list with the submitted files. There's no way to add or remove a single file. For per-file lifecycle management, use an inline model with its own `FileField`.

!!! important
    `ListField(FileField(...))` isn't supported. Use `multiple=True` for simple collections, and inline models for structured file data.

## Validation

Validation runs in this order:

1. `accept`
2. `max_size`
3. custom `validators`

A custom validator is a callable that receives the request, the field, an `UploadFile`, and the full submitted form values. It must return `None` or raise `ValueError`.

The following example validates the actual file contents with the `filetype` library:

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

!!! important "Reset the file pointer"
    Always reset the file pointer with `seek(0)` before and after inspection, so the storage layer can read the full file.

!!! note
    Validators run per file, so with `multiple=True` each file is validated independently. `ImageField` applies its own image validation before any custom validator.


!!! tip "Best practices"
    Use `accept` and `max_size` for lightweight validation.

    Use custom validators when you need to inspect file contents or enforce application-specific rules.

    Don't rely on file extensions or `Content-Type` headers for security-sensitive validation. Inspect the content instead, with a library such as `filetype` or `python-magic`.


## File cleanup limitations

`starlette-admin` uploads files to the storage backend and writes `FileInfo` metadata to the database, but it doesn't clean up files after a failure or a deletion. Two behaviors follow from that:

* **Failed transactions:** If a database transaction rolls back after an upload finishes, the file stays in the storage backend. Storage writes have no rollback mechanism.
* **Deletions and updates:** Deleting a row or replacing a file removes the `FileInfo` reference from the database, but the old file stays in `LocalStorage` or `S3Storage`.

This design keeps the storage layer simple and stops application-level errors from triggering destructive operations. The tradeoff is that orphaned files accumulate. To keep storage from growing without bound, reconcile them yourself. A common pattern is a periodic background job that diffs the keys in your storage backend against the active `FileInfo` references in your database.

### Transactional alternative

If your application needs file storage operations to be transactional with database writes, use a library that ties file storage to the SQLAlchemy unit of work.

Instead of the field's `storage=` parameter, use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). It stores files as part of the ORM flush and rollback cycle, so a failed transaction or a row deletion undoes the matching file write. For a working example, see [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## What's next

* **[Fields](fields.md):** `FileField` and `ImageField` reference.
* **[Export & Import](export-import.md):** How files are included in export bundles.
* **[Security](security.md):** Automatic sanitization and validation behavior.
