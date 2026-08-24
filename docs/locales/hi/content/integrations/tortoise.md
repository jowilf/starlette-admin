---
title: Tortoise ORM इंटीग्रेशन
description: starlette-admin का उपयोग करके FastAPI में अपने Tortoise ORM मॉडल के लिए
  आसानी से एडमिन इंटरफ़ेस बनाएं।
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Tortoise ORM इंटीग्रेशन {#tortoise-orm-integration}

Tortoise ORM, Django से प्रेरित एक asyncio-नेटिव ऑब्जेक्ट-रिलेशनल मैपर है। `starlette_admin.contrib.tortoise` मॉड्यूल विशेष `Admin`, `ModelView`, और `InlineModelView` क्लासेस प्रदान करता है, जो आपके Tortoise मॉडल के साथ सीधे इंटीग्रेट होने के लिए पहले से कॉन्फ़िगर की गई होती हैं।

**मुख्य विशेषताएँ:**

* **स्वचालित फ़ील्ड रूपांतरण:** Tortoise मॉडल फ़ील्ड को सीधे UI कंपोनेंट्स में मैप करता है। इसमें enum, JSON, तिथियों और स्वचालित टाइमस्टैंप के लिए पूर्ण समर्थन शामिल है।
* **रिलेशनशिप मैपिंग:** foreign key और one-to-one रिलेशन को `HasOne` फ़ील्ड में, तथा many-to-many रिलेशन को `HasMany` फ़ील्ड में बदलता है। backward रिलेशन स्वचालित रूप से read-only रेंडर होते हैं।
* **उन्नत फ़िल्टरिंग:** फ़िल्टर बिल्डर के लिए Tortoise `Q` एक्सप्रेशन का उपयोग करता है और string फ़ील्ड में case-insensitive फ़ुल-टेक्स्ट खोज सक्षम करता है।
* **एरर ट्रांसलेशन:** Tortoise सत्यापन त्रुटियों को सीधे UI में फ़ील्ड-विशिष्ट फ़ॉर्म त्रुटियों में बदलता है।

## इंस्टॉलेशन {#installation}

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## न्यूनतम उदाहरण {#minimal-example}

Tortoise, आपके ऐप्लिकेशन के `lifespan` कॉन्टेक्स्ट मैनेजर के भीतर डेटाबेस से कनेक्ट होता है। एडमिन व्यू आमतौर पर इंपोर्ट के समय (`Tortoise.init()` चलने से पहले) इंस्टेंटिएट किए जाते हैं, इसलिए आपको रिलेशन को जल्दी रिज़ॉल्व करना होगा।

यह सुनिश्चित करने के लिए कि एडमिन व्यू बनते समय रिलेशन उपलब्ध हों, अपने मॉडल परिभाषित करते ही तुरंत `Tortoise.init_models()` को कॉल करें।

```python
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from tortoise import Tortoise, fields
from tortoise.models import Model
from starlette_admin.contrib.tortoise import Admin, ModelView


class Genre(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)


# Resolve relations at import time before the admin views are built.
Tortoise.init_models(["app"], "models")


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(
        db_url="sqlite://library.sqlite3", modules={"models": ["app"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

`ModelView` Tortoise `Model` क्लास को सीधे स्वीकार करता है और मॉडल के स्कीमा से फ़ील्ड सूची, फ़ॉर्म और फ़िल्टर स्वचालित रूप से तैयार कर लेता है।

## मुख्य क्लासेस {#core-classes}

### `tortoise.Admin`

`tortoise.Admin` क्लास `BaseAdmin` से इनहेरिट होती है और इनिशियलाइज़ेशन के दौरान किसी डेटाबेस-विशिष्ट कॉन्फ़िगरेशन की आवश्यकता नहीं होती। कनेक्शन सेटअप पूरी तरह से ऐप्लिकेशन के lifespan के भीतर होता है। भविष्य के बैकएंड-विशिष्ट सुधारों के साथ संगतता सुनिश्चित करने के लिए `Admin` को हमेशा `starlette_admin.contrib.tortoise` से इंपोर्ट करें।

### `tortoise.ModelView`

`tortoise.ModelView` क्लास आपके डेटाबेस और यूज़र इंटरफ़ेस के बीच इंटीग्रेशन लेयर प्रदान करती है। यह निम्नलिखित ऑपरेशन स्वचालित रूप से संभालती है:

* **फ़ील्ड पॉपुलेशन:** यदि आप फ़ील्ड स्पष्ट रूप से निर्दिष्ट नहीं करते, तो उन्हें मॉडल परिभाषा से जनरेट करती है। to-one रिलेशन को बैक करने वाले raw key कॉलम (जैसे `author` नाम के रिलेशन के लिए `author_id`) और backward रिलेशन डिफ़ॉल्ट रूप से छोड़ दिए जाते हैं।
* **रिलेशन रिज़ॉल्यूशन:** व्यू द्वारा दिखाए गए प्रत्येक रिलेशन को प्रीफ़ेच करती है। इससे यह सुनिश्चित होता है कि लिस्ट और डिटेल पेज कभी lazy load ट्रिगर न करें।
* **ऑटो टाइमस्टैंप:** `DatetimeField(auto_now=...)` या `DatetimeField(auto_now_add=...)` का उपयोग करने वाले कॉलम read-only रेंडर होते हैं और उन्हें कभी required चिह्नित नहीं किया जाता।
* **एरर हैंडलिंग:** Tortoise सत्यापन त्रुटियों (`"<field>: <detail>"`) को फ़ील्ड-विशिष्ट फ़ॉर्म त्रुटियों में बदलती है जो उपयोगकर्ताओं को सीधे गलत इनपुट की ओर इंगित करती हैं।

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

इनलाइन व्यू उपयोगकर्ताओं को पैरेंट फ़ॉर्म के भीतर संबंधित पंक्तियाँ संपादित करने की सुविधा देते हैं। जब child मॉडल में parent मॉडल की ओर इशारा करता ठीक एक ही रिलेशन हो, तो foreign key स्वतः पहचान लिया जाता है। यदि एकाधिक रिलेशन मौजूद हैं, तो आपको `fk_attr` को स्पष्ट रूप से रिलेशन नाम या उसके raw key कॉलम में से किसी एक पर सेट करना होगा।

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## रिलेशन संभालना {#handling-relations}

इंटीग्रेशन फ़ील्ड टाइप के आधार पर डेटाबेस रिलेशन को एडमिन फ़ील्ड में मैप करता है। ताकि रिलेशन फ़ील्ड अपने foreign व्यू को सफलतापूर्वक रिज़ॉल्व कर सकें, आपको प्रत्येक संबंधित मॉडल के लिए एक `ModelView` रजिस्टर करना होगा।

| रिलेशन टाइप | Tortoise कॉन्फ़िगरेशन | एडमिन व्यवहार |
| --- | --- | --- |
| **Forward (To-One)** | `ForeignKeyField`, `OneToOneField` | `HasOne` में बदलता है। |
| **Forward (To-Many)** | `ManyToManyField` | `HasMany` में बदलता है। |
| **Backward** | `related_name` प्रॉपर्टीज़ | read-only रेंडर होता है। दिखाने के लिए इसे स्पष्ट रूप से `fields` में जोड़ना होगा। |

**रिलेशन पर फ़िल्टरिंग और सॉर्टिंग:**
to-one रिलेशन raw key कॉलम को लक्षित करने वाले "Is null" और "Is not null" फ़िल्टर प्रदान करते हैं। किसी रिलेशन को फ़िल्टर बिल्डर में उपलब्ध कराने के लिए, रिलेशन नाम को `searchable_fields` में जोड़ें। raw key कॉलम द्वारा सॉर्टिंग सक्षम करने के लिए, रिलेशन नाम को `sortable_fields` में जोड़ें।

## सर्च और फ़िल्टरिंग {#search-and-filtering}

### फ़िल्टर रजिस्ट्री {#filter-registry}

प्रत्येक फ़ील्ड टाइप को `TortoiseFilterRegistry` से फ़िल्टर का एक डिफ़ॉल्ट सेट मिलता है, जिसे Tortoise `Q` एक्सप्रेशन का उपयोग करके लागू किया गया है:

* **String मैचिंग:** contains, starts/ends with, और equality फ़िल्टर case-insensitive लुकअप (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`) का उपयोग करते हैं।
* **Enum:** `CharEnumField` और `IntEnumField` दोनों कॉलम के लिए क्वेरी करने से पहले raw फ़िल्टर मानों को वापस enum मेंबर्स में बदला जाता है।
* **Time कॉलम:** `TimeField` कॉलम केवल null चेक प्रदान करते हैं। यह सीमा इसलिए मौजूद है क्योंकि time-टाइप किए गए पैरामीटर को सभी डेटाबेस बैकएंड में पोर्टेबल तरीके से बाइंड नहीं किया जा सकता।

