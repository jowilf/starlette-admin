---
title: इनलाइन एडिट
description: लिस्ट व्यू टेबल के भीतर सीधे फ़ील्ड मान एडिट करके उपयोगकर्ताओं को तेज़
  डेटा एंट्री में सक्षम करें।
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# इनलाइन एडिट {#inline-edit}

इनलाइन एडिटिंग उपयोगकर्ताओं को लिस्ट पेज से सीधे किसी एक फ़ील्ड को बदलने देती है। किसी सेल को चुनने पर एक छोटा पॉपओवर (popover) खुलता है, इसलिए किसी को पूरा एडिट फ़ॉर्म खोलने की ज़रूरत नहीं पड़ती। इसका उपयोग तेज़, सिंगल-फ़ील्ड अपडेट के लिए करें: टाइटल ठीक करना, स्टेटस टॉगल करना, या तारीख़ समायोजित करना। यह इंटरैक्शन परिचित [x-editable](https://vitalets.github.io/x-editable/) पैटर्न पर आधारित है।

यह सुविधा opt-in है और डिफ़ॉल्ट रूप से बंद रहती है। इसे चालू करने से मानक एडिट पेज नहीं बदलता, जो जटिल, मल्टी-फ़ील्ड एडिट के लिए मुख्य इंटरफ़ेस बना रहता है।

> इनलाइन एडिटिंग के साथ चलाने योग्य उदाहरण के लिए, [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) देखें।

## बेसिक उपयोग {#basic-usage}

एडिट करने योग्य फ़ील्ड नाम `inline_editable_fields` सूची में घोषित करें:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

इसके बाद एडिट करने योग्य सेल लिस्ट पेज पर डैश्ड अंडरलाइन दिखाते हैं। किसी सेल को चुनने पर फ़ील्ड के मानक फ़ॉर्म कंट्रोल वाला पॉपओवर खुलता है, जो मौजूदा मान से प्रीफ़िल्ड होता है।

अंडरलाइन पूरे सेल पर नहीं लगती। हर लिस्ट टेम्पलेट `inline-edit-value` CSS क्लास को ठीक उसी एलिमेंट पर लगाता है जिसे रेखांकित (underline) करना है, और वह स्टाइल केवल एडिट करने योग्य सेल के भीतर लागू होती है। सभी बिल्ट-इन लिस्ट टेम्पलेट में यह क्लास पहले से मौजूद है। अगर आप कस्टम `list_template` लिखते हैं और वही सुविधा चाहते हैं, तो यह क्लास स्वयं जोड़ें:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

क्लास के बिना, सेल फिर भी पॉपओवर खोलता है, लेकिन उसमें कोई अंडरलाइन नहीं दिखती।

- **सेव:** चेक बटन चुनें या सिंगल-लाइन इनपुट में <kbd>Enter</kbd> दबाएँ। एडमिन फ़ील्ड को सत्यापित करता है, बदलाव सेव करता है, और पेज रीलोड किए बिना पंक्ति को रिफ़्रेश कर देता है।
- **कैंसिल:** बदलाव छोड़ने के लिए <kbd>x</kbd> बटन चुनें या <kbd>Esc</kbd> दबाएँ।

## कॉन्फ़िगरेशन नियम {#configuration-rules}

एप्लिकेशन स्टार्टअप पर `inline_editable_fields` को सत्यापित करता है ताकि ग़लत कॉन्फ़िगरेशन जल्दी विफल हो जाए। सूचीबद्ध कोई नाम इनमें से कोई शर्त पूरी करने पर `ValueError` उठाता है:

- वह `fields` में घोषित नहीं है।
- वह प्राइमरी की (primary key) फ़ील्ड है।
- वह लिस्ट पेज (`exclude_from_list`) या एडिट फ़ॉर्म (`exclude_from_edit`) से बाहर रखा गया है।
- वह कंटेनर या रीड-ओनली फ़ील्ड है: `CollectionField`, `ListField`, `ComputedField`, `FileField`, या `ImageField`।

## फ़ील्ड समर्थन {#field-support}

हर एडिट करने योग्य फ़ील्ड वही फ़ॉर्म विजेट रेंडर करता है जो वह एडिट पेज पर उपयोग करता है। किसी फ़ील्ड की JavaScript और CSS एसेट, जैसे select2, flatpickr, JSONEditor, या TinyMCE, लिस्ट पेज पर तभी लोड होती हैं जब वह फ़ील्ड इनलाइन-एडिट करने योग्य हो। इनलाइन एडिट रहित व्यू अपना मौजूदा हल्का पेज फ़ुटप्रिंट बनाए रखते हैं।

| फ़ील्ड टाइप                                                                          | समर्थित  | पॉपओवर विजेट                        |
| ------------------------------------------------------------------------------------ | --------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | हाँ       | साधारण इनपुट                        |
| `SlugField`                                                                          | हाँ       | साधारण इनपुट (सोर्स फ़ील्ड बाहर रखा गया) |
| `TextAreaField`                                                                      | हाँ       | Textarea                            |
| `IntegerField`, `DecimalField`, `FloatField`                                         | हाँ       | नंबर इनपुट                          |
| `BooleanField`                                                                       | हाँ       | टॉगल                                |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | हाँ       | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | हाँ       | select2 या native select            |
| `TagsField`                                                                          | हाँ       | select2 tags                        |
| `JSONField`                                                                          | हाँ       | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | हाँ       | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | हाँ       | async लुकअप के साथ select2          |
| `FileField`, `ImageField`                                                            | नहीं      | कोई नहीं (एडिट पेज आवश्यक)          |
| `CollectionField`, `ListField`, `ComputedField`                                      | नहीं      | कोई नहीं (रीड-ओनली कंटेनर)          |

---

## अनुमतियाँ {#permissions}

इनलाइन एडिटिंग मौजूदा अनुमति मॉडल का पुनः उपयोग करती है। पॉपओवर केवल तभी दिखता है और एडमिन रिक्वेस्ट केवल तभी स्वीकार करता है जब `is_accessible(request)` और `can_edit(request)` दोनों `True` लौटाएँ। इसलिए `can_edit` को ओवरराइड करने से इनलाइन एडिट भी सुरक्षित हो जाते हैं:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Also disables inline edit when False
        return "edit:post" in request.state.admin_user.roles
```

---

## सत्यापन {#validation}

इनलाइन सेव केवल एडिट किए गए फ़ील्ड को सत्यापित करके लिखता है।

- फ़ील्ड की `required` जाँच और `validators` चेन ठीक वैसे ही चलते हैं जैसे एडिट पेज पर चलते हैं।
- अन्य फ़ील्ड छोड़ दिए जाते हैं। लिस्ट पेज से कोई सेव किसी दूसरे फ़ील्ड के समवर्ती (concurrent) एडिट को ओवरराइट नहीं कर सकता, और किसी दूसरे फ़ील्ड का अमान्य डेटा सेव को रोकता नहीं है।

व्यू का क्रॉस-फ़ील्ड `validate` हुक फिर भी चलता है, लेकिन `data` डिक्शनरी में केवल एडिट किया गया फ़ील्ड होता है। पूरे फ़ॉर्म सबमिशन की अपेक्षा रखने वाला हुक missing कीज़ को सीधे इंडेक्स करने पर `KeyError` उठा सकता है, इसलिए पहले जाँच लें कि की (key) मौजूद है:

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

सत्यापन विफल होने पर पॉपओवर सबमिट किए गए मान को बरकरार रखते हुए खुला रहता है। एडिट किए गए फ़ील्ड का संदेश कंट्रोल के नीचे रेंडर होता है, ठीक वैसे ही जैसे एडिट पेज पर होता है। किसी दूसरे फ़ील्ड से जुड़ा संदेश उस फ़ील्ड के लेबल के साथ प्रीफ़िक्स होकर दिखता है।

किसी हुक के भीतर इनलाइन सेव पहचानने के लिए, `request.state.action == RequestAction.INLINE_EDIT` जाँचें। इसका उपयोग पूरे पेज रेंडर के लिए बने फ़्लैश संदेश छोड़ने के लिए करें।

!!! warning
    उस फ़ील्ड से जुड़ा सत्यापन नियम जिसे उपयोगकर्ता ने एडिट नहीं किया, इनलाइन सेव के दौरान नहीं चलता। अगर किसी फ़ील्ड के इनवेरिएंट (invariants) ऐसे मानों पर निर्भर हैं जिन्हें उपयोगकर्ता लिस्ट पेज से न देख सकता है न बदल सकता है, तो उस फ़ील्ड को `inline_editable_fields` से बाहर रखें।

---

## लाइफ़साइकिल हुक और इवेंट {#lifecycle-hooks-and-events}

इनलाइन सेव व्यू के मानक `edit()` पथ से गुज़रते हैं। `before_edit`, `after_edit`, और `after_edit_committed` हुक सामान्य रूप से सक्रिय (fire) होते हैं, और संगत [इवेंट](../advanced/events.md) मानक कॉन्टेक्स्ट टाइप का उपयोग करते हैं। `data` और `old_data` पेलोड में केवल एडिट किया गया फ़ील्ड होता है, इसलिए वे ठीक वही दर्शाते हैं जिसे सेव ने छुआ।

किसी इवेंट लिसनर के भीतर इनलाइन सेव को अलग करने के लिए, `ctx.extra["inline"]` जाँचें, जो इनलाइन एडिट के लिए `True` होता है:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## कस्टम फ़ील्ड {#custom-fields}

कस्टम फ़ील्ड स्वचालित रूप से इनलाइन एडिटिंग को समर्थन देते हैं जब वे मानक `BaseField` अनुबंध (contract) का पालन करते हैं। चूँकि `RequestAction.INLINE_EDIT` एक फ़ॉर्म एक्शन है, `action.is_form()` `True` लौटाता है। अगर आपका कस्टम फ़ील्ड फ़ॉर्म-वैल्यू रिप्रज़ेंटेशन बनाने के लिए `action == RequestAction.EDIT` जाँचता है, तो उसे `action.is_form()` का उपयोग करने के लिए बदलें ताकि पॉपओवर को सही रिप्रज़ेंटेशन मिले। संपूर्ण फ़ील्ड अनुबंध के लिए, [कस्टम फ़ील्ड](../advanced/custom-fields.md) देखें।
