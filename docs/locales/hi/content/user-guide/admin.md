---
title: एडमिन कॉन्फ़िगरेशन
description: अपना starlette-admin इंस्टेंस कॉन्फ़िगर करें और थीमिंग, राउटिंग तथा समग्र
  सिक्योरिटी सेटिंग्स कस्टमाइज़ करें।
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# एडमिन {#admin}

एडमिन-व्यापी हर सेटिंग आप keyword आर्ग्युमेंट के रूप में `Admin` क्लास को पास करते हैं: navbar का टाइटल, माउंट लोकेशन, CSRF और ऑथेंटिकेशन कॉन्फ़िगरेशन, और रेंडर होने वाली थीम।

## बेसिक उपयोग {#basic-usage}

शुरुआत करें अपने ऑब्जेक्ट-रिलेशनल मैपर (ORM) से मैच करने वाले `contrib` पैकेज से `Admin` क्लास इंपोर्ट करके:

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

SQLAlchemy इस्तेमाल करने वाला एक न्यूनतम कॉन्फ़िगरेशन:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` navbar का टेक्स्ट और HTML `<title>` टैग सेट करता है।
* `base_url` वह पाथ प्रीफ़िक्स तय करता है जहाँ एडमिन माउंट होता है।
* `secret_key` CSRF और flash कुकीज़ पर सिग्नेचर करता है।
* `add_view` एक व्यू रजिस्टर करता है, और `mount_to` एडमिन के रूट और मिडलवेयर बनाकर उन्हें आपकी एप्लिकेशन पर माउंट कर देता है।

हर `Admin` क्लास नीचे वर्णित सारे कॉन्फ़िगरेशन विकल्प स्वीकार करती है, और कुछ बैकएंड-विशिष्ट व्यवहार भी जोड़ती हैं:

* `contrib.sqla.Admin(session_provider, ...)` पहला positional आर्ग्युमेंट `Engine`, `AsyncEngine`, `sessionmaker` या `async_sessionmaker` लेता है और आपके लिए `DBSessionMiddleware` जोड़ देता है। `contrib.sqlmodel.Admin` वही क्लास है, दोबारा एक्सपोर्ट की हुई। [SQLAlchemy](../integrations/sqlalchemy.md) और [SQLModel](../integrations/sqlmodel.md) देखें।
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` और `contrib.tortoise.Admin` कोई एक्स्ट्रा कंस्ट्रक्टर आर्ग्युमेंट नहीं लेते, क्योंकि Beanie, MongoEngine और Tortoise ORM अपने कनेक्शन एडमिन के बाहर खुद संभालते हैं। `mongoengine.Admin` `mount_to` में एक GridFS फ़ाइल-सर्विंग रूट भी रजिस्टर करता है। [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) और [Tortoise ORM](../integrations/tortoise.md) देखें।

## पूरा रेफ़रेंस {#full-reference}

`Admin` कंस्ट्रक्टर नीचे दिए सारे पैरामीटर keyword आर्ग्युमेंट के रूप में स्वीकार करता है।

### पहचान और ब्रांडिंग {#identity-and-branding}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Navbar टेक्स्ट और `<title>` टैग। |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | `title` की जगह navbar में दिखने वाला लोगो। साधारण URL पास करें, या ऐसा कॉलेबल जो उसे हर रिक्वेस्ट पर तय करे — उदाहरण के लिए प्रति-टेनेंट ब्रांडिंग के लिए। |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | साइन-इन पेज पर `logo_url` की जगह दिखने वाला लोगो। सेट न होने पर `logo_url` पर लौट आता है। |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Favicon `<link>` href। |

`logo_url`, `login_logo_url` और `favicon_url` में से हर एक या तो स्ट्रिंग स्वीकार करता है या `(request) -> str | None` कॉलेबल। कॉलेबल तब इस्तेमाल करें जब ब्रांडिंग रिक्वेस्ट पर निर्भर हो — जैसे मल्टी-टेनेंट एप्लिकेशन में या जब आप कई hostnames सर्व करें:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### माउंटिंग {#mounting}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | URL प्रीफ़िक्स जिसके तहत एडमिन माउंट होता है। |
| `route_name` | `str` | `"admin"` | Starlette माउंट नाम। हर इंटरनल लिंक (`list`, `edit`, exports, static assets) `request.url_for(route_name + ":list", ...)` कॉल करके बनता है। |

एक ही एप्लिकेशन में एक से अधिक `Admin` चलाने के लिए हर इंस्टेंस को अलग `base_url` और `route_name` दें। वरना एक एडमिन के बनाए लिंक दूसरे पर रिज़ॉल्व हो सकते हैं। [एकाधिक एडमिन इंस्टेंस](../advanced/multiple-admin.md) देखें।


### टेम्पलेट, स्टैटिक और थीम {#templates-statics-and-theme}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | वह डायरेक्टरी जिसे बिल्ट-इन टेम्पलेट पर लौटने से पहले template overrides के लिए देखा जाता है। |
| `static_dir` | `str | None` | `None` | बिल्ट-इन CSS और JS के साथ सर्व होने वाली एक्स्ट्रा स्टैटिक फ़ाइलों की डायरेक्टरी। |
| `theme` | `BaseTheme` | `DefaultTheme()` | एक theme सबक्लास जो लेआउट टेम्पलेट, आइकॉन सेट और स्टैटिक एसेट तय करता है। |

[कस्टम थीम](../advanced/custom-themes.md) और [टेम्पलेट](../advanced/templates.md) इन विकल्पों को पूरी तरह कवर करते हैं।

### होम पेज {#the-home-page}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (आपके रजिस्टर किए गए व्यू से बना एक `DefaultIndexView`) | `base_url` पर रेंडर होने वाला पेज। |

