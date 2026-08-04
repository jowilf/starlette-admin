---
title: Security
description: Discover built-in security features in starlette-admin including CSRF protection, file upload safety, and access control.
---

# Security

`starlette-admin` includes safeguards for the risks that come with running an administration panel. Protection against cross-site request forgery (CSRF) and limits on export and import payload sizes are active as soon as you instantiate the `Admin` class.

These defaults harden the interface against common attacks, but they don't replace standard deployment security. You're still responsible for transport layer security (HTTPS/TLS), network access control, user authentication (see [Authentication](auth.md)), dependency updates, and security reviews. This page covers the automatic protections, the ones you configure, and the `secret_key` setting you need in production.

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

Even with no security parameters, the admin instance defends against several common vulnerabilities:

* **CSRF protection:** Active on every form and jQuery AJAX call, including row actions and confirmation dialogs.
* **Flash messages:** Carried in a signed cookie, so you don't need `SessionMiddleware`.
* **Filename sanitization:** Applied to every file upload that goes through a storage backend.
* **Image content verification:** Validates `ImageField` uploads at the byte level with Pillow, when it's installed.
* **Export limits:** Capped at 100,000 rows per request, to prevent resource exhaustion and denial of service.
* **Import limits:** Capped at 10 MB per request, to limit memory exhaustion.

