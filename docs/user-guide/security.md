---
title: Security
description: Discover built-in security features in starlette-admin including CSRF protection, file upload safety, and access control.
---

# Security

Starlette-admin includes built-in safeguards to mitigate the specific risks associated with running an administration panel. Protections against Cross-Site Request Forgery (CSRF) and strict limits on export and import payload sizes are active as soon as you instantiate the `Admin` class.

While these default behaviors harden the interface against common attack vectors, they do not replace standard deployment security. You remain responsible for transport layer security (HTTPS/TLS), network access control, user authentication ([Authentication](auth.md)), dependency updates, and comprehensive security reviews. This document details the automated security features, configurable protections, and the critical `secret_key` setting required for production deployments.

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

Even without providing specific security parameters, the admin instance automatically defends against several common vulnerabilities:

* **CSRF protection:** Active on every form and jQuery AJAX call, including row actions and confirmation dialogs.
* **Flash messages:** Secured via a signed cookie, completely eliminating the need for `SessionMiddleware`.
* **Filename sanitization:** Enforced on every file upload processed through a storage backend.
* **Image content verification:** Validates `ImageField` uploads at the byte level using Pillow, if installed.
* **Export limits:** Capped at 100,000 rows per request to prevent resource exhaustion and denial of service.
* **Import limits:** Restricted to 10 MB per request to mitigate memory overflow risks.

An additional, opt-in protection is available to prevent spreadsheet formula injection during CSV and spreadsheet (XLSX, XLS, ODS) exports. Refer to the [Formula injection](%23formula-injection) section for configuration details.

The following sections explain these protections and how to adjust the configurable thresholds.

## The secret key

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

