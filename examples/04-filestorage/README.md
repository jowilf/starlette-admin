# 04: File Storage

A blog-style admin demonstrating image and document uploads with `LocalStorage`.

## What it shows

- `ImageField` for author avatars and article cover images, each backed by a dedicated `LocalStorage` instance
- `FileField` for document uploads with `accept`, `max_size`, and a custom `validators` function that inspects the file's magic bytes via [`filetype`](https://github.com/h2non/filetype.py) to prevent MIME-type spoofing
- Separate storage directories per field (`uploads/avatars`, `uploads/covers`, `uploads/documents`)
- File metadata stored as JSON columns in SQLite; binary files stay on disk

## Run

```bash
cd examples/04-filestorage
uv run app.py
```

Then open <http://localhost:8000/admin/>.

## File validation

The `validate_document_type` function reads the first 2 048 bytes of each upload and uses `filetype.guess()` to detect the true MIME type, rejecting anything that is not PDF, DOC, or DOCX regardless of the extension or `Content-Type` header declared by the browser.