### फ़ुल-टेक्स्ट सर्च {#full-text-search}

लिस्ट पेज का सर्च बॉक्स सभी searchable string-जैसे फ़ील्ड में case-insensitive `contains` मैच (`OR`-संयुक्त `Q` एक्सप्रेशन) बनाता है। अपने व्यू पर `get_search_query()` मेथड को ओवरराइड करके आप इस व्यवहार को कस्टमाइज़ कर सकते हैं।

## पूर्ण कार्यशील उदाहरण {#full-working-example}

यह अनुभाग `starlette-admin` के साथ एक पूर्ण, रन करने योग्य Tortoise ORM इंटीग्रेशन प्रदान करता है।

### 1. डिपेंडेंसी इंस्टॉल करें {#1-install-dependencies}

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

`fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे `fastapi dev` चलाकर आप डेवलपमेंट सर्वर शुरू कर सकते हैं।

### 2. ऐप्लिकेशन बनाएं {#2-create-the-application}

निम्नलिखित कोड को `main.py` नाम की फ़ाइल में सहेजें।

```python title="main.py"
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from starlette_admin import SlugField
from starlette_admin.contrib.tortoise import Admin, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

DB_URL = "sqlite://blog.sqlite3"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __admin_repr__(self, request) -> str:
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts")

    def __admin_repr__(self, request) -> str:
        return self.title


# Resolve relations at import time before the admin views are built.
Tortoise.init_models(["main"], "models")


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
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["main"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

क्योंकि `created_at` में `auto_now_add` का उपयोग होता है, एडमिन इसे स्वचालित रूप से read-only रेंडर करता है। कोई `exclude_fields_from_create` या `exclude_fields_from_edit` कॉन्फ़िगरेशन की आवश्यकता नहीं है।

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

> **उन्नत उदाहरण:** रिपॉज़िटरी में [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) एक फ़ीचर-संपन्न उदाहरण है जिसमें SQLite पर आधारित रिलेशन, इनलाइन व्यू, enum, और JSON फ़ील्ड शामिल हैं।

## आगे क्या पढ़ें {#what-to-read-next}

* **[Views](../user-guide/views.md):** बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्प देखें।
* **[Filters](../user-guide/filters.md):** फ़िल्टर बिल्डर और इसमें ORM-विशिष्ट फ़िल्टर कैसे जुड़ते हैं, यह जानें।
* **[SQLAlchemy](sqlalchemy.md):** starlette-admin में बने अन्य रिलेशनल बैकएंड का दस्तावेज़ीकरण।