One more protection is available, but off by default: escaping that prevents spreadsheet formula injection in CSV and spreadsheet exports (XLSX, XLS, ODS). See [Formula injection](#formula-injection).

The sections below explain these protections and how to adjust the thresholds you control.

## The secret key

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

The `secret_key` is the cryptographic root for signing two cookies: the CSRF token and the flash-message cookie. Both use [itsdangerous](https://itsdangerous.palletsprojects.com/), so clients can read the cookies but can't forge or tamper with the payload without the key.

!!! warning "Always set an explicit secret key in production"
    If you omit `secret_key`, the `Admin` instance generates a random key at startup and emits a `UserWarning`. That's fine for a local demo, but it breaks in multi-worker deployments. When you run several workers, such as `uvicorn --workers 4`, Gunicorn, or multiple containers, each process generates its own key. A CSRF token signed by the worker that served the form then fails validation when a different worker handles the submission, which produces invalid CSRF token errors on a seemingly random fraction of requests. Set `secret_key` explicitly before you scale beyond a single process.

## CSRF protection

`CSRFMiddleware` uses a signed double-submit cookie pattern to prevent cross-site request forgery. It issues a `starlette_admin_csrftoken` cookie on safe HTTP methods (`GET`, `HEAD`, `OPTIONS`, and `TRACE`). For mutating requests, it validates that cookie against either an `X-CSRFToken` header or a `csrftoken` hidden form field.

Every built-in admin template (`create`, `edit`, and `login`) renders the hidden field for you:

```jinja
{{ csrf_input(request) }}

```

The bundled JavaScript also attaches the header to every jQuery AJAX call, so row actions and other asynchronous interactions are protected without extra code. Call `csrf_input(request)` yourself only when you build custom forms outside the default templates. See [Custom Views](custom-views.md).

## File uploads

Every upload that goes through a [storage](file-storage.md) backend is sanitized with `secure_filename`. Directory traversal path components are stripped, and characters outside `[A-Za-z0-9_.-]` become underscores (`_`). You can't turn this off.

Set content-type and size restrictions per field with `accept` and `max_size`:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Without them, a `FileField` accepts any file type and size. `ImageField` is the exception: it defaults to `accept="image/*"`, and when Pillow is installed it prepends a validator that opens the upload with `PIL.Image` to confirm the bytes decode as an image, instead of trusting browser-supplied metadata.

!!! important "Enforce request size limits at the web server level"
    Don't rely on `max_size` alone. That application-level check runs only after the server has received the full request payload. To prevent denial-of-service (DoS) attacks, cap the request body size in your web server configuration, such as `client_max_body_size` in NGINX or the equivalent setting on your load balancer.

!!! warning "File extensions and Content-Type headers can be spoofed"
    The `accept` attribute relies on the filename extension and the browser-provided `Content-Type` header, and an attacker can spoof both. A file that looks like `invoice.pdf` can carry an executable payload.

    For non-image files, pair `accept` with a custom validator that inspects the file's magic bytes. Libraries such as [`filetype`](https://github.com/h2non/filetype.py) and [`python-magic`](https://github.com/ahupp/python-magic) verify the true file format:

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

    Apply the validator with `FileField(..., validators=[validate_document_type])`. For a full implementation, see [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

## Export limits

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribute | Default | Description |
| --- | --- | --- |
| `max_rows` | `100_000` | Maximum number of rows per export request. Going over the limit flashes an error and returns the user to the list view. Set to `None` to remove the limit. |
| `restrict_url_download` | `True` | Applies to URL-only file references. Restricts the export ZIP to files whose origin matches the admin's `base_url`. |
| `max_download_size` | `20 MB` | Maximum size for a URL-only download packaged into an export ZIP. Larger files are skipped and logged with a warning. |
| `safe_download_url` | `None` | A custom callback with the signature `(url, request) -> str`. |

For how the ZIP bundle is built, see [Export & Import](export-import.md).

### Formula injection

Spreadsheet software treats a cell value that starts with `=`, `+`, `-`, or `@` as a formula. If an untrusted user saves a payload such as `=HYPERLINK(...)` into an exported field, the spreadsheet application runs it when an administrator opens the file. This is known as CSV injection, or formula injection.

Because exported values are written exactly as they're stored in the database, formula escaping is **off by default**. The CSV exporter and the Tablib spreadsheet exporters (`xlsx`, `xls`, and `ods`) all accept an `escape_formulas` parameter. When you turn it on, any string that starts with a trigger character gets a leading single quote (`'`), which forces the application to render the value as plain text.

!!! warning "Turn on formula escaping for user-supplied data"
    If any non-administrator account can write data into an exported field, set `escape_formulas=True`. Without it, attacker-controlled values can run system commands or exfiltrate data when someone opens the file locally.

To turn on escaping, replace the format string with an explicit exporter instance:

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter, TablibExporter


class ProductView(ModelView):
    exporters = [
        CsvExporter(escape_formulas=True),
        TablibExporter("xlsx", escape_formulas=True),
        "json",
    ]
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
| `max_upload_size` | `10 MB` | Checked as soon as the request arrives, before any parsing. |
| `max_rows` | `100_000` | Maximum number of rows per import request. The admin counts the payload in a pre-pass and rejects a larger file with an HTTP 400 response before it creates any database record. Set to `None` to remove the limit. |

Import rejects ZIP archives outright, which removes the risk of ZIP-bomb attacks on this endpoint. `FileField` and `ImageField` are also excluded from bulk imports, because `exclude_from_import=True` by default, so users attach files one at a time through the create or edit forms.

## What this page doesn't cover

The built-in protections address risks inside the admin codebase. They don't secure your architecture as a whole. These operational measures are outside the scope of `starlette-admin` and remain yours:

* **Transport security:** Serve the admin over HTTPS. The CSRF and flash cookies are signed, but not encrypted, so anyone who intercepts plain HTTP traffic can read them.
* **Authentication and authorization:** The `Admin` instance is public until you attach an `AuthProvider`. Without one, every endpoint and route is open. See [Authentication](auth.md).
* **Network exposure:** If the admin panel doesn't need public access, put it behind a firewall, a VPN, or an IP allowlist.
* **Dependency hygiene:** Watch security advisories and keep `starlette-admin`, Starlette, your ORM driver, and the rest of your dependencies up to date.
* **Post-authentication actions:** CSRF and upload validation don't limit what a signed-in user can do. Granular access control comes entirely from the permission checks you write in `is_accessible`, `can_create`, `can_edit`, and `can_delete`. See [Authentication](auth.md).

Treat this page as a guide to configuring the admin package, not as a checklist for securing your whole production deployment.

---

## What's next

* **[Export & Import](export-import.md):** The export dialog, the import preview lifecycle, and the ZIP bundle layout.
* **[File Storage](file-storage.md):** Patterns for configuring storage backends for `FileField` and `ImageField`.
* **[Authentication](auth.md):** How `secret_key` gates sign-in sessions and CSRF checks once you add an auth provider.
