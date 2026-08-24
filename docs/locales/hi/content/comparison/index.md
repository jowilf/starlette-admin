---
title: starlette-admin, Django Admin और Flask-Admin की तुलना
description: starlette-admin, Django Admin और Flask-Admin की पक्ष-दर-पक्ष तुलना, जिसमें
  वेब स्टैक, समर्थित ORM, फ़ीचर की गहराई और ट्रेड-ऑफ़ शामिल हैं।
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# starlette-admin, Django Admin और Flask-Admin की तुलना {#comparing-starlette-admin-django-admin-and-flask-admin}

Django Admin, Flask-Admin और starlette-admin एक ही समस्या का हल निकालते हैं: ये आपके डेटा मॉडल से production-ready एडमिन इंटरफ़ेस जनरेट कर देते हैं, ताकि आपको CRUD स्क्रीन हाथ से न लिखनी पड़ें। फ़र्क़ सिर्फ़ इतना है कि ये किन वेब स्टैक को टारगेट करते हैं, कौन-से ORM सपोर्ट करते हैं, और कितना काम इनमें इनबिल्ट है बनाम आप पर छोड़ा जाता है।

यह पेज तीनों की तुलना करता है। अगर आप Django Admin या Flask-Admin पहले से जानते हैं और सीधा API translation चाहते हैं, तो मिलती-जुलती migration guide पर जाएँ:

* [Django Admin से आ रहे हैं](django-admin.md)
* [Flask-Admin से आ रहे हैं](flask-admin.md)

## एक नज़र में स्थिति {#positioning-at-a-glance}

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **वेब फ़्रेमवर्क** | केवल Django | केवल Flask | Starlette, FastAPI, और कोई भी ASGI ऐप जो sub-applications माउंट कर सकता हो |
| **निष्पादन मॉडल** | Sync (WSGI-first) | Sync (WSGI) | Async-first (ASGI) |
| **डेटा लेयर** | केवल Django ORM | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM, या [कोई कस्टम बैकएंड](../integrations/custom-backend.md) |
| **UI टूलकिट** | Django टेम्पलेट, क्लासिक एडमिन थीम | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), डार्क मोड, [कस्टम थीम](../advanced/custom-themes.md) |
| **फ़्रेमवर्क के साथ शामिल** | हाँ, Django का हिस्सा | नहीं, अलग पैकेज | नहीं, अलग पैकेज |
| **प्रमाणीकरण** | `django.contrib.auth` के ज़रिए इनबिल्ट | ख़ुद का लाइए (`is_accessible`) | प्लगेबल [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md), अपना यूज़र स्टोर लाइए |

## कौन-सा फ़्रेमवर्क कब उपयुक्त है {#when-each-framework-fits}

### Django Admin

Django Admin नेटिव Django ऐप्लिकेशन के लिए उपयुक्त है। यह परिपक्व है और `django.contrib.auth` के साथ एकीकृत रहता है, इसलिए बिना किसी कॉन्फ़िगरेशन के आपको उपयोगकर्ता, समूह, प्रति-मॉडल अनुमतियाँ और परिवर्तन इतिहास मिल जाते हैं। यह केवल Django के अंदर ही चलता है।

### Flask-Admin

Flask-Admin ने Flask में auto-generation लाया और `ModelView` कॉन्फ़िगरेशन स्टाइल को लोकप्रिय बनाया। यह synchronous है और Flask से बँधा हुआ है, इसलिए यह async स्टैक पर नहीं चल सकता।

### starlette-admin

starlette-admin async Python स्टैक को टारगेट करता है। अगर आपका ऐप्लिकेशन FastAPI या Starlette उपयोग करता है, तो आप एडमिन को अपने ऐप पर माउंट करते हैं और वह उसी event loop पर चलता है। यह SQL और NoSQL दोनों तरह की डेटा लेयर के साथ काम करता है, Flask-Admin वाली `ModelView` कॉन्फ़िगरेशन स्टाइल बरक़रार रखता है, और Django Admin के उपयोगकर्ताओं की अपेक्षा के मुताबिक़ फ़ीचर की गहराई देता है: inlines, बैच एक्शन, per-request अनुमतियाँ और अंतर्राष्ट्रीयकरण।

## फ़ीचर मैट्रिक्स {#feature-matrix}

**संकेत:**

* **हाँ:** इनबिल्ट
* **आंशिक:** थर्ड-पार्टी पैकेज या कस्टम कोड से संभव
* **नहीं:** उपलब्ध नहीं

