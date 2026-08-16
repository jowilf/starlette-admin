## Custom Backend (TinyDB)

This example shows how to implement a custom database backend by subclassing
`BaseModelView`. It uses [TinyDB](https://github.com/msiemens/tinydb), a
lightweight, document-oriented database stored as a single JSON file, to
demonstrate that starlette-admin works with any data source.

Key things demonstrated:

- **`BaseModelView`**: implement `find_all`, `count`, `find_by_pk`, `find_by_pks`, `create`, `edit`, `delete` for any storage backend.
- **Custom filters**: per-backend filter implementations wired through `FilterRegistry`; see [`filters.py`](filters.py).
- **File uploads**: `ImageField` (cover) and `FileField` (attachments) backed by `LocalStorage`; files land in `assets/` and are served through the admin's built-in `/admin/_files/local/{key}` route. Each file field is persisted as a JSON object (or list of objects for multi-file fields) with upload metadata; see [Storage format](#storage-format) below.
- **Nested fields**: `ListField(CollectionField(...))` for structured comments.

### Storage format

File and image fields are stored inline in the document as plain JSON objects. An `ImageField` adds `width` and `height`; a `FileField` omits them. Multi-file fields (`FileField(multiple=True)`) store a list of these objects.

**Single image (`cover`):**
```json
{
  "filename": "dog.jpg",
  "content_type": "image/jpeg",
  "size": 11615,
  "storage": "local",
  "key": "covers/dog.jpg",
  "url": "",
  "uploaded_at": "2026-06-29T07:03:20.573330+00:00",
  "width": 200,
  "height": 300,
  "extra": {}
}
```

**File list (`attachments`):**
```json
[
  {
    "filename": "dummy-pdf.pdf",
    "content_type": "application/pdf",
    "size": 13264,
    "storage": "local",
    "key": "attachments/dummy-pdf.pdf",
    "url": "",
    "uploaded_at": "2026-06-29T07:03:20.573919+00:00",
    "extra": {}
  }
]
```

The `key` is the path under `assets/` where the file is saved on disk, and is also the path segment used by the `/admin/files/local/{key}` serve route.

### Running

```shell
cd examples/advanced/03-custom-backend
uv run app.py
```

Then open <http://localhost:8000/admin/>.
