---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# starlette-admin के साथ FastAPI में 5 मिनट में एडमिन पैनल जोड़ें {#add-an-admin-panel-to-fastapi-in-5-minutes-with-starlette-admin}

_2026-07-13_

आपने API शिप कर दी है। अब आपकी टीम में किसी को इसके पीछे का डेटा एडिट करने की ज़रूरत है: किसी रिकॉर्ड की टाइपिंग की ग़लती ठीक करना, कोई पोस्ट अनपब्लिश करना, या देखना कि यूज़र ने असल में क्या सबमिट किया। मानक विकल्प आम तौर पर महँगे होते हैं:

| विकल्प | दिक़्क़त |
| --- | --- |
| **कस्टम CRUD फ़्रंटएंड** | इसे बनाने और मैनेज करने में डेवलपर के हफ़्तों भर वक़्त की ख़र्च होती है। |
| **सीधा डेटाबेस एक्सेस** | यह सुरक्षा और डेटा इंटीग्रिटी के लिए बहुत बड़ा जोखिम पैदा करता है। |
| **Django Admin / Flask Admin** | यह या तो फ़्रेमवर्क बदलने पर मजबूर करता है या सिंक्रोनस WSGI पर टिका रहता है, जो आपकी एसिंक्रोनस ASGI ऐप्लिकेशन को ब्लॉक कर देता है। |
| **starlette-admin** | **यह बिना किसी फ़्रंटएंड कोड के आपकी ऐप्लिकेशन पर तुरंत माउंट हो जाता है।** |

`starlette-admin` किसी भी Starlette-आधारित ऐप्लिकेशन के साथ काम करता है — और FastAPI ठीक वही है।

यह गाइड आपको पाँच मिनट में एक ख़ाली फ़ाइल से लेकर चलने वाले बैक ऑफ़िस तक ले जाती है। आप पेजिनेटेड लिस्ट, सर्च फ़ंक्शनैलिटी, सॉर्ट करने योग्य कॉलम, अपने मौजूदा Pydantic स्कीमा से वैलिडेट होने वाले क्रिएट और एडिट फ़ॉर्म, डिलीशन कन्फ़र्मेशन और CSV एक्सपोर्ट बनाएँगे — सब कुछ सीधे एक SQLAlchemy मॉडल से जनरेट होकर।

पूरा चलने योग्य कोड [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>) में उपलब्ध है।

## मिनट 1: इंस्टॉल {#minute-1-install}

आपको तीन पैकेज चाहिए: एडमिन फ़्रेमवर्क, ORM, और FastAPI ख़ुद।

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic FastAPI के साथ ही आता है, जो आगे चलकर मायने रखता है: एडमिन पैनल ठीक वही स्कीमा दोबारा इस्तेमाल कर सकता है जिनका इस्तेमाल आपकी API वैलिडेशन के लिए करती है।

## मिनट 2 और 3: पूरा ऐप {#minutes-2-and-3-the-complete-app}

`main.py` बनाएँ। यही पूरी ऐप्लिकेशन है:

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

ग़ौर करें कि क्या मौजूद नहीं है। यहाँ कोई टेम्पलेट नहीं है, एडमिन पेजों के लिए कोई रूट हैंडलर नहीं है, कोई सीरिएलाइज़र नहीं है, और न ही कोई फ़ील्ड कॉन्फ़िगरेशन है। `starlette-admin` SQLAlchemy की कॉलम मेटाडेटा पढ़ता है और पूरा इंटरफ़ेस अपने आप तैयार कर लेता है: दोनों `String` कॉलम के लिए लिमिट वाले टेक्स्ट इनपुट, `Text` कंटेंट के लिए टेक्स्टएरिया, और `published_at` के लिए डेटाटाइम पिकर।

हाइलाइट की गई तीनों लाइनें ही आपके एकमात्र इंटीग्रेशन पॉइंट हैं। `Admin` डेटाबेस इंजन से बाइंड करता है, `add_view` मॉडल को साइडबार में रजिस्टर करता है, और `mount_to` सब कुछ आपकी मौजूदा FastAPI ऐप्लिकेशन से `/admin` पाथ के तहत जोड़ देता है। आपकी API रूट बिल्कुल नहीं बदलतीं; एडमिन पैनल बस एक माउंट किए गए सब-ऐप्लिकेशन की तरह काम करता है।

## मिनट 4: इसे चलाएँ {#minute-4-run-it}

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

[http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) खोलें और साइडबार में **Post** पर क्लिक करें। बिना किसी अतिरिक्त सेटअप के आपको ये सब मिलता है:

- सभी पोस्ट की एक पेजिनेटेड, सॉर्ट करने योग्य लिस्ट व्यू।
- हर कॉलम टाइप के अनुसार सही इनपुट विजेट से लैस क्रिएट और एडिट फ़ॉर्म।
- हर रिकॉर्ड के लिए एक डिटेल व्यू पेज।
- कन्फ़र्मेशन डायलॉग के साथ बैच डिलीशन की सुविधा।
- मौजूदा लिस्ट के लिए CSV और Excel एक्सपोर्ट।

