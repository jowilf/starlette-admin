# Security

starlette-admin provides built-in protections for the risks specific to running an admin panel. Features like Cross-Site Request Forgery (CSRF) mitigation and export/import rate limiting are wired up the moment you construct `Admin`.

While these defaults harden the admin against common attack vectors, they do not replace standard deployment security. Transport security (HTTPS/TLS), network access control, user authentication ([Authentication](auth.md)), dependency updates, and comprehensive security reviews remain your responsibility. Read this page as a set of security best practices: what is handled automatically, what you should configure, and the critical `secret_key` setting required before deployment.

## What you get automatically

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

Even without passing any security-specific arguments, this admin instance automatically guards against several common issues:

* **CSRF protection:** Enabled on every form and jQuery AJAX call (including row actions and confirm dialogs).
* **Flash messages:** Delivered through a signed cookie, meaning no `SessionMiddleware` is required.
* **Filename sanitization:** Applied to every file upload passing through a storage backend.
* **Image content verification:** Applied to `ImageField` uploads when Pillow is installed.
* **Export limits:** Capped at 100,000 rows per request.
* **Formula escaping:** Applied to CSV and Excel exports to neutralize spreadsheet formula injection.
* **Import limits:** Capped at 10 MB per request.

The rest of this page explains each of these protections and how to adjust the configurable ones.

## The secret key

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

