---
title: SQLAlchemy इंटीग्रेशन
description: जानें कि starlette-admin को SQLAlchemy के साथ कैसे एकीकृत करें। FastAPI
  में अपने रिलेशनल डेटाबेस मॉडल के लिए एक एडमिन डैशबोर्ड बनाएँ।
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

SQLAlchemy बैकएंड, `BaseModelView` के लिए संदर्भ इम्प्लीमेंटेशन का काम करता है। इसे केवल SQLAlchemy 2 `DeclarativeBase` मॉडल के विरुद्ध ही परखा गया है। अन्य बैकएंड (जैसे Beanie, MongoEngine, Tortoise ORM, या आपका कोई कस्टम इम्प्लीमेंटेशन) अपने-अपने डेटा स्टोर के विरुद्ध यही समान अनुबंध पूरा करते हैं।

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


class ProductView(ModelView):
    fields = ["id", "name", "price"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

## इंस्टॉल {#install}

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

यदि आप SQLite का उपयोग नहीं करना चाहते हैं, तो `aiosqlite` की जगह `asyncpg` (PostgreSQL) या `aiomysql`/`asyncmy` (MySQL) इस्तेमाल करें। डेटाबेस ड्राइवर केवल एसिंक्रोनस इंजन के लिए प्रासंगिक है। सिंक्रोनस इंजन, प्लेन SQLAlchemy द्वारा आवश्यक स्टैंडर्ड DBAPI ड्राइवर (जैसे `psycopg2` या `pymysql`) का उपयोग करता है और `starlette-admin` से किसी अतिरिक्त पैकेज की आवश्यकता नहीं होती।

## एसिंक्रोनस बनाम सिंक्रोनस इंजन {#async-vs-sync-engines}

`Admin`, `Engine` या `AsyncEngine` — दोनों में से कोई भी स्वीकार करता है। जो इंस्टेंस आपने कॉन्फ़िगर किया है, वही पास करें:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` रिक्वेस्ट के समय इंजन का एक बार निरीक्षण करता है और मेल खाती सेशन टाइप खोलता है: `AsyncEngine` के लिए `AsyncSession` या सिंक्रोनस `Engine` के लिए प्लेन `Session`। आंतरिक रूप से, `ModelView`, `isinstance(session, AsyncSession)` पर ब्रांच करता है। सिंक्रोनस सेशन के लिए, यह इवेंट लूप को ब्लॉक होने से बचाने के लिए ब्लॉकिंग कॉल को `anyio.to_thread.run_sync` के ज़रिए रूट करता है।

## इंजन के बदले `sessionmaker` पास करना {#passing-a-sessionmaker-instead-of-an-engine}

`session_provider` पैरामीटर एक `sessionmaker` या `async_sessionmaker` भी स्वीकार करता है। जब आपको सेशन को सीधे कॉन्फ़िगर करना हो, तो खाली इंजन की जगह सेशन मेकर प्रदान करें।

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
सेशन मिडलवेयर, आंतरिक रूप से सेशन बनाने के बजाय प्रत्येक रिक्वेस्ट के लिए नया सेशन जनरेट करने हेतु `session_maker()` को कॉल करता है।

## `sqla.Admin` और `sqla.ModelView` {#sqlaadmin-and-sqlamodelview}

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin`, `starlette_admin.BaseAdmin` के समान आर्ग्युमेंट्स के साथ-साथ एक आवश्यक पोज़िशनल आर्ग्युमेंट स्वीकार करता है: `session_provider`। यह प्रोवाइडर एक `Engine`, `AsyncEngine`, `sessionmaker`, या `async_sessionmaker` हो सकता है। इनिशियलाइज़ेशन के दौरान, एडमिनिस्ट्रेशन पैनल आपके चुने हुए प्रोवाइडर से बंधित एक सेशन मिडलवेयर कॉन्फ़िगर करता है और उसे मिडलवेयर स्टैक के सबसे आगे डालता है। यह तंत्र गारंटी देता है कि `request.state.session` हर रिक्वेस्ट पर आपके व्यू कोड के चलने से पहले स्वतः पॉप्युलेट हो जाए।

`sqla.ModelView` को एक SQLAlchemy मॉडल की आवश्यकता होती है। इनिशियलाइज़ेशन पर, यह मॉडल का निरीक्षण करके फ़ील्ड्स का स्वतः पता लगाता है, प्राइमरी कीज़ को मैनेज करता है, और फ़िल्टर रजिस्ट्री को सीधे मेटाडेटा से कॉन्फ़िगर करता है।

## मॉडल घोषणा {#model-declaration}

अपने मॉडल को स्टैंडर्ड SQLAlchemy घोषणात्मक क्लास के उपयोग से परिभाषित करें:

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

यदि आप व्यू पर `fields` सेट नहीं करते हैं, तो `ModelView` मॉडल पर घोषित हर एट्रिब्यूट का उपयोग उसी क्रम में करता है जिस क्रम में वे दिखाई देते हैं। प्राइमरी की स्वतः पहचाना जाता है और create तथा edit फ़ॉर्म से हटा दिया जाता है। हर अन्य कॉलम और रिलेशनशिप स्वतः ही एक उपयुक्त फ़ील्ड टाइप (जैसे `IntegerField`, `StringField`, `EnumField`, `HasOne`, या `HasMany`) में बदल जाता है।

## स्वतः पहचाने गए डिफ़ॉल्ट {#auto-detected-defaults}

किसी कॉलम का Python-साइड `default=` कॉन्फ़िगरेशन, creation फ़ॉर्म पहली बार खोलने पर स्वतः पॉप्युलेट हो जाता है। आपको यह परिभाषा फ़ील्ड पर दोहराने की आवश्यकता नहीं है:

```python
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    views: Mapped[int] = mapped_column(default=0)  # form shows 0
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )  # form shows now()
```

एक स्केलर डिफ़ॉल्ट (`default=0`) परिभाषित अवस्था में हूबहू कॉपी होता है। एक कॉलेबल डिफ़ॉल्ट (`default=datetime.utcnow` या `default=uuid.uuid4`) फ़ॉर्म रेंडर होते समय एक बार ट्रिगर होता है, जिससे उपयोगकर्ता फ़ंक्शन के `repr` फ़ॉर्मैट के बजाय एक वास्तविक मान देख पाता है।

!!! important
    प्राइमरी की कॉलम को परिभाषित होने पर भी कभी कोई प्री-फ़िल्ड डिफ़ॉल्ट नहीं मिलता। उन्हें सर्वर-जनरेटेड (`autoincrement` या किसी sequence के माध्यम से) माना जाता है और वे create तथा edit फ़ॉर्म से पूरी तरह हटा दिए जाते हैं। SQL-expression डिफ़ॉल्ट (जैसे `server_default=func.now()` या डेटाबेस-साइड `DEFAULT`) भी छोड़ दिए जाते हैं, क्योंकि दिखाने के लिए कोई Python-स्तर का मान नहीं होता। इन मानों को इंसर्शन के समय पॉप्युलेट करने का काम डेटाबेस संभालता है।

## रिलेशनशिप फ़ील्ड्स {#relationship-fields}

मॉडल पर SQLAlchemy का `relationship()` स्वतः ही `RelationshipProperty.direction` एट्रिब्यूट के आधार पर `HasOne` (many-to-one या one-to-one) या `HasMany` (one-to-many या many-to-many) में बदल जाता है। आपको फ़ील्ड टाइप स्पष्ट रूप से घोषित करने की आवश्यकता नहीं है:

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")
```

`PostView.fields = ["id", "title", "author"]` सेट करने पर `author`, Select2 ड्रॉपडाउन के रूप में रेंडर होता है। यह ड्रॉपडाउन संबंधित व्यू के `/_api/{key}/relation-lookup` एंडपॉइंट से AJAX के माध्यम से पॉप्युलेट होता है (जहाँ `{key}` `author` को दर्शाता है, जो `AuthorView` की key है)। ऐप्लिकेशन कभी भी authors की पूरी टेबल एक ही बार में पेज पर लोड नहीं करता। संबंधित टेबल में हज़ारों पंक्तियाँ होने पर यह lazy-loading व्यवहार परफ़ॉर्मेंस के लिए अत्यंत महत्वपूर्ण है। इसी प्रकार, `AuthorView.fields = ["id", "name", "posts"]` सेट करने पर `posts`, उसी lookup एंडपॉइंट का उपयोग करते हुए एक multi-select कंट्रोल के रूप में रेंडर होता है।

## कंपोज़िट प्राइमरी कीज़ {#composite-primary-keys}

कंपोज़िट प्राइमरी की के लिए एकाधिक `primary_key=True` कॉलम का उपयोग करने वाले मॉडल बिना किसी अतिरिक्त कॉन्फ़िगरेशन के out of the box समर्थित हैं। इसमें वे परिदृश्य भी शामिल हैं जहाँ हर प्राइमरी-की कॉलम एक फ़ॉरेन की के रूप में भी कार्य करता है, जैसे many-to-many एसोसिएशन ऑब्जेक्ट।

पूरी तरह चलाने योग्य उदाहरण के लिए [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks) देखें।

## फ़िल्टर रजिस्ट्री {#filter-registry}

हर फ़ील्ड टाइप को `SqlaFilterRegistry` से फ़िल्टर्स का एक डिफ़ॉल्ट सेट मिलता है। इन्हें फ़ील्ड की क्लास हायरार्की को traverse करके resolve किया जाता है, जैसा कि [फ़िल्टर्स](../user-guide/filters.md) दस्तावेज़ में विस्तार से बताया गया है। एक महत्वपूर्ण SQLAlchemy-विशिष्ट बात यह है कि हर फ़िल्टर किसी क्वेरी फ़्रैगमेंट में कैसे बदलता है। इस मॉड्यूल की हर `apply()` मेथड एक स्टैंडअलोन SQLAlchemy boolean क्लॉज़ (जैसे `column == value` या `column.between(a, b)`) रिटर्न करती है।

!!! note
    रिलेशनशिप पर `Is null` फ़िल्टर, `column.is_(None)` के बजाय `~column.has()` (many-to-one रिलेशन के लिए) या `~column.any()` (one-to-many तथा many-to-many रिलेशन के लिए) का मूल्यांकन करता है। चूँकि रिलेशनशिप एट्रिब्यूट कोई स्टैंडर्ड कॉलम नहीं है जिसमें `NULL` मान हो, इसकी nullability पूरी तरह इस बात पर निर्भर करती है कि कोई संबंधित पंक्तियाँ मौजूद हैं या नहीं।

!!! note
    SQLAlchemy बैकएंड, Beanie और MongoEngine के विपरीत, `ArrayInFilter` या `ArrayNotInFilter` (list-valued कॉलम के लिए "is one of" फ़िल्टर्स) प्रदान नहीं करता। यदि आपको `TagsField`-आधारित JSON या ARRAY कॉलम पर "is one of" फ़िल्टरिंग की आवश्यकता है, तो आपको अपना `apply()` लॉजिक स्वयं लिखना होगा। अधिक जानकारी के लिए [कस्टम फ़िल्टर्स](../advanced/custom-filters.md) दस्तावेज़ देखें।

## सेशन और ट्रांज़ैक्शन {#sessions-and-transactions}

सेशन मिडलवेयर प्रत्येक रिक्वेस्ट के लिए ठीक एक सेशन खोलता है और उसे सुरक्षित रूप से `request.state.session` पर संग्रहित करता है। एसिंक्रोनस इंजन (या `async_sessionmaker`) का उपयोग करते समय यह ऑब्जेक्ट एक `AsyncSession` होगा, अन्यथा एक स्टैंडर्ड `Session`। रिक्वेस्ट द्वारा स्पर्श किया गया हर घटक इसी एक सेशन को साझा करता है। लिस्ट क्वेरी, फ़ॉर्म के भीतर रिलेशनशिप lookups, और हुक, एक्शन, या एंडपॉइंट में चलने वाला कोई भी कस्टम लॉजिक — सभी ठीक इसी एक ट्रांज़ैक्शन के भीतर संचालित होंगे। अंतर्निहित इंजन टाइप चाहे जो हो, आप इसे समान रूप से प्राप्त करते हैं:

```python
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    @action(name="publish", text="Publish selected")
    async def publish(self, request: Request, pks: list[Any]) -> str:
        session: AsyncSession = request.state.session
        for post in await self.find_by_pks(request, pks):
            post.status = "PUBLISHED"
            session.add(post)
        await session.flush()
        return f"{len(pks)} post(s) published."
```

सिंक्रोनस इंजन का उपयोग करते समय, `request.state.session` एक स्टैंडर्ड `Session` होता है और `session.flush()` बिना `await` के कॉल किया जाता है। ऊपर दिए गए कोड स्निपेट का शेष भाग अपरिवर्तित रहता है। आपको अलग से कोई `get_session()` डिपेंडेंसी इंपोर्ट करने की आवश्यकता नहीं है। रूट हैंडलर को कॉल करने से पहले सेशन मिडलवेयर कनेक्शन स्थापित करता है, इसलिए सेशन आपके हुक या एक्शन के चलने से पहले ही रिक्वेस्ट से जुड़ जाता है।

**प्रति रिक्वेस्ट एक commit।** आपको कभी भी मैन्युअल रूप से `session.commit()` को कॉल नहीं करना चाहिए। `flush()` को कॉल करना (या read-only क्वेरी करते समय कुछ न करना) पर्याप्त है। सेशन मिडलवेयर, रूट हैंडलर के रिटर्न करने के बाद सेशन को ठीक एक बार commit करता है, बशर्ते रिस्पॉन्स सफलता दर्शाए। यदि कोई त्रुटि होती है, तो मिडलवेयर पूरे ट्रांज़ैक्शन को स्वतः रोल बैक कर देता है:

* यदि हैंडलर कोई exception उठाता है, तो सेशन रोल बैक हो जाता है और ऐप्लिकेशन उस exception को दोबारा उठा देता है।
* यदि हैंडलर `status_code >= 400` वाला रिस्पॉन्स रिटर्न करता है (जैसे फ़ॉर्म सत्यापन विफलता), तो सेशन रोल बैक हो जाता है और सर्वर रिस्पॉन्स को अपरिवर्तित रूप से लौटा देता है। यह रोल बैक अत्यंत महत्वपूर्ण है, क्योंकि उस चरण में ट्रांज़ैक्शन में विफल flush हो सकता है। उसे commit करने से अनजाने में आंशिक रूप से लिखा गया रिकॉर्ड सहेजा जा सकता है।
* यदि commit ऑपरेशन स्वयं कोई exception उठाता है (जैसे flush के समय पकड़ी गई डेटाबेस constraint violation), तो सेशन रोल बैक हो जाता है और exception को दोबारा उठा देता है।

अन्य सभी परिदृश्यों में, जहाँ हैंडलर 2xx या 3xx रिस्पॉन्स देता है, मिडलवेयर सेशन को commit करता है और कनेक्शन जारी कर देता है। यही लाइफ़साइकल बताता है कि ऊपर दिखाया गया `publish` एक्शन स्पष्ट commit या close स्टेटमेंट की माँग क्यों नहीं करता। सेशन मिडलवेयर आपका कोड चलने से पहले सेशन खोलता है और फिर रिस्पॉन्स के व्यू से निकलने से पहले commit या रोल बैक ऑपरेशन संभाल लेता है।

## Pydantic सत्यापन {#pydantic-validation}

आप प्लेन SQLAlchemy मॉडल का उपयोग करते हुए भी सेव करने से पहले फ़ॉर्म डेटा को किसी Pydantic स्कीमा के विरुद्ध सत्यापित करना चाह सकते हैं। ऐसे में, `starlette_admin.contrib.sqla.ext.pydantic.ModelView` एक `pydantic_model` आर्ग्युमेंट स्वीकार करता है ताकि अंतर्निहित SQLAlchemy कॉलम टाइप के बजाय उस स्कीमा के विरुद्ध सत्यापन किया जा सके:

```python
from sqlalchemy import ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///users.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip().split()) < 2:
            raise ValueError("Must include both first and last name (e.g. John Doe)")
        return v


admin = Admin(engine, title="Users Admin", secret_key="change-me")
admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

`full_name="Madonna"` (एक एकल शब्द) सबमिट करने पर `validate_full_name` मेथड विफल हो जाती है। तब create या edit फ़ॉर्म त्रुटि को स्पष्ट रूप से `full_name` फ़ील्ड से जोड़कर पुनः रेंडर होता है। अंतर्निहित SQLAlchemy `String(100)` कॉलम में ऐसा कोई नियम नहीं है। यह बाध्यता पूरी तरह `UserIn` Pydantic मॉडल के भीतर स्थित है। पूर्ण उदाहरण के लिए [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi) देखें, जिसमें उसी एडमिनिस्ट्रेशन पैनल से जुड़ा एक द्वितीयक व्यू (`PostIn`) भी शामिल है।

## पूर्ण कार्यशील उदाहरण {#full-working-example}


यहाँ starlette-admin के साथ एक पूर्ण SQLAlchemy उदाहरण दिया गया है। चलाने योग्य संस्करण के लिए [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) देखें।

### 1. डिपेंडेंसी इंस्टॉल करें {#1-install-dependencies}

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

`fastapi[standard]` पैकेज में FastAPI CLI शामिल है, जिससे आप `fastapi dev` चलाकर डेवलपमेंट सर्वर शुरू कर सकते हैं।

### 2. ऐप्लिकेशन बनाएँ {#2-create-the-application}

निम्नलिखित कोड को `main.py` के रूप में सेव करें। यह स्क्रिप्ट प्रदर्शन हेतु एक लोकल SQLite डेटाबेस (`blog.db`) का उपयोग करती है, हालाँकि Starlette-Admin PostgreSQL, MySQL, और SQLite के लिए सिंक्रोनस तथा एसिंक्रोनस दोनों इंजनों का समर्थन करता है।

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import SlugField
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")


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
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
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

अब आप अपने ब्राउज़र में [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) पर जाकर एडमिन डैशबोर्ड देख सकते हैं और उसके साथ इंटरैक्ट कर सकते हैं।

---

## आगे क्या पढ़ें {#what-to-read-next}

* **[व्यूज़](../user-guide/views.md)**: बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्पों का अन्वेषण करें।
* [फ़िल्टर्स](../user-guide/filters.md): फ़िल्टर रजिस्ट्री द्वारा संचालित फ़िल्टर बिल्डर और URL फ़ॉर्मैट का विवरण।
* [व्यूज़](../user-guide/views.md): हर `ModelView` कॉन्फ़िगरेशन विकल्प की व्यापक सूची (backend-agnostic)।
* [SQLModel](sqlmodel.md): इस बैकएंड के चारों ओर एक पतली wrapper, जो फ़ॉर्म में Pydantic सत्यापन जोड़ती है।
* [Beanie](beanie.md): MongoDB डेटाबेस के विरुद्ध समान `ModelView` API के उपयोग की गाइड।
* [Tortoise ORM](tortoise.md): starlette-admin में बिल्ट-इन अन्य रिलेशनल बैकएंड।
