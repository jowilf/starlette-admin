---
title: SQLModel इंटीग्रेशन
description: starlette-admin का उपयोग करके अपने FastAPI SQLModel ऐप्लिकेशन के लिए
  एक व्यापक एडमिन डैशबोर्ड बनाएँ।
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# SQLModel इंटीग्रेशन {#sqlmodel-integration}

[SQLModel](https://sqlmodel.tiangolo.com/) SQLAlchemy टेबल को Pydantic सत्यापन के साथ एक ही मॉडल क्लास में जोड़ता है। चूँकि SQLModel मॉडल अंदरूनी रूप से SQLAlchemy मॉडल ही होते हैं, इसलिए `starlette_admin.contrib.sqlmodel` मॉड्यूल मौजूदा [SQLAlchemy बैकएंड](sqlalchemy.md) के चारों ओर एक पतली wrapper के रूप में कार्य करता है।

अलग सिस्टम लागू करने के बजाय, यह इंटीग्रेशन सभी फ़ील्ड ऑटो-डिटेक्शन, प्राइमरी की मैनेजमेंट, रिलेशनशिप हैंडलिंग, फ़िल्टरिंग, और सेशन मिडलवेयर सीधे कोर SQLAlchemy बैकएंड से विरासत में लेता है। यह एक मज़बूत सत्यापन लेयर प्रस्तुत करता है, जो किसी भी डेटाबेस राइट होने से पहले सबमिट किए गए फ़ॉर्म डेटा को आपके मॉडल के नेटिव Pydantic validators (जैसे `Field(min_length=...)` या कस्टम `@field_validator` मेथड्स) से गुज़ारती है। फलस्वरूप आने वाली किसी भी `ValidationError` exception को UI में स्वतः प्रति-फ़ील्ड फ़ॉर्म त्रुटियों में बदल दिया जाता है।

!!! note
    [SQLAlchemy पेज](sqlalchemy.md) पर दस्तावेज़ित हर बात अपरिवर्तित रूप से लागू होती है। इसमें सिंक्रोनस और एसिंक्रोनस इंजन, `sessionmaker` प्रोवाइडर्स, प्रति-रिक्वेस्ट-एक-commit सेशन लाइफ़साइकल, रिलेशनशिप फ़ील्ड्स, और फ़िल्टर रजिस्ट्री शामिल हैं।

## इंस्टॉलेशन {#installation}

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## न्यूनतम उदाहरण {#minimal-example}

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ModelView` SQLModel टेबल क्लास को सीधे स्वीकार करता है और मॉडल के स्कीमा से फ़ील्ड सूची, फ़ॉर्म, तथा फ़िल्टर्स स्वतः प्राप्त कर लेता है।

## मुख्य क्लास {#core-classes}

### `sqlmodel.Admin`

`sqlmodel.Admin` क्लास, `sqla.Admin` क्लास का re-export है। यह वही कंस्ट्रक्टर उपयोग करता है और अपने आवश्यक `session_provider` आर्ग्युमेंट के रूप में एक `Engine`, `AsyncEngine`, `sessionmaker`, या `async_sessionmaker` स्वीकार करता है। यह वही सेशन मिडलवेयर भी जोड़ता है जो हर रिक्वेस्ट पर `request.state.session` को पॉप्युलेट करता है।

### `sqlmodel.ModelView`

`sqlmodel.ModelView` क्लास `sqla.ModelView` से सब कुछ विरासत में लेता है और एक सत्यापन लेयर जोड़ता है। इसकी `validate()` मेथड रिकॉर्ड लिखने से पहले `self.model.model_validate(data)` को कॉल करती है, जिससे यह सुनिश्चित होता है कि फ़ॉर्म सबमिशन को केवल SQLAlchemy कॉलम constraints पर निर्भर रहने के बजाय मॉडल के Pydantic validators द्वारा जाँचा जाए। फ़ाइल फ़ील्ड्स और रिलेशनशिप फ़ील्ड्स जानबूझकर इस सत्यापन कॉल से बाहर रखे जाते हैं, क्योंकि वे मॉडल की Pydantic सत्यापन सतह से बाहर होते हैं।

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

इनलाइन व्यू उपयोगकर्ताओं को पैरेंट फ़ॉर्म के भीतर संबंधित पंक्तियाँ संपादित करने की सुविधा देते हैं। यह क्लास SQLAlchemy `InlineModelView` से foreign key detection और सेशन हैंडलिंग विरासत में लेता है और प्रत्येक इनलाइन पंक्ति पर वही Pydantic सत्यापन लागू करता है।

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Pydantic सत्यापन {#pydantic-validation}

मॉडल पर घोषित constraints स्वतः ही create और edit फ़ॉर्म पर लागू होते हैं:

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

दो वर्णों से छोटा `full_name` या अमान्य ईमेल पते जैसा इनपुट सत्यापन में विफल होगा। ये विफलताएँ किसी भी `INSERT` या `UPDATE` ऑपरेशन के डेटाबेस तक पहुँचने से पहले प्रति-फ़ील्ड फ़ॉर्म त्रुटियों के रूप में लौटती हैं।

!!! note
    `EmailStr` टाइप को `email-validator` पैकेज की आवश्यकता होती है, जिसे `pip install "pydantic[email]"` के ज़रिए इंस्टॉल किया जा सकता है।

## पूर्ण कार्यशील उदाहरण {#full-working-example}

यह अनुभाग `starlette-admin` के साथ एक पूर्ण और चलाने योग्य SQLModel इंटीग्रेशन प्रदान करता है।

### 1. डिपेंडेंसी इंस्टॉल करें {#1-install-dependencies}

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

`fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे आप `fastapi dev` चलाकर डेवलपमेंट सर्वर शुरू कर सकते हैं।

### 2. ऐप्लिकेशन बनाएँ {#2-create-the-application}

निम्नलिखित कोड को `main.py` नाम की फ़ाइल में सेव करें।

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts"]


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
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

तीन वर्णों से छोटा `title` या दो वर्णों से छोटा `name` सबमिट करने पर फ़ॉर्म त्रुटि को संबंधित दोषपूर्ण फ़ील्ड से जोड़कर पुनः रेंडर होता है।

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

> **उन्नत उदाहरण:** रिपॉज़िटरी में [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) एक पूर्ण-फ़ीचर्ड CMS उदाहरण रखता है, जिसमें रिलेशनशिप, इनलाइन व्यू, एक्शन, फ़िल्टर्स, इवेंट, और एक्सपोर्ट शामिल हैं।

## आगे क्या पढ़ें {#what-to-read-next}

* **[SQLAlchemy](sqlalchemy.md):** वह बैकएंड जिस पर यह इंटीग्रेशन आधारित है; इसमें इंजन, सेशन, ट्रांज़ैक्शन, और फ़िल्टर रजिस्ट्री शामिल हैं।
* **[व्यूज़](../user-guide/views.md):** बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्पों का अन्वेषण करें।
* **[फ़िल्टर्स](../user-guide/filters.md):** फ़िल्टर बिल्डर के बारे में जानें और देखें कि ORM-विशिष्ट फ़िल्टर्स कैसे जुड़ते हैं।
