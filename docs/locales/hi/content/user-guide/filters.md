---
title: फ़िल्टर
description: टाइप-अवेयर क्वेरी बिल्डर का उपयोग करके अपने एडमिन व्यूज़ में जटिल नेस्टेड
  AND/OR फ़िल्टरिंग क्षमताएँ जोड़ें।
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# फ़िल्टर {#filters}

लिस्ट पेज के हर फ़ील्ड का अपना फ़िल्टर ऑपरेटर सेट हो सकता है, जैसे `contains`, `between`, और `is null`। आपके उपयोगकर्ता इन ऑपरेटरों को एक नेस्टेड `AND`/`OR` ट्री में जोड़ते हैं, और आपको कभी भी कोई जटिल डेटाबेस क्वेरी नहीं लिखनी पड़ती।

एडमिन उपलब्ध फ़िल्टर फ़ील्ड के अंतर्निहित टाइप से व्युत्पन्न करता है। आप किसी भी फ़ील्ड के लिए उस सेट को सीमित, विस्तारित, या पूरी तरह बदल सकते हैं।


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

डिफ़ॉल्ट फ़िल्टर, प्रति-फ़ील्ड ओवरराइड और कस्टम `BaseFilter` सबक्लास को कवर करने वाले रन करने योग्य ऐप के लिए [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) देखें।

आपके द्वारा `searchable_fields` में सूचीबद्ध हर फ़ील्ड को लिस्ट टूलबार में एक **Filters** ड्रॉपडाउन मिलता है। वहाँ से उपयोगकर्ता आवश्यक पंक्तियाँ खोजने के लिए कितने भी फ़िल्टर जोड़ सकते हैं।

## फ़िल्टर बिल्डर कैसे काम करता है {#how-the-filter-builder-works}

**Filters** बटन चुनने पर एक ड्रॉपडाउन फ़ॉर्म खुलता है जहाँ उपयोगकर्ता अपनी क्वेरी बनाते हैं:

