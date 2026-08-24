---
title: सुरक्षा
description: starlette-admin में बिल्ट-इन सुरक्षा फ़ीचर्स देखें, जिनमें CSRF सुरक्षा,
  file upload safety, और access control शामिल हैं।
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# सुरक्षा {#security}

`starlette-admin` में administration panel चलाने से जुड़े जोखिमों के लिए safeguards बने होते हैं। Cross-site request forgery (CSRF) से सुरक्षा और export/import payload आकारों पर limits `Admin` क्लास instantiate होते ही सक्रिय हो जाती हैं।

ये defaults interface को common attacks के विरुद्ध मज़बूत बनाते हैं, पर ये standard deployment security का विकल्प नहीं हैं। Transport layer security (HTTPS/TLS), network access control, user authentication ([Authentication](auth.md) देखें), dependency updates, और security reviews की ज़िम्मेदारी फिर भी आपकी है। यह पेज automatic protections, उन protections को कवर करता है जिन्हें आप configure करते हैं, और production के लिए आवश्यक `secret_key` setting को।

## स्वतः क्या मिलता है {#what-you-get-automatically}

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

कोई security parameter न होने पर भी admin instance कई common vulnerabilities से बचाता है:

* **CSRF protection:** हर form और jQuery AJAX call पर सक्रिय — row actions और confirmation dialogs सहित।
* **Flash messages:** signed cookie में carried, इसलिए `SessionMiddleware` की ज़रूरत नहीं।
* **Filename sanitization:** storage backend से गुज़रने वाले हर file upload पर लागू।
* **Image content verification:** Pillow इंस्टॉल होने पर `ImageField` uploads को byte level पर validate करता है।
* **Export limits:** resource exhaustion और denial of service से बचने के लिए per request 100,000 rows पर capped.
* **Import limits:** memory exhaustion सीमित करने के लिए per request 10 MB पर capped.