| फ़ीचर | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| ऑटो-जनरेटेड CRUD व्यू | **हाँ** | **हाँ** | **हाँ** |
| फ़ुल-टेक्स्ट सर्च | **हाँ** `search_fields` | **हाँ** `column_searchable_list` | **हाँ** [`searchable_fields`](../user-guide/filters.md) |
| कॉलम फ़िल्टर | **हाँ** `list_filter` | **हाँ** `column_filters` | **हाँ** `AND`/`OR` ग्रुप वाला [विज़ुअल फ़िल्टर बिल्डर](../user-guide/filters.md) |
| सॉर्टिंग और डिफ़ॉल्ट क्रम | **हाँ** | **हाँ** | **हाँ** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| लिस्ट व्यू में इनलाइन एडिटिंग | **हाँ** `list_editable` | **हाँ** `column_editable_list` | **हाँ** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| संबंधित मॉडल के इनलाइन फ़ॉर्म | **हाँ** `TabularInline` / `StackedInline` | **हाँ** `inline_models` | **हाँ** [`InlineModelView`](../user-guide/inline-forms.md) |
| बैच एक्शन | **हाँ** `actions` | **हाँ** `@action` | **हाँ** कन्फ़र्मेशन डायलॉग और कस्टम फ़ॉर्म के साथ [`@action`](../user-guide/actions.md) |
| प्रति-पंक्ति एक्शन | **आंशिक** कस्टम टेम्पलेट | **आंशिक** कस्टम फ़ॉर्मैटर | **हाँ** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| डेटा एक्सपोर्ट | **आंशिक** `django-import-export` | **हाँ**, CSV और अन्य | **हाँ** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| डेटा इंपोर्ट | **आंशिक** `django-import-export` | **नहीं** | **हाँ** preview सत्यापन और upsert वाला [CSV, JSON, Excel](../user-guide/export-import.md) |
| फ़ाइल और इमेज अपलोड | **हाँ** `FileField` / `ImageField` | **आंशिक** extra setup चाहिए | **हाँ** [लोकल और S3 स्टोरेज](../user-guide/file-storage.md) |
| डैशबोर्ड विजेट | **आंशिक** थर्ड-पार्टी थीम | **आंशिक** custom index view | **हाँ** [इनबिल्ट विजेट सिस्टम](../user-guide/custom-views.md) |
| कस्टम standalone पेज | **हाँ** custom `AdminSite` URLs | **हाँ** `BaseView` + `@expose` | **हाँ** [`CustomView`](../user-guide/custom-views.md) |
| फ़ॉर्म लेआउट नियंत्रण | **हाँ** `fieldsets` | **हाँ** `form_rules` | **हाँ** tabs और grids के साथ [`form_layout`](../advanced/form-layout.md) |
| प्रमाणीकरण | **हाँ** `django.contrib.auth` | **नहीं**, ख़ुद का लाइए | **हाँ** [`AuthProvider`](../user-guide/auth.md) या `OAuthProvider` |
| प्रति-मॉडल अनुमतियाँ | **हाँ**, permission framework | **हाँ**, `can_*` flags override करें | **हाँ**, [per-request methods](../user-guide/views.md#security-and-authorization) |
| प्रति-फ़ील्ड अनुमतियाँ | **आंशिक** `get_readonly_fields` | **नहीं** | **हाँ** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| लाइफ़साइकल हुक | **हाँ** `save_model`, signals | **हाँ** `on_model_change` | **हाँ** [लाइफ़साइकल हुक](../user-guide/views.md#lifecycle-hooks) और [इवेंट](../advanced/events.md) |
| CSRF सुरक्षा | **हाँ**, Django middleware | **हाँ**, Flask-WTF के ज़रिए | **हाँ**, [`Admin`](../user-guide/security.md) में इनबिल्ट |
| परिवर्तन इतिहास / audit log | **हाँ** `LogEntry` | **नहीं** | **आंशिक**, [इवेंट](../advanced/events.md) से ख़ुद बनाइए |
| अंतर्राष्ट्रीयकरण | **हाँ** | **हाँ**, Flask-Babel के ज़रिए | **हाँ** [`I18nConfig`](../user-guide/i18n.md) |
| एकाधिक एडमिन इंस्टेंस | **हाँ**, multiple `AdminSite`s | **हाँ** | **हाँ**, [multiple `Admin` माउंट](../advanced/multiple-admin.md) |
| Async ORM समर्थन | **आंशिक** | **नहीं** | **हाँ**, async SQLAlchemy, Beanie, Tortoise ORM |

## ट्रेड-ऑफ़ {#trade-offs}

* **संपूर्ण यूज़र सिस्टम:** Django Admin एक पूरा यूज़र सिस्टम साथ लाता है। `django.contrib.auth` उपयोगकर्ता, समूह, अनुमतियाँ और password management आपके लिए सँभाल लेता है। starlette-admin में आप अपने ही डेटा स्टोर के आधार पर `authenticate()` implement करते हैं, जिसका मतलब शुरुआत में थोड़ा ज़्यादा setup और बाद में ज़्यादा architectural आज़ादी है।
* **ऑटोमेटेड परिवर्तन इतिहास:** Django Admin परिवर्तन इतिहास `LogEntry` में दर्ज करता है। starlette-admin में आप lifecycle [इवेंट](../advanced/events.md) subscribe करके audit trail ख़ुद बनाते हैं। इसमें कुछ लाइनों का कोड लगता है, लेकिन यह ऑटोमैटिक नहीं होता।
* **थर्ड-पार्टी ecosystem:** Django Admin के पास थीम, विजेट और data workflows के लिए थर्ड-पार्टी पैकेजों का बड़ा ecosystem है। starlette-admin इनमें से कई फ़ीचर नेटिव रूप से देता है, लेकिन हो सकता है कि आप जिस niche extension पर निर्भर हैं वह अभी मौजूद न हो।
* **फ़ाइल management:** Flask-Admin `FileAdmin` देता है, जो सर्वर file system का browser है। starlette-admin मॉडल फ़ील्ड से जुड़ी फ़ाइलों को [लोकल disk या S3](../user-guide/file-storage.md) के ज़रिए सँभालता है, और इसमें general-purpose सर्वर file browser नहीं है।

## अगले कदम {#next-steps}

* Django से shift कर रहे हैं? [Django Admin से आ रहे हैं](django-admin.md) पढ़ें।
* Flask-Admin से shift कर रहे हैं? [Flask-Admin से आ रहे हैं](flask-admin.md) पढ़ें।
* बिल्कुल नई शुरुआत कर रहे हैं? [Quickstart](../getting-started/quickstart.md) कुछ ही मिनटों में चालू एडमिन इंटरफ़ेस दे देता है।