आपकी API पहले की तरह ट्रैफ़िक संभालती रहती है। यह पक्का करने के लिए कि सब कुछ बरक़रार है, [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) देखें।

## मिनट 5: इसे कस्टम-निर्मित जैसा बनाएँ {#minute-5-make-it-feel-hand-built}

डिफ़ॉल्ट व्यू एक पूरा CRUD इंटरफ़ेस देता है, लेकिन एक असली बैक ऑफ़िस अपनी पसंद के मुताबिक़ ढला हुआ होना चाहिए: आपका फ़ील्ड क्रम, आपका फ़ॉर्म लेआउट, और आपकी सर्च स्थिति। `ModelView` को सबक्लास करना वही जगह है जहाँ `starlette-admin` अपनी पूरी क्षमता खोलता है। `add_view` कॉल को एक कॉन्फ़िगर किए गए व्यू से बदलें:

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

इस एक क्लास में चार दमदार अपग्रेड होते हैं:

- **`SlugField(populate_from="title")`**: ऑपरेटर के टाइटल टाइप करते ही slug अपने आप जनरेट हो जाता है; आपकी तरफ़ से कस्टम JavaScript की ज़रूरत ज़ीरो रहती है।
- **`ComputedField`**: ऐसी वैल्यू दिखाता है जो डेटाबेस में मौजूद नहीं है। वर्ड काउंट रेंडर के समय एक साधारण Python कॉलेबल से निकाला जाता है।
- **`form_layout`**: फ़ॉर्म को तार्किक रो में व्यवस्थित करता है: टाइटल और slug साथ-साथ, कंटेंट पूरी चौड़ाई में, और प्रकाशन की तारीख़ नीचे।
- **`search_auto_submit`**: ऑपरेटर के टाइप करते ही `searchable_fields` में शामिल सभी कॉलम पर लिस्ट को डायनामिक रूप से फ़िल्टर करता है।

## ग़लत डेटा ठुकराना: वही स्कीमा इस्तेमाल करें जो आपके पास पहले से है {#rejecting-bad-data-use-the-schema-you-already-have}

ऑपरेटर ग़लतियाँ करते हैं, यानी एडमिन को आपके नियम सर्वर साइड पर लागू करने होंगे। फ़ायदा यह है कि वे नियम आप पहले ही लिख चुके हैं। हर FastAPI प्रोजेक्ट अपनी रिक्वेस्ट बॉडी Pydantic मॉडल से वैलिडेट करता है, इसलिए आपके कोडबेस में कहीं न कहीं ऐसा स्कीमा मौजूद है जो कुछ यूँ दिखता है:

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

वही वैलिडेशन लॉजिक दो बार लिखने की बजाय, एडमिन को अपना मौजूदा मॉडल सौंप दें। `ext.pydantic` एक्सटेंशन एक ऐसा `ModelView` देता है जो डेटाबेस तक पहुँचने से पहले हर फ़ॉर्म सबमिशन को एक Pydantic मॉडल से प्रोसेस करता है। अपना `ModelView` इम्पोर्ट एक्सटेंशन की ओर पॉइंट करें, `Admin` को जैसा है वैसा रहने दें, और स्कीमा पास कर दें:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

`PostView` की क्लास बॉडी बिल्कुल वही रहती है; सिर्फ़ नए इम्पोर्ट के ज़रिए उसकी बेस क्लास बदलती है।

इंटीग्रेशन बिल्कुल सहज है। क्रिएट और एडिट के दौरान हर कंस्ट्रेंट लागू होता है: लंबाई की सीमाएँ, slug रेगेक्स, और कस्टम `field_validator`। हर Pydantic एरर सीधे अपने संबंधित फ़ॉर्म फ़ील्ड से मैप होकर इनलाइन रेंडर होता है — बिल्कुल किसी हाथ से बने फ़ॉर्म जैसा। स्कीमा में `id` को ऑप्शनल रखना न भूलें ताकि क्रिएट फ़ॉर्म, जिसमें शुरू में ID नहीं होती, फिर भी वैलिडेट हो सके।

इससे सिंगल सोर्स ऑफ़ ट्रुथ क़ायम होता है। जब आपकी API स्कीमा में कोई नया नियम आता है, तो एडमिन उसे अगली ही रिक्वेस्ट पर लागू कर देता है — एडमिन-साइड कोड में कोई बदलाव किए बिना।

## एक फ़ुर्सत का मिनट है? पोस्ट को एक लेखक दें {#one-spare-minute-give-posts-an-author}

असली डेटा रिलेशनशिप पर टिका होता है, और एडमिन उन्हें उसी ज़ीरो-कॉन्फ़िगरेशन तरीक़े से संभालता है। एक `User` मॉडल जोड़ें और उसे `Post` से लिंक करें:

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

