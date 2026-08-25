---
title: MongoEngine इंटीग्रेशन
description: MongoEngine मॉडल को starlette-admin के साथ जोड़ना सीखें और एडमिन पैनल
  के ज़रिए अपना MongoDB डेटा प्रबंधित करें।
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# MongoEngine इंटीग्रेशन {#mongoengine-integration}

MongoEngine, Django-शैली के फ़ील्ड API का उपयोग करके MongoDB डॉक्यूमेंट को सिंक्रोनस Python क्लासेस के रूप में मॉडल करता है। `starlette_admin.contrib.mongoengine` मॉड्यूल विशेष `Admin` और `ModelView` क्लासेस प्रदान करता है, जो आपकी `mongoengine.Document` परिभाषाओं से सीधे एडमिनिस्ट्रेटिव व्यू बनाते हैं।

**मुख्य विशेषताएँ:**

* फ़ील्ड टाइप, रिलेशनशिप, और embedded डॉक्यूमेंट का स्वचालित रूपांतरण।
* GridFS-आधारित `FileField` और `ImageField` अपलोड के लिए out-of-the-box समर्थन।

## इंस्टॉलेशन {#installation}

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## न्यूनतम उदाहरण {#minimal-example}

एडमिन इंटरफ़ेस तक कोई भी रिक्वेस्ट पहुँचने से पहले आपको MongoDB कनेक्शन स्थापित करना होगा। यह पूर्वापेक्षा पूरी होना सुनिश्चित करने का सबसे अच्छा तरीका यह है कि कनेक्शन लॉजिक को अपने मुख्य ऐप्लिकेशन के `lifespan` कॉन्टेक्स्ट मैनेजर के भीतर रैप किया जाए।

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

`ModelView` `mongoengine.Document` क्लास को सीधे स्वीकार करता है। यह डॉक्यूमेंट के फ़ील्ड से फ़ील्ड सूची, फ़ॉर्म और फ़िल्टर स्वचालित रूप से तैयार कर लेता है।

## मुख्य क्लासेस: Admin और ModelView {#core-classes-admin-and-modelview}

### `mongoengine.Admin` क्लास {#the-mongoengineadmin-class}

`mongoengine.Admin` क्लास बेस `Admin` को एक विशेष रूट जोड़कर विस्तारित करती है: `/api/file/{db}/{col}/{pk}`। यह रूट GridFS फ़ाइल को सीधे ब्राउज़र को स्ट्रीम करता है।

चूँकि MongoEngine मॉडल पर प्रत्येक `FileField` और `ImageField` अपलोड GridFS में संग्रहीत होता है, इन फ़ाइलों को सर्व करने के लिए यह रूट आवश्यक है। बेस `Admin` के स्थान पर हमेशा `mongoengine.Admin` का उपयोग करें।

### `mongoengine.ModelView` क्लास {#the-mongoenginemodelview-class}

बेस क्लास के विपरीत, `mongoengine.ModelView` कंस्ट्रक्टर घोषणात्मक मॉडल क्लास के बजाय `document` पोज़िशनल आर्ग्युमेंट लेता है:

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

यदि आप अपनी `ModelView` सबक्लास पर `fields` एट्रिब्यूट अनसेट छोड़ दें, तो यह डिफ़ॉल्ट रूप से डॉक्यूमेंट के प्रत्येक फ़ील्ड को उनकी घोषणा के क्रम में शामिल करता है।

`key`, `menu_label`, और `display_name` जैसे एट्रिब्यूट एक सख़्त फ़ॉलबैक क्रम का पालन करते हैं:

1. कंस्ट्रक्टर आर्ग्युमेंट।
2. सबक्लास पर सेट किया गया क्लास-स्तरीय एट्रिब्यूट।
3. डॉक्यूमेंट के क्लास नाम से प्राप्त मान (`key` slugified नाम बन जाता है, `menu_label` pluralized prettified नाम बन जाता है, और `display_name` singular prettified नाम बन जाता है)।

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## फ़िल्टर रजिस्ट्री {#filter-registry}

प्रत्येक फ़ील्ड टाइप में `MongoEngineFilterRegistry` द्वारा प्रदान किए गए फ़िल्टर का एक निश्चित सेट शामिल है। आप `filters=[...]` आर्ग्युमेंट का उपयोग करके इन डिफ़ॉल्ट को प्रति फ़ील्ड ओवरराइड कर सकते हैं।

