---
title: फ़ाइल स्टोरेज
description: starlette-admin में LocalStorage या S3-संगत backend storage का उपयोग
  करके file और image uploads प्रबंधित करें।
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# File Storage

`FileField` और `ImageField` uploaded files को एक storage backend के माध्यम से store करते हैं, जिसे आप field के `storage` parameter से सेट करते हैं।

Storage backend एक बार बनाएँ और उसी location में files रखने वाले हर field पर reuse करें।


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

जब user admin के माध्यम से cover upload करता है, admin:

* file को `uploads/covers/` में save करता है
* `cover` column में JSON metadata object store करता है

Database में कभी file स्वयं, filesystem path, या binary data नहीं रहता।


## Database में क्या store होता है {#what-gets-stored-in-the-database}

Admin file upload को model field में serialized [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) object के रूप में represent करता है।

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

* `filename`: sanitized original filename, display के लिए उपयोगी
* `content_type`: upload के समय detect किया गया MIME type
* `size`: bytes में file size
* `storage`: registered backend name — URL generation और deletion के लिए file location resolve करने में उपयोगी
* `key`: storage-relative path या object key
* `url`: cached public URL

`LocalStorage` खाली `url` value store करता है, क्योंकि URLs active request पर निर्भर करते हैं। `S3Storage` public या presigned URL store करता है, आपकी configuration के अनुसार।

Backend कुछ भी हो, `FileField` render time पर stored value पर भरोसा करने के बजाय URL को `storage.url()` से regenerate करता है।

`ImageField` `width` और `height` जोड़ता है।

Admin हर filename को store करने से पहले `secure_filename` से sanitize करता है: path components strip करता है और `[A-Za-z0-9_.-]` से बाहर के characters `_` से replace कर देता है। [Security](security.md) देखें।


## Storage backends

### Local storage

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `base_dir` | `str \| Path` | required | Root directory for stored files. Created for you if it doesn't exist. |
| `name` | `str \| None` | `"local"` | Registry name that identifies the backend. Must be unique when you use several instances. |

Admin files इस route के माध्यम से serve करता है:

```
/_files/{storage}/{path}
```

आपको किसी extra static file configuration की आवश्यकता नहीं।

`LocalStorage.url()` current request context से URLs बनाता है, इसलिए stored `url` field खाली रहता है और on demand recompute होता है।

!!! note
    Code example के लिए [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) देखें।

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

Optional dependencies इंस्टॉल करें:

```bash
pip install starlette-admin[s3]
```

इससे `aiobotocore` इंस्टॉल होता है।

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `bucket` | `str` | required | S3 bucket name. |
| `prefix` | `str` | `"uploads/"` | Key prefix applied to every stored object. |
| `region` | `str` | `"us-east-1"` | AWS region used for signing and URL generation. |
| `access_key` and `secret_key` | `str \| None` | `None` | Optional credentials. Falls back to the default AWS credential chain. |
| `public` | `bool` | `True` | When `True`, returns a public URL. When `False`, generates presigned URLs. |
| `expires` | `int` | `3600` | Expiration time for presigned URLs, in seconds. |
| `endpoint_url` | `str \| None` | `None` | Custom S3-compatible endpoint, such as MinIO, R2, or B2. |
| `name` | `str \| None` | `"s3"` | Registry name that identifies the backend. |

जब आप `endpoint_url` provide करते हैं, तब admin URLs इस रूप में बनाता है:

```
{endpoint_url}/{bucket}/{key}
```

AWS virtual-hosted format का उपयोग करने के बजाय।


!!! important
    File fields को JSON-capable database column पर map होना चाहिए। Database में केवल metadata रहता है; storage backend में file स्वयं।


## Multiple files (`multiple=True`)

एक ही field में कई uploads accept करने के लिए `FileField` या `ImageField` पर `multiple=True` सेट करें।

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

Database `FileInfo` objects की एक JSON list store करता है, और admin प्रत्येक file को validation तथा storage के माध्यम से स्वतंत्र रूप से process करता है।


!!! warning
    Form save करने पर पूरी file list submitted files से replace हो जाती है। Single file add/remove करने का कोई रास्ता नहीं। Per-file lifecycle management के लिए अपने `FileField` वाले inline model का उपयोग करें।

!!! important
    `ListField(FileField(...))` supported नहीं है। Simple collections के लिए `multiple=True` और structured file data के लिए inline models का उपयोग करें।

## Validation

Validation इस क्रम में चलती है:

1. `accept`
2. `max_size`
3. custom `validators`

Custom validator एक callable है जो request, field, एक `UploadFile`, और पूरे submitted form values पाता है। उसे `None` return करना चाहिए या `ValueError` raise करना चाहिए।

निम्नलिखित उदाहरण `filetype` library से वास्तविक file contents validate करता है:

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

!!! important "File pointer reset करें"
    Inspection से पहले और बाद हमेशा `seek(0)` से file pointer reset करें, ताकि storage layer पूरी file पढ़ सके।

!!! note
    Validators प्रति file चलते हैं, इसलिए `multiple=True` के साथ हर file independently validate होती है। `ImageField` custom validator से पहले अपनी image validation लगाता है।


!!! tip "बेहतरीन प्रथाएँ"
    Lightweight validation के लिए `accept` और `max_size` का उपयोग करें।

    File contents inspect करने या application-specific rules enforce करने हों तो custom validators का उपयोग करें।

    Security-sensitive validation के लिए file extensions या `Content-Type` headers पर भरोसा न करें। इसके बजाय contents की जाँच करें — `filetype` या `python-magic` जैसी library से।


## File cleanup की सीमाएँ {#file-cleanup-limitations}

`starlette-admin` files को storage backend में upload करता है और database में `FileInfo` metadata लिखता है, पर failure या deletion के बाद files clean up नहीं करता। इसके दो व्यवहार निकलते हैं:

* **Failed transactions:** यदि upload पूरा होने के बाद database transaction rollback हो जाती है, file storage backend में रह जाती है। Storage writes का कोई rollback mechanism नहीं होता।
* **Deletions और updates:** Row delete करने या file replace करने से database से `FileInfo` reference हट जाता है, पर पुरानी file `LocalStorage` या `S3Storage` में बनी रहती है।

यह design storage layer को सरल रखता है और application-level errors को destructive operations trigger करने से रोकता है। Tradeoff यह है कि orphaned files जमा होती जाती हैं। Storage को असीमित बढ़ने से रोकने के लिए उन्हें स्वयं reconcile करें। एक common pattern है periodic background job जो storage backend की keys को database की active `FileInfo` references से diff करता है।

### Transactional alternative

यदि आपके application को file storage operations को database writes के साथ transactional चाहिए, तो ऐसी library का उपयोग करें जो file storage को SQLAlchemy unit of work से जोड़े।

Field के `storage=` parameter के बजाय [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file) उपयोग करें। वह files को ORM flush और rollback cycle के हिस्से के रूप में store करता है, इसलिए failed transaction या row deletion matching file write को undo कर देता है। Working example के लिए [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) देखें।

---

## आगे क्या {#whats-next}

* **[फ़ील्ड्स](fields.md):** `FileField` और `ImageField` संदर्भ.
* **[Export & Import](export-import.md):** Export bundles में files कैसे शामिल होती हैं।
* **[Security](security.md):** Automatic sanitization और validation behavior.
