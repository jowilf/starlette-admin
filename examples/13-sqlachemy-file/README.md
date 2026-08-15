This example shows how to use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file) to handle file uploads at the **SQLAlchemy model layer**, without relying on starlette-admin's own file-management abstractions.

File fields (`FileField`, `ImageField`) are declared directly on the models. starlette-admin detects them automatically and renders the appropriate upload widgets; all storage logic lives in sqlalchemy-file and [apache-libcloud](https://github.com/apache/libcloud).

**Models**

| Model | Fields |
|-------|--------|
| `Author` | `avatar`: single image, max 200 KB, 50×50 thumbnail |
| `Book` | `cover`: single image, max 1 MB; `document`: PDF/Word only, max 5 MB |
| `Dump` | `multiple_images`, `multiple_files`: multiple-upload fields, max 100 KB each |

Local storage is used by default. Switching to S3, MinIO, or any other provider supported by apache-libcloud requires only changing the driver in `configure_storage()`.

## Run

```shell
# from the repo root
cd examples/13-sqlachemy-file
uv run app.py
```

Then open http://localhost:8000/admin/.

Uploaded files are stored under `upload/` relative to the working directory.