| फ़ील्ड टाइप | उपलब्ध फ़िल्टर |
| --- | --- |
| `StringField` | contains, not contains, starts with, ends with, equals, not equals, is null, is not null |
| `TextAreaField` | contains, not contains, starts with, ends with, is null, is not null |
| `EnumField` | equals, not equals, in, not in, is null, is not null |
| `NumberField` | equals, not equals, greater than, less than, between, is null, is not null |
| `FloatField` | equals, not equals, greater than, less than, between, is null, is not null |
| `DateField` | equals, between, in the past, in the future, is null, is not null |
| `DateTimeField` | equals, between, in the past, in the future, is null, is not null |
| `BooleanField` | is true, is false, is null, is not null |
| `TagsField` | in, not in, is null, is not null |
| `RelationField` | is null, is not null |
| `ObjectIdField` | equals, not equals, in, not in, is null, is not null |

!!! note
    `ObjectIdField` डॉक्यूमेंट के `id` को दर्शाता है।

अंदरूनी तौर पर, प्रत्येक फ़िल्टर की `apply()` मेथड अपनी विशिष्ट शर्त के लिए एक MongoEngine `Q` फ़्रैगमेंट लौटाती है। फिर नेस्टेड `FilterGroup` ट्री क्वेरी निष्पादित करने से पहले bitwise ऑपरेटर (`&` या `|`) का उपयोग करके उन फ़्रैगमेंट को संयोजित करते हैं। अधिक जानकारी के लिए [Filters](../user-guide/filters.md) दस्तावेज़ीकरण देखें।

## Embedded डॉक्यूमेंट {#embedded-documents}

MongoEngine का `EmbeddedDocumentField` एक `CollectionField` में बदल जाता है। यह प्रक्रिया embedded डॉक्यूमेंट के प्रत्येक फ़ील्ड को उसके अपने सब-फ़ील्ड में पुनरावर्ती (recursive) रूप से बदलती है:

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

इस उदाहरण में:

* `address` फ़ील्ड निर्माण और संपादन के दौरान एक नेस्टेड सब-फ़ॉर्म के रूप में, और डिटेल पेज पर एक नेस्टेड ब्लॉक के रूप में रेंडर होता है।
* `comments` फ़ील्ड (एक `EmbeddedDocumentListField`) `CollectionField` की एक `ListField` में बदल जाता है। यह सब-फ़ॉर्म के एक दोहराए जा सकने वाले समूह के रूप में रेंडर होता है, जिसमें प्रत्येक लिस्ट एंट्री के लिए एक दिखाया जाता है।

## पूर्ण कार्यशील उदाहरण {#full-working-example}

यह अनुभाग `starlette-admin` के साथ एक पूर्ण, रन करने योग्य MongoEngine इंटीग्रेशन प्रदान करता है।

### 1. डिपेंडेंसी इंस्टॉल करें {#1-install-dependencies}

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

`fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे `fastapi dev` चलाकर आप डेवलपमेंट सर्वर शुरू कर सकते हैं।

### 2. ऐप्लिकेशन बनाएं {#2-create-the-application}

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


class AuthorView(ModelView):
    fields = ["id", "name"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

### 3. सर्वर चलाएं {#3-run-the-server}

FastAPI डेवलपमेंट सर्वर शुरू करें:

=== "pip"

    ```bash
    fastapi dev
    ```


=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

एडमिन डैशबोर्ड देखने और उसके साथ इंटरैक्ट करने के लिए अपने ब्राउज़र में [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) पर जाएँ।

> **उन्नत उदाहरण:** रिपॉज़िटरी में [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) एक पूर्ण फ़ीचर वाला ऐप्लिकेशन है। इसमें इनलाइन व्यू, इवेंट, कस्टम row और batch एक्शन, तथा GridFS इमेज और फ़ाइल अपलोड शामिल हैं।

---

## आगे क्या पढ़ें {#what-to-read-next}

* **[Views](../user-guide/views.md):** बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्प देखें।
* **[Fields](../user-guide/fields.md):** `CollectionField` सहित प्रत्येक फ़ील्ड टाइप और उसके एट्रिब्यूट की विस्तृत गाइड।
* **[Filters](../user-guide/filters.md):** फ़िल्टर बिल्डर UI देखें और कस्टम फ़िल्टर लिखना सीखें।
* **[Beanie](beanie.md):** MongoDB के लिए async, Pydantic-आधारित विकल्प जानें।