एक और protection उपलब्ध है, पर डिफ़ॉल्ट रूप से बंद: CSV और spreadsheet exports (XLSX, XLS, ODS) में spreadsheet formula injection रोकने वाला escaping। [Formula injection](#formula-injection) देखें।

नीचे के sections इन protections को समझाते हैं और बताते हैं कि आपके नियंत्रण की thresholds कैसे adjust करें।

## Secret key {#the-secret-key}

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

`secret_key` दो cookies पर signing का cryptographic आधार है: CSRF token और flash-message cookie। दोनों [itsdangerous](https://itsdangerous.palletsprojects.com/) का उपयोग करते हैं, इसलिए clients cookies पढ़ तो सकते हैं पर key के बिना payload forge या tamper नहीं कर सकते।

!!! warning "Production में हमेशा explicit secret key सेट करें"
    यदि आप `secret_key` छोड़ दें, तो `Admin` instance startup पर एक random key generate करता है और `UserWarning` emit करता है। Local demo के लिए ठीक, पर multi-worker deployments में यह टूट जाता है। जब आप कई workers चलाते हैं — जैसे `uvicorn --workers 4`, Gunicorn, या multiple containers — प्रत्येक process अपनी key generate करता है। Form serve करने वाले worker द्वारा sign किया गया CSRF token, submission को handle करने वाले दूसरे worker पर validation fail कर देता है; परिणाम requests के एक अनियमित (seemingly random) भाग पर invalid CSRF token errors। Single process से आगे बढ़ने से पहले `secret_key` explicitly सेट करें।

## CSRF protection

`CSRFMiddleware` cross-site request forgery रोकने के लिए signed double-submit cookie pattern का उपयोग करता है। यह safe HTTP methods (`GET`, `HEAD`, `OPTIONS`, और `TRACE`) पर `starlette_admin_csrftoken` cookie issue करता है। Mutating requests के लिए, वह उस cookie को `X-CSRFToken` header या `csrftoken` hidden form field के विरुद्ध validate करता है।

हर बिल्ट-इन admin template (`create`, `edit`, और `login`) hidden field आपके लिए render कर देता है:

```jinja
{{ csrf_input(request) }}

```

Bundled JavaScript हर jQuery AJAX call में header attach करता है, इसलिए row actions और अन्य asynchronous interactions बिना extra code protected रहते हैं। `csrf_input(request)` स्वयं कॉल करें केवल तब जब default templates के बाहर custom forms बना रहे हों। [Custom Views](custom-views.md) देखें।

## File uploads

[storage](file-storage.md) backend से गुज़रने वाला हर upload `secure_filename` से sanitized होता है। Directory traversal path components strip हो जाते हैं, और `[A-Za-z0-9_.-]` से बाहर के characters underscores (`_`) बन जाते हैं। इसे बंद नहीं किया जा सकता।

`accept` और `max_size` से content-type तथा size restrictions per field सेट करें:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

इनके बिना `FileField` कोई भी file type और size स्वीकार करता है। `ImageField` अपवाद है: उसका default `accept="image/*"` है, और Pillow इंस्टॉल होने पर वह ऐसा validator prepend करता है जो upload को `PIL.Image` से खोलकर पुष्टि करता है कि bytes image के रूप में decode होते हैं — browser-supplied metadata पर भरोसा करने के बजाय।

!!! important "Web server level पर request size limits enforce करें"
    केवल `max_size` पर भरोसा न करें। Application-level check server द्वारा पूरा request payload receive होने के बाद ही चलता है। Denial-of-service (DoS) attacks रोकने के लिए request body size को web server configuration में cap करें — जैसे NGINX का `client_max_body_size` या load balancer पर समकक्ष setting।

!!! warning "File extensions और Content-Type headers spoofed हो सकते हैं"
    `accept` attribute filename extension और browser-provided `Content-Type` header पर टिका है, और attacker दोनों spoof कर सकता है। `invoice.pdf` दिखने वाली file executable payload carry कर सकती है।

    Non-image files के लिए `accept` को ऐसे custom validator के साथ जोड़ें जो file के magic bytes inspect करे। [`filetype`](https://github.com/h2non/filetype.py) और [`python-magic`](https://github.com/ahupp/python-magic) जैसी libraries true file format verify करती हैं:

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

    Validator को `FileField(..., validators=[validate_document_type])` से लगाएँ। पूर्ण implementation के लिए [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) देखें।

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

ZIP bundle कैसे बनता है, इसके लिए [Export & Import](export-import.md) देखें।

### Formula injection

Spreadsheet software किसी cell value को जो `=`, `+`, `-`, या `@` से शुरू होती है, formula की तरह treat करता है। यदि कोई untrusted user exported field में `=HYPERLINK(...)` जैसा payload save कर दे, तो administrator द्वारा file खोलने पर spreadsheet application उसे run कर देता है। इसे CSV injection, या formula injection कहते हैं।

Exported values database में stored हुए ठीक उसी रूप में लिखे जाते हैं, इसलिए formula escaping **डिफ़ॉल्ट रूप से बंद** है। CSV exporter और Tablib spreadsheet exporters (`xlsx`, `xls`, और `ods`) सभी `escape_formulas` parameter स्वीकार करते हैं। इसे चालू करने पर trigger character से शुरू होने वाली किसी भी string के आगे single quote (`'`) लग जाता है, जो application को उस value को plain text की तरह render करने के लिए मजबूर करता है।

!!! warning "User-supplied data के लिए formula escaping चालू करें"
    यदि कोई non-administrator account exported field में data लिख सकता है, तो `escape_formulas=True` सेट करें। इसके बिना attacker-controlled values किसी के locally file खोलने पर system commands run कर सकते हैं या data exfiltrate कर सकते हैं।

Escaping चालू करने के लिए format string को explicit exporter instance से बदलें:

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

Import ZIP archives को outright reject करता है, जिससे इस endpoint पर ZIP-bomb attacks का जोखिम समाप्त हो जाता है। Bulk imports से `FileField` और `ImageField` भी excluded हैं — डिफ़ॉल्ट रूप से `exclude_from_import=True` — इसलिए users files को create/edit फ़ॉर्म से एक-एक करके attach करते हैं।

## इस पेज में क्या शामिल नहीं {#what-this-page-doesnt-cover}

Built-in protections admin codebase के अंदर के risks address करती हैं। वे आपकी architecture को पूरे में secure नहीं बनातीं। ये operational measures `starlette-admin` के scope से बाहर हैं और आपकी ही ज़िम्मेदारी रहती हैं:

* **Transport security:** Admin को HTTPS पर serve करें। CSRF और flash cookies signed हैं, encrypted नहीं — plain HTTP traffic intercept करने वाला कोई भी उन्हें पढ़ सकता है।
* **Authentication और authorization:** जब तक आप `AuthProvider` attach नहीं करते, `Admin` instance public रहता है। इसके बिना हर endpoint और route open रहता है। [Authentication](auth.md) देखें।
* **Network exposure:** यदि admin panel को public access नहीं चाहिए, तो उसे firewall, VPN, या IP allowlist के पीछे रखें।
* **Dependency hygiene:** Security advisories पर नज़र रखें और `starlette-admin`, Starlette, अपने ORM driver, और बाकी dependencies को up to date रखें।
* **Post-authentication actions:** CSRF और upload validation signed-in user को क्या करने से रोकती नहीं। Granular access control पूरी तरह आपके द्वारा `is_accessible`, `can_create`, `can_edit`, और `can_delete` में लिखे permission checks से आती है। [Authentication](auth.md) देखें।

इस पेज को admin package configure करने की guide समझें — पूरे production deployment को secure करने की checklist नहीं।

---

## आगे क्या {#whats-next}

* **[Export & Import](export-import.md):** Export dialog, import preview lifecycle, और ZIP bundle layout.
* **[File Storage](file-storage.md):** `FileField` और `ImageField` के लिए storage backends configure करने के patterns.
* **[Authentication](auth.md):** Auth provider जोड़ने के बाद `secret_key` sign-in sessions और CSRF checks को कैसे gate करता है।
