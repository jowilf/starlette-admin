---
title: क्विकस्टार्ट
description: हमारे विस्तृत क्विकस्टार्ट गाइड के साथ मिनटों में FastAPI और Starlette
  के लिए पूर्ण कार्यशील CRUD एडमिन इंटरफ़ेस बनाएँ।
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# क्विकस्टार्ट {#quickstart}

मिनटों में एक ब्लॉग के लिए पूर्ण कार्यशील CRUD एडमिन इंटरफ़ेस बनाएँ, जिसमें ऑटो-जनरेटेड फ़ॉर्म, लिस्ट, खोज, इंपोर्ट और एक्सपोर्ट सीधे आपके डेटा मॉडल से संचालित होते हैं।

## इंस्टॉलेशन {#installation}

आवश्यक पैकेज को अपनी पसंदीदा पैकेज मैनेजर से इंस्टॉल करें:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    `fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे आप `fastapi dev` चलाकर डेवलपमेंट सर्वर शुरू कर सकते हैं।

## पूर्ण उदाहरण {#the-complete-example}

`main.py` नाम की फ़ाइल बनाएँ और उसमें निम्नलिखित कोड जोड़ें:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## एप्लिकेशन चलाएँ {#run-the-application}

डेवलपमेंट सर्वर शुरू करें:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

ब्राउज़र खोलें और [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) पर जाएँ।

साइडबार में **Posts** चुनें, फिर **Create** चुनें। अब आप पेजिनेटेड लिस्ट, डिटेल, create, edit और delete पेजों तक पहुँच सकते हैं। यह सिस्टम आपकी मॉडल परिभाषा से इन सभी इंटरफ़ेस को स्वतः जनरेट करता है।

## यह कैसे काम करता है {#how-it-works}

निम्नलिखित सेक्शन एप्लिकेशन के कोर कंपोनेंट समझाते हैं।

### मॉडल {#the-model}

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

यह कोड स्टैंडर्ड SQLAlchemy 2.0 का उपयोग करता है। starlette-admin पैकेज इन एट्रिब्यूट्स पर मैप किए गए कॉलम मेटाडेटा को पढ़कर यह तय करता है कि कौन सा HTML इनपुट जनरेट करना है। उदाहरण के लिए, यह `str` के लिए टेक्स्ट इनपुट, `bool` के लिए चेकबॉक्स और `datetime` के लिए डेटाटाइम पिकर बनाता है।

### व्यू {#the-view}

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` इस रिसोर्स के लिए केंद्रीय ऑब्जेक्ट के रूप में कार्य करता है। `fields` एट्रिब्यूट यह नियंत्रित करता है कि लिस्ट और फ़ॉर्म में कौन से कॉलम दिखें, जबकि `searchable_fields` सर्च बार को सक्षम करता है। एडमिन डैशबोर्ड में `Post` कैसा दिखे और कैसे व्यवहार करे, इसका पूरा कॉन्फ़िगरेशन इसी एक क्लास में रहता है।

!!! note
    उदाहरण `ModelView` को `starlette_admin.contrib.sqla` से इंपोर्ट करता है क्योंकि यह SQLAlchemy पर निर्भर है। यदि आप Beanie, MongoEngine, या Tortoise ORM जैसा कोई दूसरा बैकएंड उपयोग करते हैं, तो आपको `ModelView` को संबंधित contrib पैकेज से इंपोर्ट करना होगा। कॉन्फ़िगरेशन API सभी समर्थित बैकएंड में सुसंगत रहता है।

### Admin {#the-admin}

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

`Admin` क्लास डेटाबेस इंजन को यूज़र इंटरफ़ेस से जोड़ती है।

* `add_view` आपके व्यू को साइडबार में रजिस्टर करता है। वैकल्पिक `icon` पैरामीटर कोई भी मान्य [Font Awesome](https://fontawesome.com/icons) क्लास स्वीकार करता है।
* `mount_to` एडमिन एप्लिकेशन को `/admin` पाथ पर आपके FastAPI या Starlette एप्लिकेशन से जोड़ता है।

!!! warning
    `secret_key` पैरामीटर सेशन डेटा के लिए कुकीज़ पर हस्ताक्षर करता है, जिसमें फ़्लैश संदेश और CSRF सुरक्षा शामिल हैं। प्रोडक्शन वातावरण में आपको उदाहरण मान को लंबी, यादृच्छिक और सुरक्षित रूप से जनरेट की गई स्ट्रिंग से बदलना होगा। लाइव डिप्लॉयमेंट में कभी भी प्लेसहोल्डर मान का उपयोग न करें।

## दूसरा मॉडल जोड़ें {#add-a-second-model}

आप असीमित संख्या में मॉडल रजिस्टर कर सकते हैं। उदाहरण के लिए, `Tag` मॉडल और उसका संबंधित व्यू जोड़ने के लिए, क्लास परिभाषित करें और `add_view` को फिर से कॉल करें:

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

साइडबार में **Posts** और **Tags** दोनों को देखने के लिए ब्राउज़र विंडो को रिफ़्रेश करें। अब प्रत्येक रिसोर्स में अपनी पूर्ण कार्यशील लिस्ट, create, edit और delete पेज मौजूद हैं।

---

## अगले चरण {#next-steps}

* **[अवधारणाएँ](concepts.md):** यहाँ पेश की गई अवधारणाओं की शब्दावली जानें ताकि उपयोगकर्ता गाइड में बेहतर ढंग से नेविगेट कर सकें।
* **[Admin](../user-guide/admin.md):** ब्रांडिंग, थीमिंग, प्रमाणीकरण, सुरक्षा और अंतर्राष्ट्रीयकरण सहित `Admin(...)` के सभी विकल्प देखें।
* **[व्यूज़](../user-guide/views.md):** अपनी डेटा प्रस्तुति को अनुकूलित करने के लिए उपलब्ध हर `ModelView` कॉन्फ़िगरेशन विकल्प देखें।