यूज़र मॉडल को उसी स्कीमा-चालित पैटर्न से रजिस्टर करें। `EmailStr` और `HttpUrl` फ़ॉर्मैट वैलिडेशन अपने आप देते हैं, और `email-validator` पहले से ही `fastapi[standard]` में शामिल है:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

इस बार कॉन्फ़िगर करने को कुछ नहीं है, इसलिए एक्सटेंशन वाले `ModelView` का इस्तेमाल बिना सबक्लास बनाए सीधे किया गया है।

आख़िर में, `PostIn` में दो लाइनें जोड़कर लेखक को अनिवार्य बनाएँ:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` की कोई डिफ़ॉल्ट वैल्यू नहीं है, यानी बिना लेखक वाली पोस्ट किसी और वैलिडेशन एरर की तरह ठुकरा दी जाएगी। टाइप सीधे SQLAlchemy की `User` क्लास है, क्योंकि वैलिडेशन चलने से पहले एडमिन चुनी गई ID को एक ORM इंस्टेंस में बदल देता है। इसीलिए `arbitrary_types_allowed` ज़रूरी है (`ConfigDict` `pydantic` से इम्पोर्ट होता है)।

इसके बाद, `"user"` को `PostView.fields` और `form_layout` में जोड़ें ताकि लेखक पोस्ट फ़ॉर्म में दिखे। यह फ़ील्ड कोई साधारण ड्रॉपडाउन नहीं है। यह एक सेलेक्ट इनपुट है जिसमें सर्वर-साइड ऑटोकम्प्लीट है — ऑपरेटर के टाइप करते ही यह आपके यूज़र्स में खोज करता है, और यूज़र डिटेल पेज हर संबंधित पोस्ट का लिंक वापस दिखाता है।

!!! note
`create_all` मौजूदा टेबल को नहीं बदलता, इसलिए नए `user_id` कॉलम को शामिल करने के लिए रीस्टार्ट करने से पहले `blog.db` को डिलीट करना होगा।

## डिप्लॉय करने से पहले {#before-you-deploy}

!!! warning
`secret_key` पैरामीटर उस सेशन कुकी पर सिग्नेचर करता है जिसका इस्तेमाल CSRF सुरक्षा और फ़्लैश मैसेज के लिए होता है। डिप्लॉयमेंट से पहले प्लेसहोल्डर को अपनी सेटिंग्स से ली गई किसी लंबी, रैंडम वैल्यू से बदलें, और ध्यान रखें कि उसे सोर्स कोड में हार्डकोड करने की बजाय एनवायरनमेंट वेरिएबल से लोड किया जाए।

!!! note
lifespan में दिया गया `Base.metadata.create_all(engine)` क्विकस्टार्ट की सुविधा के लिए है। प्रोडक्शन प्रोजेक्ट में आपकी टेबल माइग्रेशन (जैसे Alembic) से मैनेज होती हैं। उस कॉल को हटा दें और `Admin` को सीधे अपने मौजूदा इंजन पर पॉइंट करें। `starlette-admin` आपका स्कीमा कभी नहीं बदलता; वह सिर्फ़ रो पढ़ता और लिखता है।

## यह डेमो से आगे स्केल होता है {#this-scales-past-the-demo}

ऊपर सब कुछ दो मॉडल का इस्तेमाल करता है, लेकिन यही `ModelView` मैकेनिज़्म एक बड़े बैक ऑफ़िस को सपोर्ट कर सकते हैं। आप आसानी से फ़ाइल और इमेज अपलोड, [रोल-आधारित एक्सेस के साथ ऑथेंटिकेशन](../../user-guide/auth.md), [कस्टम फ़िल्टर](../../user-guide/filters.md), [रो और बैच एक्शन](../../user-guide/actions.md), और पूरा [i18n](../../user-guide/i18n.md) इम्प्लीमेंट कर सकते हैं। जब भी बिल्ट-इन व्यवहार कम पड़े, हर क्वेरी और लाइफ़साइकिल स्टेप एक ओवरराइड हुक देता है। [ट्रैश व्यू के साथ सॉफ़्ट डिलीट](soft-deletes-trash-view.md) जैसे पैटर्न इसी लचीलेपन से बनते हैं।

---

## आगे क्या {#whats-next}

- **[कॉन्सेप्ट्स](../../getting-started/concepts.md):** अभी जो आपने बनाया है उसके पीछे की शब्दावली, जिससे बाक़ी डॉक्यूमेंटेशन सहजता से पढ़ी जा सके।
- **[व्यू](../../user-guide/views.md):** हर `ModelView` विकल्प और परमिशन हुक समेत विस्तृत परिचय।
- **[FastAPI के लिए सॉफ़्ट डिलीट और ट्रैश व्यू](soft-deletes-trash-view.md):** पहला एडवांस रेसिपी, जो सीधे यहीं पेश किए गए ओवरराइड हुक पर बना है।
