---
title: Beanie इंटीग्रेशन
description: FastAPI में अपने MongoDB कलेक्शन के लिए एक विस्तारशील एडमिन इंटरफ़ेस
  बनाने हेतु Beanie ODM को starlette-admin के साथ एकीकृत करें।
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Beanie इंटीग्रेशन {#beanie-integration}

Beanie, MongoDB डॉक्यूमेंट्स को एसिंक्रोनस Pydantic मॉडल के रूप में मॉडल करता है। `starlette_admin.contrib.beanie` मॉड्यूल विशेष `Admin` और `ModelView` क्लासेज़ प्रदान करता है, जो इन डॉक्यूमेंट्स के साथ सीधे इंटरैक्ट करने के लिए कॉन्फ़िगर किए गए हैं।

**प्रमुख विशेषताएँ:**

- MongoDB क्वेरी ऑपरेटर्स और फ़िल्टरिंग के लिए नेटिव समर्थन।
- Pydantic सत्यापन त्रुटियों का स्वतः फ़ील्ड-विशिष्ट UI फ़ॉर्म त्रुटियों में रूपांतरण।
- MongoDB फ़ुल-टेक्स्ट सर्च के लिए बिल्ट-इन इंटीग्रेशन।

## इंस्टॉलेशन {#installation}

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## न्यूनतम उदाहरण {#minimal-example}

किसी भी रिक्वेस्ट के एडमिनिस्ट्रेशन इंटरफ़ेस तक पहुँचने से पहले आपको Beanie को इनिशियलाइज़ करना होगा। इस आवश्यकता की पूर्ति सुनिश्चित करने का सर्वोत्तम तरीका है कि कनेक्शन लॉजिक को अपनी मुख्य ऐप्लिकेशन के `lifespan` context manager के भीतर लपेटा जाए।

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
```

`ModelView` Beanie `Document` क्लास को सीधे स्वीकार करता है। यह डॉक्यूमेंट के फ़ील्ड्स से फ़ील्ड सूची, फ़ॉर्म, तथा फ़िल्टर्स स्वतः प्राप्त कर लेता है।

## मुख्य क्लास {#core-classes}

### `beanie.Admin` क्लास {#the-beanieadmin-class}

`beanie.Admin` क्लास `BaseAdmin` से विरासत में मिलती है और इनिशियलाइज़ेशन के दौरान किसी डेटाबेस-विशिष्ट कॉन्फ़िगरेशन की आवश्यकता नहीं रखती। कनेक्शन सेटअप पूरी तरह ऐप्लिकेशन के lifespan के भीतर होता है। भविष्य के बैकएंड-विशिष्ट संवर्द्धनों के साथ संगतता सुनिश्चित करने के लिए `Admin` को हमेशा `starlette_admin.contrib.beanie` से इंपोर्ट करें।

### `beanie.ModelView` क्लास {#the-beaniemodelview-class}

`beanie.ModelView` क्लास आपके डेटाबेस और UI के बीच इंटीग्रेशन लेयर प्रदान करती है। यह कई ऑपरेशन स्वतः संभालती है:

- **फ़ील्ड पॉप्युलेशन:** यदि आप उन्हें स्पष्ट रूप से निर्दिष्ट नहीं करते, तो डॉक्यूमेंट परिभाषा से फ़ील्ड्स स्वतः जनरेट करता है।
- **आंतरिक फ़ील्ड फ़िल्टरिंग:** डिफ़ॉल्ट रूप से Beanie के आंतरिक `revision_id` फ़ील्ड को लिस्ट और फ़ॉर्म से बाहर रखता है।
- **रिलेशनशिप रिज़ॉल्यूशन:** `fetch_links=True` और `nesting_depth=1` के साथ डेटाबेस रीड निष्पादित करता है, जिससे `Link` संदर्भ कच्चे डेटाबेस references लौटाने के बजाय अपनी संबंधित ऑब्जेक्ट्स तक resolve हो जाते हैं।
- **त्रुटि हैंडलिंग:** Pydantic सत्यापन त्रुटियों को फ़ील्ड-विशिष्ट फ़ॉर्म त्रुटियों में बदलता है, जिससे उपयोगकर्ता सीधे गलत इनपुट तक पहुँचता है।

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## `BeanieObjectIdField` {#the-beanieobjectidfield}

Beanie प्राइमरी कीज़ के लिए `PydanticObjectId` का उपयोग करता है। एडमिनिस्ट्रेशन पैनल इन कीज़ तथा किसी भी raw ObjectId संदर्भ को स्वतः एक समर्पित `BeanieObjectIdField` के माध्यम से दर्शाता है।

यह एक स्टैंडर्ड `StringField` की तरह हूबहू रेंडर और सत्यापित होता है, लेकिन फ़िल्टर रजिस्ट्री में यह अपना अलग स्लॉट बनाए रखता है। यह पृथक्करण सुनिश्चित करता है कि ObjectId-विशिष्ट फ़िल्टर्स केवल ObjectId फ़ील्ड्स पर लागू हों, न कि आपकी ऐप्लिकेशन के हर स्टैंडर्ड टेक्स्ट फ़ील्ड पर। ये विशेष फ़िल्टर्स डेटाबेस से क्वेरी करने से पहले स्ट्रिंग्स को सुरक्षित रूप से वैध `PydanticObjectId` ऑब्जेक्ट्स में parse करते हैं।

## फ़िल्टर रजिस्ट्री {#filter-registry}

हर फ़ील्ड टाइप को `BeanieFilterRegistry` से फ़िल्टर्स का एक डिफ़ॉल्ट सेट मिलता है।

- **स्ट्रिंग मिलान:** समानता (equality) फ़िल्टर अन्य टेक्स्ट सर्च, जैसे "Contains" या "Starts with", के साथ संगतता बनाए रखने के लिए case-insensitive रेगुलर एक्सप्रेशन का उपयोग करता है।
- **ऐरे ऑपरेशन्स:** रजिस्ट्री array-आधारित फ़िल्टरिंग के लिए बिल्ट-इन समर्थन प्रदान करती है, जिससे list-valued फ़ील्ड्स (जैसे `TagsField`) पर "Is one of" ऑपरेशन्स out of the box काम करते हैं।
- **प्राइमरी कीज़:** क्वेरी फ़्रैगमेंट बनाते समय `id` फ़ील्ड स्वतः MongoDB के नेटिव `_id` पर remap हो जाता है।

## फ़ुल-टेक्स्ट सर्च {#full-text-search}

जब उपयोगकर्ता किसी लिस्ट पेज पर सर्च बॉक्स का उपयोग करते हैं, तो एडमिनिस्ट्रेशन पैनल MongoDB कलेक्शन में किसी मौजूदा टेक्स्ट इंडेक्स की जाँच करता है और उसी के अनुसार अपनी क्वेरी रणनीति समायोजित करता है:

- **टेक्स्ट इंडेक्स मौजूद:** क्वेरी MongoDB के नेटिव `$text` ऑपरेटर का उपयोग करती है। यह टोकनाइज़ेशन, स्टेमिंग, और प्रासंगिकता रैंकिंग सहित वास्तविक फ़ुल-टेक्स्ट सर्च क्षमताएँ प्रदान करता है।
- **टेक्स्ट इंडेक्स नहीं:** सिस्टम `searchable` के रूप में चिह्नित सभी फ़ील्ड्स में case-insensitive रेगुलर एक्सप्रेशन सर्च पर लौट आता है। हालाँकि इसके लिए कोई सेटअप आवश्यक नहीं है, यह परिणामों को प्रासंगिकता के अनुसार रैंक नहीं कर सकता और स्टैंडर्ड इंडेक्स का उपयोग नहीं कर सकता।

एडमिनिस्ट्रेशन पैनल मौजूदा टेक्स्ट इंडेक्स का पता लगाता है, लेकिन उन्हें बनाता नहीं है। नेटिव टेक्स्ट सर्च सक्षम करने के लिए आपको अपने Beanie डॉक्यूमेंट पर इंडेक्स परिभाषित करना होगा। उदाहरण के लिए, आप अपने मॉडल में `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` जोड़कर यह कर सकते हैं।

!!! note
यदि आप टेक्स्ट इंडेक्स सक्षम करते हैं, तो आप अपनी `ModelView` सबक्लास पर `full_text_override_order_by = True` सेट करके डिफ़ॉल्ट कॉलम सॉर्ट के बजाय MongoDB के प्रासंगिकता स्कोर के अनुसार सर्च परिणामों को सॉर्ट कर सकते हैं।

## पूर्ण कार्यशील उदाहरण {#full-working-example}

यह अनुभाग `starlette-admin` के साथ एक पूर्ण, चलाने योग्य Beanie इंटीग्रेशन प्रदान करता है।

### 1. डिपेंडेंसी इंस्टॉल करें {#1-install-dependencies}

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

`fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे आप `fastapi dev` चलाकर डेवलपमेंट सर्वर शुरू कर सकते हैं।

### 2. ऐप्लिकेशन बनाएँ {#2-create-the-application}

निम्नलिखित कोड को `main.py` नाम की फ़ाइल में सेव करें।

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

### 3. सर्वर चलाएँ {#3-run-the-server}

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

> **उन्नत उदाहरण:** रिपॉज़िटरी में [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) एक पूर्ण-फ़ीचर्ड उदाहरण रखता है, जिसमें इनलाइन व्यू, इवेंट, और कस्टम बैच एक्शन शामिल हैं।

## आगे क्या पढ़ें {#what-to-read-next}

- **[व्यूज़](../user-guide/views.md)**: बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्पों का अन्वेषण करें।
- **[फ़िल्टर्स](../user-guide/filters.md):** फ़िल्टर बिल्डर और ORM-विशिष्ट फ़िल्टर्स के जुड़ने का तरीका।
- **[MongoEngine](mongoengine.md):** starlette-admin में बिल्ट-इन अन्य MongoDB बैकएंड।
- **[SQLAlchemy](sqlalchemy.md):** starlette-admin में बिल्ट-इन रिलेशनल बैकएंड।