* **Add filter**: एक कंडीशन पंक्ति (row) जोड़ता है। उपयोगकर्ता एक फ़ील्ड चुनता है, उस फ़ील्ड के उपलब्ध फ़िल्टर में से ऑपरेटर चुनता है, और एक मान देता है। इनपुट ऑपरेटर के अनुसार ढल जाता है: `contains` के लिए सादा टेक्स्ट बॉक्स, `between` के लिए दो बॉक्स, और `is null` के लिए कोई इनपुट नहीं।
* **Add group**: अपने `AND`/`OR` सेलेक्टर वाला एक सबफ़ॉर्म नेस्ट करता है। इससे `A AND (B OR C)` जैसी कंडीशन बनाएँ।
* **Match all/any of the following**: यह तय करता है कि वर्तमान स्तर `AND` लॉजिक उपयोग करेगा या `OR`।
* **Apply filters**: फ़ॉर्म को `GET` रिक्वेस्ट के रूप में सबमिट करता है। एडमिन पूरे फ़िल्टर ट्री को एक single `filter` क्वेरी पैरामीटर में सीरियलाइज़ करता है, जिसका वर्णन [The filter URL format](#the-filter-url-format) में है।
* **Active filters**: प्रत्येक सक्रिय फ़िल्टर टेबल के ऊपर एक removable pill की तरह दिखता है। `×` चुनने पर लिस्ट उस रूल को हटाकर फिर से सबमिट होती है। एक नेस्टेड ग्रुप एक ही pill में सिमट जाता है जिसे उपयोगकर्ता पूरे के पूरे हटा सकते हैं।

!!! tip
    चूँकि पूरी फ़िल्टर स्थिति URL में रहती है, इसलिए फ़िल्टर की गई लिस्ट शेयर की जा सकती है। आपके उपयोगकर्ता पेज को बुकमार्क कर सकते हैं और लिंक किसी सहकर्मी को भेज सकते हैं।

## किसी विशेष फ़ील्ड के लिए फ़िल्टर ओवरराइड करना {#overriding-filters-for-a-specific-field}

जब डिफ़ॉल्ट फ़िल्टर बहुत व्यापक हों, या आपको कुछ अधिक विशिष्ट चाहिए, तो किसी फ़ील्ड को `filters=` आर्ग्युमेंट पास करें और उसका डिफ़ॉल्ट सेट बदल दें।

आप लिस्ट को केवल ज़रूरी ऑपरेटरों तक सीमित कर सकते हैं, उसे किसी कस्टम फ़िल्टर से विस्तारित कर सकते हैं, या किसी ऐसे फ़ील्ड में ऑपरेटर जोड़ सकते हैं जिसमें डिफ़ॉल्ट रूप से केवल null चेक होते हैं — जैसे `TagsField`:

```python
from enum import Enum

from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import ModelView

# Import the concrete filter implementations for your specific backend
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    NumericEqualFilter,
)


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductView(ModelView):
    fields = [
        "id",
        StringField("name"),  # Uses the default filter set, no override needed
        EnumField("status", enum=ProductStatus),  # Uses the default filter set
        DecimalField(
            "price",
            # Narrowed down to just 3 of the 9 default numeric filters
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Import filters from your backend"
    आपके द्वारा `filters=` को पास की गई फ़िल्टर क्लास आपके डेटाबेस बैकएंड की concrete implementations होनी चाहिए: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`, या `.tortoise.filters`। इंपोर्ट अपने बैकएंड के `filters` मॉड्यूल से करें, `starlette_admin.filters` से नहीं।

## फ़िल्टर URL फ़ॉर्मेट {#the-filter-url-format}

फ़िल्टर बिल्डर अपनी स्थिति को एक compact स्ट्रिंग के रूप में `filter` क्वेरी पैरामीटर में सीरियलाइज़ करता है।

फ़ॉर्मेट है: बिना-मान वाले फ़िल्टर के लिए `field__operator`, एक मान वाले के लिए `field__operator=value`, और दो-मान वाले फ़िल्टर जैसे `between` के लिए `field__operator=value..value2`। रूल्स `AND` या `OR` से जुड़ते हैं, और कोष्ठक एक ग्रुप को नेस्ट करते हैं:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

जब किसी मान में space या कोष्ठक हो, तो उसे quotes में लिखें: `name__eq="quoted value"`। `is one of` जैसे multi-select फ़िल्टर का list मान comma से अलग होता है और उसे quotes की आवश्यकता नहीं होती: `status__in=ACTIVE,OUT_OF_STOCK`।

जब URL में अमान्य `filter` स्ट्रिंग हो — जैसे अज्ञात फ़ील्ड, अनुपलब्ध ऑपरेटर, या unparseable मान — तो एप्लिकेशन कंडीशन के किसी हिस्से को चुपचाप हटाने के बजाय `HTTP 400` त्रुटि रिटर्न करता है।

!!! important
    केवल वही फ़ील्ड फ़िल्टर पाते हैं जिन्हें आप `searchable_fields` में सूचीबद्ध करते हैं। यदि आप `searchable_fields` अनसेट छोड़ें, तो हर फ़ील्ड को फ़िल्टर मिल जाते हैं।


## बिल्ट-इन फ़िल्टर संदर्भ {#built-in-filter-reference}

निम्नलिखित तालिका बॉक्स से उपलब्ध हर फ़िल्टर, बुकमार्क किए गए लिंक में दिखने वाला URL slug, और प्रत्येक की अपेक्षित मान का प्रकार सूचीबद्ध करती है। "Two values" वाले फ़िल्टर को URL में `value` और `value2` दोनों चाहिए, उदाहरण के लिए `between=2026-01-01..2026-01-31`।

| Filter | Slug | Value type | Two values? |
| --- | --- | --- | --- |
| Contains | `contains` | text |  |
| Does not contain | `not_contains` | text |  |
| Starts with | `startswith` | text |  |
| Ends with | `endswith` | text |  |
| Equal | `eq` | text, number, date, datetime, or time |  |
| Not equal | `neq` | text or number |  |
| Is null | `is_null` | *(none)* |  |
| Is not null | `is_not_null` | *(none)* |  |
| Greater than | `gt` | number |  |
| Less than | `lt` | number |  |
| Greater than or equal | `gte` | number |  |
| Less than or equal | `lte` | number |  |
| Between | `between` | number, date, datetime, or time | ✓ |
| Is in the past | `in_past` | *(none)* |  |
| Is in the future | `in_future` | *(none)* |  |
| Is true | `is_true` | *(none)* |  |
| Is false | `is_false` | *(none)* |  |
| Is one of | `in` | comma-separated list |  |
| Is not one of | `not_in` | comma-separated list |  |

यदि आपको किसी ऐसे डेटा टाइप के लिए फ़िल्टर चाहिए जिसे बिल्ट-इन कवर नहीं करते — जैसे JSON फ़ील्ड या geo-point — तो `BaseFilter` सबक्लास लिखने और उसे globally या per-field रजिस्टर करने के लिए [Custom Filters](../advanced/custom-filters.md) देखें।

---

**आगे क्या**

* **[Custom Filters](../advanced/custom-filters.md):** `BaseFilter` सबक्लास लिखें और रजिस्टर करें।
* **[एक्शन](actions.md):** अपने लिस्ट पेजों में bulk और row एक्शन जोड़ें।
* **[व्यूज़](views.md):** `searchable_fields` और लिस्ट-पेज कॉन्फ़िगरेशन के बाकी हिस्सों के बारे में और जानें।