The `secret_key` signs two cookies: the CSRF token and the flash-message cookie. Both use [itsdangerous](https://itsdangerous.palletsprojects.com/), meaning a client can read the cookie but cannot forge or tamper with its contents without the key.

!!! warning 
    If you do not pass a `secret_key`, `Admin` generates a random one at startup and emits a `UserWarning`. While convenient for a quick demo, each **worker process** generates its own key independently. If you run more than one worker (`uvicorn --workers 4`, gunicorn, or multiple containers) without an explicit `secret_key`, a CSRF token signed by the worker that served the form will not validate on the worker that receives the submission. The request will fail with an invalid CSRF token error on a seemingly random fraction of submissions. Always set `secret_key` explicitly before running more than one process.

## CSRF protection

`CSRFMiddleware` implements a signed double-submit cookie, which protects against most types of CSRF attacks. It sets a `starlette_admin_csrftoken` cookie on safe responses (`GET`, `HEAD`, `OPTIONS`, `TRACE`), and on every mutating request, it compares that cookie against either an `X-CSRFToken` header or a `csrftoken` hidden form field. All three admin form templates (`create`, `edit`, `login`) render the hidden field automatically:

```jinja
{{ csrf_input(request) }}

```

The bundled JavaScript attaches the header to every jQuery AJAX call automatically, ensuring row actions and other AJAX-driven interactions are covered without extra code. You only need to call `csrf_input(request)` directly if you add a custom form outside the admin's own templates. For more details, see [Custom Views](custom-views.md).


## File uploads

Every upload that goes through a [storage](file-storage.md) backend has its filename sanitized with `secure_filename`. Path components are stripped, and anything outside `[A-Za-z0-9_.-]` is collapsed to `_` regardless of field configuration. This protection is not optional.

Content-type and size restrictions are opt-in per field via `accept` and `max_size`:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB
```

If you leave both unset, a plain `FileField` accepts any file of any size since `accept` and `max_size` default to `None`. `ImageField` is the exception. It defaults to `accept="image/*"` and, when Pillow is installed, prepends a validator that opens the upload with `PIL.Image` to verify it decodes as a real image instead of trusting the filename extension or the browser-supplied content type.

!!! important
    Do not rely on `max_size` alone: it is checked only after the request has already reached the application. It is strongly advised that you limit the maximum request body size in your web server configuration (for example `client_max_body_size` in nginx, or the equivalent on your load balancer) to prevent denial-of-service (DoS) attacks.


!!! warning 
    The `accept` attribute only checks the filename extension and the `Content-Type` header sent by the browser. Both of these values are client-supplied and trivial to spoof. A file named `invoice.pdf` with `Content-Type: application/pdf` can still contain anything, including an executable or a malicious script.
    For non-image uploads, pair `accept` with a custom `validators` callable that inspects the file's magic bytes using a library like [`filetype`](https://github.com/h2non/filetype.py) or [`python-magic`](https://github.com/ahupp/python-magic). You can then raise a `ValueError` when the detected type does not match your allowed formats:
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
        request: Request, field: BaseField, upload: UploadFile
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

  
  Pass this validator to your field using `FileField(..., validators=[validate_document_type])`. For a complete working setup, refer to the [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) directory.


## Export limits

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribute | Default | Description |
| --- | --- | --- |
| `max_rows` | `100_000` | Rows allowed per export request. Above this limit, the endpoint flashes an error and redirects back to the list page. Set to `None` to disable the cap. |
| `restrict_url_download` | `True` | For URL-only file references, this limits the export ZIP to files whose origin matches the admin's `base_url`. |
| `max_download_size` | `20 MB` | Per-file cap on URL-only downloads pulled into an export ZIP. Oversized files are skipped with a warning. |
| `safe_download_url` | `None` | Callback `(url, request) -> str` |

See [Export & Import](export-import.md) for details on how the ZIP bundle is built.

### Formula injection

Spreadsheet applications treat cell values starting with `=`, `+`, `-`, or `@` as formulas. A record containing a value like `=HYPERLINK(...)`, entered by any user who can write to an exported field, executes when someone opens the exported file in Excel or LibreOffice. This is known as CSV (or formula) injection.

Both spreadsheet exporters neutralize it by default: `CsvExporter` and `ExcelExporter` prefix any string cell starting with a trigger character with a single quote, so the value displays as text instead of executing. Disable it per exporter only if you trust everyone who can write to the exported data:

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter


class ProductView(ModelView):
    exporters = [CsvExporter(escape_formulas=False)]
```

## Import limits

```python
from starlette_admin.importers import ImportConfig

admin = Admin(
    engine,
    title="My Admin",
    import_config=ImportConfig(
        max_upload_size=5 * 1024 * 1024,
        max_rows=50_000,
    ),
)
```

| Attribute | Default | Description |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | Checked before any parsing begins. |
| `max_rows` | `100_000` | Rows allowed per import request. The file is counted in a pre-pass, so an oversized file is rejected with HTTP 400 before any record is created. Set to `None` to disable the cap. |

Import does not accept ZIP archives, so there's no ZIP-bomb surface to guard against on this endpoint. `FileField` and `ImageField` are always excluded from import (`exclude_from_import=True` by default); attach files through the create/edit forms instead.

## What this page doesn't cover

The protections above reduce risk in the admin's own code, but they do not secure your deployment as a whole. The following areas fall outside the scope of starlette-admin and remain your responsibility:

* **Transport security:** Serve the admin over HTTPS. CSRF and flash cookies are signed but not encrypted in transit, meaning anyone on the network path can read them over plain HTTP.
* **Authentication and authorization:** `Admin` has no login screen until you attach an `AuthProvider` (see [Authentication](auth.md)). Without one, every route is open to anyone who can reach it.
* **Network exposure:** Place the admin behind a firewall, VPN, or IP allowlist if it does not need to be public. Restricting access to the login page limits potential attackers.
* **Dependency hygiene:** Keep starlette-admin, Starlette, and your ORM driver up to date, and monitor their security advisories.
* **Post-authentication actions:** CSRF and upload checks do not limit what an authenticated user can do once logged in. That is governed by the permission checks you implement in `is_accessible`, `can_create`, `can_edit`, and `can_delete` (see [Authentication](auth.md)).

Treat this page as best practices for the admin itself, not as a complete checklist for securing your deployment in isolation.

---

## What's next

* **[Export & Import](export-import.md):** The export/import UI, dry-run mode, and the ZIP bundle format.
* **[File Storage](file-storage.md):** Configuring storage backends for `FileField` and `ImageField`.
* **[Authentication](auth.md):** How `secret_key` gates login and CSRF when an auth provider is set.