डिफ़ॉल्ट होम पेज एक welcome बैनर है और साथ में हर रजिस्टर किए गए model view का एक पैनल, जिसमें उसका रिकॉर्ड काउंट दिखता है। इसे बदलने के लिए अपना `CustomView` पास करें — आमतौर पर `DefaultIndexView` सबक्लास या `widget` वाला कोई भी `CustomView`। [कस्टम व्यू और विजेट](custom-views.md) देखें।

### ऑथ, सिक्योरिटी और डेटा सुरक्षा {#auth-security-and-data-safety}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (एडमिन सबके लिए खुला है) | हर रूट के लिए गेट। [ऑथेंटिकेशन](auth.md) देखें। |
| `secret_key` | `str | None` | `None` (स्टार्टअप पर एक रैंडम key बनती है, `UserWarning` के साथ) | CSRF और flash कुकीज़ पर सिग्नेचर करता है। |
| `middlewares` | `Sequence[Middleware] | None` | `None` | एक्स्ट्रा Starlette मिडलवेयर, जो एडमिन के खुद जोड़े CSRF, flash और auth मिडलवेयर के अतिरिक्त चलता है। |
| `import_config` | `ImportConfig | None` | `None` (`ImportConfig()` डिफ़ॉल्ट) | इंपोर्ट एंडपॉइंट के लिए अपलोड साइज़ और ZIP-bomb सीमाएँ। |
| `export_config` | `ExportConfig | None` | `None` (`ExportConfig()` डिफ़ॉल्ट) | एक्सपोर्ट एंडपॉइंट के लिए row-count कैप और URL-फ़ाइल डाउनलोड सीमाएँ। |

[सिक्योरिटी](security.md) गाइड इन पाँचों पैरामीटर को विस्तार से कवर करती है।

### लोकेल और टाइमज़ोन {#locale-and-timezone}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (केवल English, कोई `LocaleMiddleware` नहीं) | अनुवादित UI स्ट्रिंग चालू करता है। |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (चालू) | दिखाई जाने वाली datetimes को देखने वाले के टाइमज़ोन में बदलता है। |

पूरी walkthrough के लिए [इंटरनेशनलाइज़ेशन और टाइमज़ोन](i18n.md) देखें।

### डिबगिंग {#debugging}

| पैरामीटर | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | `True` होने पर स्टार्टअप से पहले `starlette_admin.logging.configure_logging()` कॉल करता है, जो `starlette_admin` पैकेज के लिए रंगीन DEBUG-लेवल कंसोल लॉगिंग चालू करता है। |

```python
admin = Admin(
    session_provider=engine,
    title="My Admin",
    secret_key="a-long-random-string",
    debug=True,
)
```

डिबग लॉगिंग डेवलपमेंट के दौरान मदद करती है। हर रिक्वेस्ट लॉग करती है कि कौन-सा मिडलवेयर चला, किस व्यू ने URL रिज़ॉल्व किया, और परमिशन चेक किस वजह से पास हुआ या फेल।

!!! warning
    प्रोडक्शन में `debug=False` ही रखें। DEBUG-लेवल लॉगिंग बहुत वर्बोस होती है और हर रिक्वेस्ट पर काफ़ी ओवरहेड जोड़ती है।

हल्के तरीके के लिए `debug=True` पास करने के बजाय `starlette_admin.logging.configure_logging(level=logging.INFO)` खुद कॉल करें। आपको पूरी DEBUG वर्बोसिटी के बिना हैंडलर मिल जाएगा।

## व्यू रजिस्टर करना और माउंट करना {#registering-views-and-mounting}

`Admin` इंस्टेंस बनाने के बाद अपने व्यू रजिस्टर करें और एडमिन को अपनी एप्लिकेशन पर माउंट करें।

```python
admin.add_view(
    ModelView(Post)
)  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### व्यू रजिस्टर करना {#registering-views}

अपने एडमिन डैशबोर्ड में कंपोनेंट जोड़ने के लिए `add_view` का उपयोग करें। यह मेथड व्यू इंस्टेंस या व्यू क्लास — दोनों स्वीकार करता है, और आप model views, कस्टम पेज, ड्रॉपडाउन मेनू और एक्सटर्नल लिंक रजिस्टर कर सकते हैं।

### एप्लिकेशन माउंट करना {#mounting-the-application}

अपने सारे व्यू रजिस्टर करने के बाद एडमिन को अपनी Starlette या FastAPI एप्लिकेशन से जोड़ने के लिए `mount_to(app)` ठीक एक ही बार कॉल करें। यह चरण राउटिंग और सिक्योरिटी कॉन्फ़िगरेशन को फ़ाइनल कर देता है।

!!! important "ऑपरेशन का क्रम मायने रखता है"
    माउंटिंग एडमिन कॉन्फ़िगरेशन को लॉक कर देती है ताकि हर व्यू सही तरीके से रूट हो।

    * माउंट होने से पहले `admin.app` एक्सेस करने पर `RuntimeError` आता है।
    * पहली माउंटिंग के बाद दूसरा व्यू रजिस्टर करना या `mount_to` फिर से कॉल करना भी `RuntimeError` देता है।

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**आगे क्या है**

* **[सिक्योरिटी](security.md):** `secret_key`, CSRF, और एक्सपोर्ट तथा इंपोर्ट की सीमाएँ।
* **[ऑथेंटिकेशन](auth.md):** `auth_provider` को जोड़ना।
* **[एकाधिक एडमिन इंस्टेंस](../advanced/multiple-admin.md):** एक ही एप्लिकेशन में एक से अधिक `Admin` चलाना।