The `secret_key` acts as the cryptographic root for signing two critical cookies: the CSRF token and the flash-message cookie. Because these leverage [itsdangerous](https://itsdangerous.palletsprojects.com/), clients can read the cookies but cannot forge or tamper with the payload without the key.

!!! warning "Always configure an explicit secret key in production environments"
    If you omit the `secret_key`, the `Admin` instance generates a random key at startup and emits a `UserWarning`. While this is acceptable for local demonstrations, it causes failures in multi-worker environments. If you run multiple workers (such as `uvicorn --workers 4`, Gunicorn, or multiple containers) without an explicit `secret_key`, each process generates its own independent key. Consequently, a CSRF token signed by the worker that served the form will fail validation if a different worker handles the form submission. This results in invalid CSRF token errors on a seemingly random fraction of requests. Always set the `secret_key` explicitly before scaling beyond a single process.

## CSRF protection

The `CSRFMiddleware` utilizes a signed double-submit cookie pattern to prevent Cross-Site Request Forgery. It issues a `starlette_admin_csrftoken` cookie on safe HTTP methods (`GET`, `HEAD`, `OPTIONS`, `TRACE`). For mutating requests, it validates this cookie against either an `X-CSRFToken` header or a `csrftoken` hidden form field.

All built-in admin templates (`create`, `edit`, and `login`) automatically render the required hidden field:

```jinja
{{ csrf_input(request) }}

```

Additionally, the bundled JavaScript automatically attaches the necessary header to all jQuery AJAX calls. This guarantees that row actions and asynchronous interactions are protected without requiring boilerplate code. You only need to invoke `csrf_input(request)` manually if you are building custom forms outside the default templates. For further instructions, consult the [Custom Views](custom-views.md) documentation.

## File uploads

All uploads routed through a [storage](file-storage.md) backend undergo mandatory filename sanitization using `secure_filename`. Directory traversal path components are stripped, and any characters outside the standard alphanumeric set (`[A-Za-z0-9_.-]`) are replaced with underscores (`_`). This foundational protection cannot be disabled.

You can configure content-type and size restrictions on a per-field basis using `accept` and `max_size`:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

If omitted, a standard `FileField` accepts any file type and size. The `ImageField` is a notable exception: it defaults to `accept="image/*"` and, when Pillow is installed, automatically prepends a validator. This validator opens the upload using `PIL.Image` to confirm it decodes as a valid image rather than relying on browser-supplied metadata.

!!! important "Enforce request size limits at the web server level"
    Do not rely exclusively on the `max_size` parameter. This application-level check is evaluated only after the server has received the full request payload. To effectively prevent denial-of-service (DoS) attacks, restrict the maximum request body size directly in your web server configuration (such as `client_max_body_size` in NGINX or the equivalent setting on your load balancer).

!!! warning "File extensions and Content-Type headers can be spoofed"
    The `accept` attribute relies entirely on the filename extension and the browser-provided `Content-Type` header, both of which are trivially spoofed by malicious actors. A file disguised as `invoice.pdf` could contain an executable payload.

    For non-image files, pair the `accept` attribute with a custom validator that inspects the file's magic bytes. Libraries like [`filetype`](https://github.com/h2non/filetype.py) or [`python-magic`](https://github.com/ahupp/python-magic) allow you to verify the true file format:

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

    Apply this validator to your field using `FileField(..., validators=[validate_document_type])`. For a comprehensive implementation, refer to the [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) directory.

## Export limits

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribute | Default | Description |
| --- | --- | --- |
| `max_rows` | `100_000` | The maximum number of rows permitted per export request. Exceeding this threshold flashes an error and redirects the user back to the list view. Set to `None` to disable the limit. |
| `restrict_url_download` | `True` | Applies to URL-only file references. Restricts the resulting export ZIP to include only files whose origin matches the admin interface's `base_url`. |
| `max_download_size` | `20 MB` | The maximum file size limit for URL-only downloads packaged into an export ZIP. Oversized files are skipped and logged with a warning. |
| `safe_download_url` | `None` | A custom callback function signature: `(url, request) -> str`. |

Refer to the [Export & Import](export-import.md) documentation for a technical breakdown of how the ZIP bundle is constructed.

### Formula injection

Spreadsheet software interprets cell values beginning with `=`, `+`, `-`, or `@` as executable formulas. If a malicious payload like `=HYPERLINK(...)` is saved into an exported field by an untrusted user, the spreadsheet application will execute it when an administrator opens the file. This vulnerability is commonly referred to as CSV injection or formula injection.

Because exported values are written exactly as they are stored in the database, formula escaping is **disabled by default**. Both the CSV exporter and the Tablib spreadsheet exporters (`xlsx`, `xls`, `ods`) accept an `escape_formulas` parameter. When enabled, any string starting with a trigger character is prefixed with a single quote (`'`), forcing the application to render the value strictly as plain text.

!!! warning "Enable formula escaping for user-supplied data"
    If any non-administrator accounts can write data to an exported field, you must set `escape_formulas=True`. Failing to sanitize exports allows attacker-controlled values to execute system commands or exfiltrate sensitive data when the file is opened locally.

To enable escaping, replace the string format identifier with an explicit exporter instance in your configuration:

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
| `max_upload_size` | `10 MB` | Validated immediately upon request receipt before any parsing is executed. |
| `max_rows` | `100_000` | The maximum number of rows permitted per import request. The payload is counted during a pre-pass phase. Oversized files are rejected with an HTTP 400 response before any database records are initialized. Set to `None` to disable the limit. |

The import feature strictly rejects ZIP archives, completely neutralizing the risk of ZIP-bomb attacks on this endpoint. Furthermore, `FileField` and `ImageField` are systematically excluded from bulk imports (`exclude_from_import=True` by default). Users must attach files individually through the standard create or edit interfaces.

## What this page doesn't cover

The built-in protections mitigate risks specifically within the admin codebase. However, they do not guarantee the security of your overall architecture. The following operational security measures are outside the scope of Starlette-admin and remain your responsibility:

* **Transport security:** You must serve the admin over HTTPS. While CSRF and flash cookies are cryptographically signed, they are not encrypted in transit. Anyone intercepting plain HTTP traffic can read their contents.
* **Authentication and authorization:** The `Admin` instance is entirely public until you attach an `AuthProvider`. Without one, every endpoint and route is completely unrestricted. See [Authentication](auth.md).
* **Network exposure:** If the administration panel does not require public access, restrict it via a firewall, VPN, or strict IP allowlisting.
* **Dependency hygiene:** Monitor security advisories and keep `starlette-admin`, `Starlette`, your ORM driver, and all underlying dependencies actively updated.
* **Post-authentication actions:** CSRF and upload validation do not restrict an authenticated user's privileges. Granular access control is governed entirely by the permission checks you implement within `is_accessible`, `can_create`, `can_edit`, and `can_delete` (see [Authentication](auth.md)).

Treat this documentation as a guide to configuring the admin package itself, rather than a comprehensive checklist for securing your entire production deployment.

---

## What's next

* **[Export & Import](export-import.md):** Deep dive into the export dialog, the import preview lifecycle, and the ZIP bundle specification.
* **[File Storage](file-storage.md):** Architectural patterns for configuring storage backends targeting `FileField` and `ImageField`.
* **[Authentication](auth.md):** Learn how the `secret_key` securely gates login sessions and CSRF checks once an authentication provider is established.
