---
title: फ़ील्ड्स
description: starlette-admin के सभी बिल्ट-इन फ़ील्ड का व्यापक रेफ़रेंस, जिनसे आप अपने
  डेटाबेस कॉलम को UI कंपोनेंट में मैप कर सकते हैं।
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# फ़ील्ड्स {#fields}

फ़ील्ड आपके व्यू की बिल्डिंग ब्लॉक हैं। भीतर झाँकें तो वे साधारण Python dataclasses हैं: फ़ील्ड कंस्ट्रक्टर को पास किया गया हर एट्रिब्यूट एक dataclass field बन जाता है, और हर फ़ील्ड टाइप `BaseField` का सबक्लास होता है, इसलिए आप उसे inspect कर सकते हैं, सबक्लास कर सकते हैं, या सीधे instantiate कर सकते हैं।

## सामान्य एट्रिब्यूट {#common-attributes}

हर फ़ील्ड टाइप कॉन्फ़िगरेशन एट्रिब्यूट का यह सेट `BaseField` से inherit करता है।

| एट्रिब्यूट | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `name` | `str` | **आवश्यक** | आपके मॉडल पर एट्रिब्यूट का नाम। |
| `label` | `str | None` | टाइटल-केस `name` | कॉलम हेडर और फ़ॉर्म लेबल। |
| `help_text` | `str | None` | `None` | फ़ॉर्म इनपुट के नीचे दिखाया जाने वाला हिंट टेक्स्ट। |
| `required` | `bool` | `False` | फ़ॉर्म में क्लाइंट और सर्वर, दोनों तरफ़ मान अनिवार्य करता है। |
| `validators` | `list[Validator]` | `[]` | सबमिट किए गए मान पर चलने वाले सर्वर-साइड वैलिडेटर। [सत्यापन](#validation) देखें। |
| `disabled` | `bool` | `False` | फ़ॉर्म में इनपुट को ग्रे करके लॉक कर देता है। |
| `read_only` | `bool` | `False` | फ़ील्ड दिखाता है पर एडिट रोकता है। |
| `default` | `Any | Callable` | `None` | क्रिएट फ़ॉर्म पर प्रीफ़िल मान। |
| `getter` | `Callable | None` | `None` | मान पढ़ते समय मॉडल एट्रिब्यूट लुकअप की जगह लेता है। [मानों की गणना, फ़ॉर्मेटिंग और पार्सिंग](#computing-formatting-and-parsing-values) देखें। |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | प्रति-एक्शन डिस्प्ले फ़ॉर्मेटिंग, जो उस एक्शन के लिए सीरियलाइज़ेशन की जगह लेती है। [मानों की गणना, फ़ॉर्मेटिंग और पार्सिंग](#computing-formatting-and-parsing-values) देखें। |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | प्रति-एक्शन इनपुट पार्सिंग, जो फ़ील्ड की डिफ़ॉल्ट पार्सिंग की जगह लेती है। [मानों की गणना, फ़ॉर्मेटिंग और पार्सिंग](#computing-formatting-and-parsing-values) देखें। |
| `searchable` | `bool` | `True` | `q` सर्च पैरामीटर मैच होने पर शामिल होता है। |
| `orderable` | `bool` | `True` | लिस्ट हेडर में सॉर्ट लिंक जोड़ता है। |
| `copy_to_clipboard` | `bool` | `False` | डिटेल पेज पर मान के बगल में कॉपी बटन जोड़ता है। |
| `filters` | `list | None` | `None` | लिस्ट पेज के फ़िल्टर का स्पष्ट ओवरराइड। |
| `extra` | `dict[str, Any]` | `{}` | आपके अपने मेटाडेटा के लिए एक डिक्शनरी। |

### दृश्यता नियंत्रण {#visibility-controls}

इन बूलियन फ़्लैग (सभी डिफ़ॉल्ट रूप से `False`) का उपयोग यह नियंत्रित करने के लिए करें कि फ़ील्ड कहाँ दिखे:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### डिफ़ॉल्ट तय करना {#defining-defaults}

`default` एट्रिब्यूट एक स्टैटिक मान, शून्य-आर्ग्युमेंट वाला कॉलेबल, या रिक्वेस्ट-अवेयर फ़ंक्शन स्वीकार करता है:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### मानों की गणना, फ़ॉर्मेटिंग और पार्सिंग {#computing-formatting-and-parsing-values}

हर फ़ील्ड तीन कॉलेबल हुक स्वीकार करता है — `getter`, `formatter` और `parser` — जो डेटा के आपके मॉडल और UI के बीच आवागमन के दौरान उसे इंटरसेप्ट करके बदल देते हैं। हर एक सिंक्रोनस या एसिंक्रोनस फ़ंक्शन स्वीकार करता है।

#### `getter`: कस्टम मान पढ़ना {#getter-reading-custom-values}

`getter` हुक, फ़ील्ड के मॉडल इंस्टेंस पढ़ते समय डिफ़ॉल्ट `getattr()` लुकअप की जगह ले लेता है। फ़ील्ड `getter(request, obj)` कॉल करता है और रिटर्न किया गया मान दिखाता है।

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

चूँकि `getter` मान शायद ही कभी किसी भौतिक डेटाबेस कॉलम से मैप होते हैं, इसलिए वे रीड-ओनली डिस्प्ले के साथ सबसे अच्छे फिट बैठते हैं। [`ComputedField`](#computedfield) उस संयोजन के लिए एक बिल्ट-इन शॉर्टकट है।

#### `formatter`: डिस्प्ले आउटपुट बदलना {#formatter-transforming-display-output}

`formatter` हुक तय करता है कि स्टोर किया गया मान किन्हीं खास पेजों पर कैसे रेंडर होगा। यह किसी `RequestAction`, जैसे `LIST`, `DETAIL` या `EXPORT`, को `(request, value) -> value` कॉलेबल से मैप करता है।

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**ध्यान में रखने योग्य फ़ॉर्मेटिंग व्यवहार:**

* **Nulls फ़ॉर्मेटर तक पहुँचते हैं:** डिफ़ॉल्ट सीरियलाइज़ेशन के उलट, फ़ॉर्मेटर को `None` मान भी मिलते हैं, इसलिए आप ऊपर `"unset"` की तरह फ़ॉलबैक टेक्स्ट दे सकते हैं।
* **सीरियलाइज़ेशन स्किप हो जाता है:** मैच होने वाला फ़ॉर्मेटर फ़ील्ड के `serialize_value` और `serialize_none_value` मेथड की जगह ले लेता है। रिटर्न किया गया मान जस का तस उपयोग होता है, इसलिए अंतिम आउटपुट की पूरी ज़िम्मेदारी फ़ॉर्मेटर की होती है।
* **JSON आवश्यकता:** `LIST` और `RELATION_LOOKUP` एक्शन के लिए रिटर्न किए गए मान JSON-सीरियलाइज़ेबल रहने चाहिए।

#### `parser`: आने वाले डेटा की प्रोसेसिंग {#parser-processing-incoming-data}

`parser` हुक, सबमिट या इंपोर्ट किए गए डेटा को पार्स करने की फ़ील्ड की डिफ़ॉल्ट प्रक्रिया को ओवरराइड करता है। यह किसी `RequestAction` को `(request, raw) -> value` कॉलेबल से मैप करता है।

* **फ़ॉर्म (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` सबमिट किया गया फ़ॉर्म इनपुट होता है, और `multiple=True` होने पर लिस्ट।
* **इंपोर्ट (`IMPORT`):** `raw` फ़ाइल से मिला बिना प्रोसेस किया हुआ सेल मान होता है।

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

पार्सिंग के बाद रिटर्न किया गया मान मानक सत्यापन चेन से गुज़रता है — पहले `required`, फिर `validators` — ठीक वैसे ही जैसे फ़ील्ड ने खुद डेटा पार्स किया हो।

!!! tip "हुक या सबक्लास?"
    किसी एक फ़ील्ड पर एकबारगी कस्टमाइज़ेशन के लिए आपको शायद ही कभी सबक्लास की ज़रूरत पड़ती है। पढ़ने, डिस्प्ले फ़ॉर्मेटिंग और इनपुट पार्सिंग को हैंडल करने के लिए इन हुक को कंस्ट्रक्टर आर्ग्युमेंट के रूप में पास करें। जब आप यह लॉजिक कई व्यू में दोबारा इस्तेमाल करें, या HTML रेंडरिंग टेम्पलेट बदलना चाहें, तब [फ़ील्ड को सबक्लास करें](../advanced/custom-fields.md)।

### सत्यापन {#validation}

क्रिएट या एडिट फ़ॉर्म सबमिट होने पर सर्वर-साइड सत्यापन हर फ़ील्ड पर चलता है, ताकि गलत डेटा कभी डेटाबेस तक न पहुँचे।

लाइफ़साइकल नियत है:

1. **खाली मान:** जब सबमिट किया गया मान खाली हो, जैसे `None`, `""`, या खाली कलेक्शन, तो सिर्फ़ `required` फ़्लैग चेक होता है। वैलिडेटर स्किप कर दिए जाते हैं।
2. **भरे हुए मान:** जब डेटा मौजूद हो, तो `validators` लिस्ट का हर कॉलेबल क्रम से पार्स किए गए मान पर चलता है।

#### वैलिडेटर का सिग्नेचर {#validator-signature}

एक वैलिडेटर को चार आर्ग्युमेंट मिलते हैं: `(request, field, value, form_values)`।

* **`request`:** मौजूदा Starlette रिक्वेस्ट ऑब्जेक्ट।
* **`field`:** वह फ़ील्ड इंस्टेंस जिसे वैलिडेट किया जा रहा है।
* **`value`:** इस फ़ील्ड के लिए सबमिट किया गया, पार्स किया हुआ मान।
* **`form_values`:** सारे पार्स किए गए फ़ॉर्म डेटा का डिक्शनरी, फ़ील्ड नाम की key के साथ, ताकि आप दूसरे फ़ील्ड भी देख सकें।

किसी मान को अस्वीकार करने के लिए `ValueError` रेज़ करें। एडमिन किसी फ़ील्ड की पहली एरर पकड़ता है, उस फ़ील्ड के बाकी वैलिडेटर स्किप कर देता है, और सारी एरर इकट्ठा करके उनके इनपुट के पास दिखाता है।

#### बिल्ट-इन वैलिडेटर {#built-in-validators}

[`starlette_admin.validators`](../api/validators.md) मॉड्यूल मानक नियम देता है:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### कस्टम और एसिंक्रोनस सत्यापन {#custom-and-asynchronous-validation}

कस्टम वैलिडेटर को सिंक्रोनस या एसिंक्रोनस फ़ंक्शन के रूप में लिखें। उन्हें `request` मिलता है, इसलिए वे जटिल शर्तें जाँचने के लिए डेटाबेस क्वेरी कर सकते हैं।

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

`form_values` आर्ग्युमेंट के साथ, फ़ील्ड-लेवल वैलिडेटर किसी दूसरे सबमिट किए गए फ़ील्ड पर निर्भर नियम भी लागू कर सकता है।

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### संदर्भ-विशिष्ट सत्यापन नियम {#context-specific-validation-rules}

* **रिलेशन फ़ील्ड:** सत्यापन के दौरान `HasOne` और `HasMany` को संबंधित रिकॉर्ड की प्राइमरी key मिलती है।
* **फ़ाइल फ़ील्ड:** पेलोड में हर `UploadFile` पर सत्यापन एक-एक बार चलता है। [फ़ाइल और मीडिया फ़ील्ड](#file-media-fields) देखें।
* **क्रॉस-फ़ील्ड सत्यापन:** साधारण निर्भरता के लिए `form_values` का उपयोग करें। पूरे फ़ॉर्म पर लागू होने वाले नियम के लिए इसके बजाय अपने व्यू पर `validate()` मेथड ओवरराइड करें। व्यू-लेवल सत्यापन तभी चलता है जब हर फ़ील्ड अपनी सत्यापन चेन पार कर चुका हो।

### कस्टम मेटाडेटा सहेजना {#storing-custom-metadata}

`extra` एक साधारण `dict` है जिसे `starlette-admin` कभी पढ़ता या लिखता नहीं। बिना फ़ील्ड सबक्लास किए अपना डेटा किसी फ़ील्ड इंस्टेंस से जोड़ने के लिए इसका उपयोग करें — चाहे कस्टम टेम्पलेट के लिए, अपनी [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) सबक्लास के किसी हुक के लिए, या किसी और इंटीग्रेशन पॉइंट के लिए:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## टेक्स्ट फ़ील्ड {#text-fields}

### StringField & TextAreaField

`StringField` छोटे कंटेंट के लिए सिंगल-लाइन टेक्स्ट इनपुट रेंडर करता है। `TextAreaField` इसे `<textarea>` एलिमेंट के साथ लंबे, बहु-पंक्ति टेक्स्ट के लिए बढ़ा देता है।

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| एक्स्ट्रा एट्रिब्यूट | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `maxlength` and `minlength` | `int | None` | `None` | HTML लंबाई की पाबंदियाँ। |
| `placeholder` | `str | None` | `None` | इनपुट का प्लेसहोल्डर टेक्स्ट। |
| `rows` *(केवल TextArea)* | `int` | `6` | दिखने वाली टेक्स्ट पंक्तियों की संख्या। |

### TinyMCEEditorField

`TextAreaField` को TinyMCE लाइब्रेरी के WYSIWYG एडिटर के साथ बढ़ाता है। इसके लिए `tinymce` एक्स्ट्रा पैकेज चाहिए।

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    `height`, `menubar`, `statusbar` और `toolbar` एट्रिब्यूट एडिटर का UI नियंत्रित करते हैं। बाकी कोई भी नेटिव TinyMCE कॉन्फ़िगरेशन `extra_options` के ज़रिए पास करें।

### फ़ॉर्मेटेड टेक्स्ट फ़ील्ड {#formatted-text-fields}

ये `StringField` वेरिएंट मैचिंग HTML इनपुट टाइप रेंडर करते हैं और रिकॉर्ड दिखाते समय मान को फ़ॉर्मेट करते हैं।

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` और `IPAddressField` में से हर एक, जब आप `validators` खाली छोड़ते हैं, एक मैचिंग वैलिडेटर ([`starlette_admin.validators`](../api/validators.md) का `email`, `url`, `uuid` और `ip_address`) जोड़ लेता है। इसे ओवरराइड करने के लिए अपना `validators` पास करें।

    `UUIDField` डिफ़ॉल्ट रूप से `copy_to_clipboard=True` सेट करता है। `IPAddressField` `ipv4` (डिफ़ॉल्ट `True`) और `ipv6` (डिफ़ॉल्ट `False`) स्वीकार करता है, जो तय करते हैं कि इसका डिफ़ॉल्ट वैलिडेटर कौन-कौन सी एड्रेस फ़ैमिली स्वीकार करेगा।

### PasswordField

फ़ॉर्म पर `<input type="password">` एलिमेंट रेंडर करता है ताकि उपयोगकर्ता जो टाइप करे वह छिपा रहे।

!!! danger
    `PasswordField` केवल क्रिएट और एडिट फ़ॉर्म पर इनपुट मास्क करता है। यह डिस्प्ले टेम्पलेट को ओवरराइड नहीं करता, इसलिए मान लिस्ट और डिटेल पेजों पर **प्लेन टेक्स्ट** में रेंडर होते हैं, और यह सबमिट किए गए रॉ मान `DEBUG` लेवल पर लॉग करता है।

    पासवर्ड फ़ील्ड पर `exclude_from_list = True` और `exclude_from_detail = True` सेट करें, और प्रोडक्शन में `DEBUG` लॉगिंग बंद कर दें।

## संख्यात्मक फ़ील्ड {#numeric-fields}

संख्यात्मक फ़ील्ड पूर्णांक, फ़्लोट और दशमलव मानों को संभालते हैं।

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| एक्स्ट्रा एट्रिब्यूट | लागू होता है | विवरण |
| --- | --- | --- |
| `min` and `max` | Integer, Decimal | न्यूनतम और अधिकतम स्वीकार्य मान। |
| `step` | Integer, Decimal | इंक्रीमेंट स्टेप की पाबंदी। |

!!! note
    `FloatField` अलग तरह से काम करता है: यह साधारण टेक्स्ट इनपुट की तरह रेंडर होता है, सबमिशन को `float` में बदल देता है, और `min`, `max` या `step` सपोर्ट नहीं करता।

## दिनांक और समय फ़ील्ड {#date-time-fields}

ये फ़ील्ड ब्राउज़र के नेटिव तारीख़ और समय पिकर इस्तेमाल करते हैं, जो मैचिंग स्टैंडर्ड लाइब्रेरी टाइप (`datetime.date`, `datetime.datetime`, और `datetime.time`) पर आधारित हैं।

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| एक्स्ट्रा एट्रिब्यूट | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel डिस्प्ले फ़ॉर्मेट: `"short"`, `"medium"`, `"long"`, `"full"`, या कोई कस्टम पैटर्न। |
| `search_format` | `str | None` | ORM-विशिष्ट | डेटाबेस सर्च क्वेरी बनाने में उपयोग होने वाला फ़ॉर्मेट। |

!!! note
    टाइमज़ोन सपोर्ट चालू होने पर `DateTimeField` डिस्प्ले टाइमज़ोन और डेटाबेस टाइमज़ोन के बीच बदलाव आपके लिए कर देता है।

### ArrowField

`Arrow` ऑब्जेक्ट पर आधारित `DateTimeField` वेरिएंट। एडिट फ़ॉर्म के बाहर यह इंसानी अंदाज़ में सापेक्ष समय दिखाता है, जैसे "3 hours ago"। इसके लिए `arrow` पैकेज चाहिए।

## सिलेक्शन और कलेक्शन फ़ील्ड {#selection-collection-fields}

### EnumField

सामान्य-उपयोग वाला सिलेक्ट फ़ील्ड। यह `<select>` ड्रॉपडाउन रेंडर करता है, या `multiple=True` होने पर `select2` मल्टी-सिलेक्ट। इसे Python `Enum` सबक्लास, tuples की लिस्ट, या रिक्वेस्ट के समय लोड किए गए choices से बैक करें।

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| एक्स्ट्रा एट्रिब्यूट | टाइप | विवरण |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Python `Enum` क्लास से choices बनाता है। |
| `choices` | `Sequence | None` | स्टैटिक `(value, label)` जोड़े, या सीधे मान। |
| `choices_loader` | `Callable | None` | हर रिक्वेस्ट पर choices तैयार करता है। |
| `multiple` | `bool` | मल्टी-सिलेक्ट चालू करता है और मानों को लिस्ट के रूप में स्टोर करता है। |

!!! important
    `enum`, `choices` या `choices_loader` में से ठीक एक ही दें।

`TimeZoneField`, `CountryField` और `CurrencyField`, `EnumField` के सबक्लास हैं जो Babel लोकेल डेटा पर आधारित हैं; इसके लिए `i18n` एक्स्ट्रा चाहिए। ये अपने लेबल मौजूदा रिक्वेस्ट के अनुसार लोकलाइज़ करते हैं।

### TagsField

`select2` पर बना फ़्री-टेक्स्ट टैगिंग इनपुट। यह `list[str]` स्टोर करता है और इसे पहले से तय कोई choices नहीं चाहिए।

### ListField

किसी दूसरे फ़ील्ड को रैप करके उसी टाइप के मानों की क्रमबद्ध लिस्ट स्टोर करता है। यह add और remove कंट्रोल वाली दोहराई जा सकने वाली पंक्तियों की तरह रेंडर होता है। रैप किए गए फ़ील्ड का नाम ही `ListField` का नाम बन जाता है।

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

कई सबफ़ील्ड को एक नेस्टेड ऑब्जेक्ट में ग्रुप करता है। इसे एम्बेडेड या struct जैसे डेटा के लिए उपयोग करें, जैसे MongoDB embedded document।

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## विशेषीकृत फ़ील्ड {#specialized-fields}

### JSONField

JSON ट्री और कोड एडिटर रेंडर करता है, और Python `dict` स्टोर करता है। क्लाइंट-साइड फ़ीडबैक के लिए `validation_schema` को स्टैंडर्ड JSON Schema डिक्शनरी पास करें।

### SlugField

`StringField` का वेरिएंट जो क्लाइंट पर किसी दूसरे फ़ील्ड के इनपुट से खुद को भर लेता है। मैनुअल एडिट ऑटो-फ़िल रोक देता है।

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` आवश्यक है और उसे उसी फ़ॉर्म के किसी दूसरे फ़ील्ड की ओर इशारा करना चाहिए। जनरेट किया गया slug किसी और स्ट्रिंग की तरह ही सबमिट और स्टोर होता है।

### ComputedField

एक रीड-ओनली, वर्चुअल फ़ील्ड जो डिस्प्ले के समय मॉडल इंस्टेंस से तैयार होता है; इसके पीछे कोई डेटाबेस कॉलम नहीं होता। यह उस [`getter` हुक](#computing-formatting-and-parsing-values) पर बना है जो हर फ़ील्ड में होता है, और साथ में वे डिफ़ॉल्ट जोड़ता है जो एक वर्चुअल कॉलम को चाहिए: क्रिएट फ़ॉर्म से बाहर, रीड-ओनली, नॉन-सर्चेबल और नॉन-ऑर्डरेबल।

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

जटिल या दोबारा इस्तेमाल होने वाले लॉजिक के लिए, इनलाइन `getter` पास करने के बजाय `ComputedField` को सबक्लास करके `parse_obj()` ओवरराइड करें:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` और `parse_obj` एक ही काम करते हैं: छोटे एक्सप्रेशन के लिए `getter` इस्तेमाल करें, और जब लॉजिक कई पंक्तियों में फैला हो या कई व्यू में दोबारा इस्तेमाल हो तो `ComputedField` सबक्लास करें। एडिट फ़ॉर्म पर यह फ़ील्ड फिर भी प्लेन-टेक्स्ट डिस्प्ले की तरह दिखता है, ताकि उपयोगकर्ता मौजूदा computed मान देख सके।

हर `ComputedField` सबक्लास `StringField` रेंडरिंग ही रखता है। ऐसा मान compute करने के लिए जिसे किसी दूसरे टाइप में रेंडर होना चाहिए — जैसे तारीख़, बैज या छवि — उस फ़ील्ड टाइप पर सीधे `getter=` सेट करें, साथ में मैचिंग `read_only` और `exclude_from_*` फ़्लैग भी दें।

## फ़ाइल और मीडिया फ़ील्ड {#file-media-fields}

`FileField` एक फ़ाइल अपलोड इनपुट रेंडर करता है, और `ImageField` उसमें छवि प्रीव्यू और वैधता जाँच जोड़ता है। अपलोड अपने-आप सहेजने और डेटाबेस में JSON `FileInfo` डिक्शनरी स्टोर करने के लिए एक `storage=` बैकएंड जोड़ें। पूरी कॉन्फ़िगरेशन के लिए [File Storage गाइड](file-storage.md) देखें।

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| एक्स्ट्रा एट्रिब्यूट | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | स्वीकार किए जाने वाले फ़ाइल एक्सटेंशन या MIME टाइप की कॉमा-सेपरेटेड लिस्ट, जो HTML `accept` एट्रिब्यूट को पास होती है। |
| `multiple` | `bool` | `False` | एक ही फ़ील्ड में कई फ़ाइलें स्वीकार करता है। |
| `storage` | `BaseStorage | None` | `None` | अपलोड सहेजने वाला स्टोरेज बैकएंड। इसके बिना फ़ील्ड रॉ अपलोड सीधे आपके बैकएंड को सौंप देता है। |
| `upload_folder` | `str` | `""` | सहेजी गई फ़ाइलों का स्टोरेज-रिलेटिव फ़ोल्डर। |
| `max_size` | `int | None` | `None` | स्वीकार किया जाने वाला अधिकतम अपलोड साइज़, बाइट्स में। |
| `validators` | `list[Validator]` | `[]` | कस्टम वैलिडेटर; हर अपलोड की गई फ़ाइल पर `accept` और `max_size` जाँचों के बाद `(request, field, upload)` के रूप में एक-एक बार कॉल होते हैं। अस्वीकार करने के लिए `ValueError` रेज़ करें। |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | केवल `ImageField`। सेट होने पर Pillow सहेजते समय एक सीमित-आकार का थंबनेल बनाता है, और लिस्ट पेज पूरी छवि की जगह उसी का उपयोग करता है। |

!!! note
    `ImageField`, `validators` लिस्ट की शुरुआत में Pillow आधारित छवि वैधता जाँच जोड़ देता है। जब Pillow इंस्टॉल हो और स्टोरेज कॉन्फ़िगर हो, तो वह बनने वाली `FileInfo` में `width` और `height` भी दर्ज करता है।

`thumbnail_size` सेट होने पर एडमिन पूरी छवि के साथ एक थंबनेल भी बनाता है — एस्पेक्ट रेशियो बनाए रखते हुए और कभी अपस्केल किए बिना — और उसे अपनी अलग key के तहत स्टोर करता है। उदाहरण के लिए, `covers/cat.jpg` के साथ `covers/cat.thumb.jpg` बन जाता है। लिस्ट पेज थंबनेल का उपयोग अपने-आप करता है। जिन पंक्तियों पर थंबनेल नहीं है — पहले से मौजूद डेटा की वजह से या क्योंकि `thumbnail_size` सेट नहीं है — वे पूरी छवि पर लौट आती हैं। थंबनेल बनने में नाकामी लॉग हो जाती है और अपलोड को कभी फेल नहीं करती।

डिटेल पेज हर `ImageField` छवि को lightbox में खोलता है, ताकि देखने वाले फ़ुल-रेज़ोल्यूशन छवियों में एक-एक करके जा सकें। एक ही फ़ील्ड (`multiple=True`) की छवियाँ एक गैलरी में ग्रुप हो जाती हैं।

कस्टम MIME-टाइप वैलिडेटर समेत पूरा चलने योग्य ऐप [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) में देखें।

### स्टोरेज के बिना {#without-a-storage}

`storage=` जुड़ा न हो, तो फ़ील्ड अपलोड सहेजने के बजाय रॉ रूप में आपके बैकएंड को सौंप देता है:

* **क्रिएट और एडिट फ़ॉर्म में**, पार्स किया गया मान एक tuple होता है: `(UploadFile | list[UploadFile] | None, bool)`। पहला एलिमेंट रॉ Starlette `UploadFile` है — `multiple=True` होने पर लिस्ट, और उपयोगकर्ता कुछ न चुने तो `None`। दूसरा एलिमेंट `True` होता है जब उपयोगकर्ता एडिट फ़ॉर्म पर delete बॉक्स चुनता है, यानी वह मौजूदा फ़ाइल को बदले बिना हटाना चाहता है। आपके बैकएंड का `create()` और `edit()` लॉजिक अपलोड स्टोर करता है और delete फ़्लैग का सम्मान करता है।
* **लिस्ट और डिटेल पेजों पर**, फ़ील्ड चाहता है कि मान `dict` के रूप में तीन keys उजागर करे, या ऑब्जेक्ट के रूप में तीन एट्रिब्यूट: `url` (आवश्यक, लिंक टारगेट); `filename` (डिस्प्ले लेबल); और `content_type` (जो फ़ाइल-टाइप आइकॉन चुनता है)।

इसी कॉन्ट्रैक्ट के ज़रिए नीचे दिए गए ORM इंटीग्रेशन अपनी फ़ाइल हैंडलिंग इसी फ़ील्ड में जोड़ते हैं।

### ORM-नेटिव फ़ाइल कॉलम {#orm-native-file-columns}

**MongoEngine** `mongoengine.FileField` और `mongoengine.ImageField` को out of the box सपोर्ट करता है, स्टोरेज के रूप में **GridFS** के साथ। एडमिन आपके लिए GridFS में अपलोड, सर्व और डिलीट सब कर देता है। आपको कोई `storage=` कॉन्फ़िगरेशन नहीं चाहिए: फ़ील्ड को नाम से लिस्ट कर दें।

**SQLAlchemy** को वही सुविधा [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/) के ज़रिए मिलती है। अपने मॉडल पर इसके `FileField` या `ImageField` कॉलम टाइप घोषित करें, और `starlette-admin` उन्हें पहचान लेता है, मैचिंग एडमिन फ़ील्ड रेंडर करता है, तथा स्टोर की गई फ़ाइलें सर्व करने के लिए एक रूट रजिस्टर करता है। स्टोरेज आप sqlalchemy-file के अपने `StorageManager` से कॉन्फ़िगर करते हैं, जो Apache Libcloud कंटेनरों पर आधारित है; अपलोड सेशन ट्रांज़ैक्शन का हिस्सा बनते हैं, इसलिए rollback होने पर सेशन स्टोर की गई फ़ाइल को हटा देता है।

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

कई स्टोरेज, content-type सत्यापन और `multiple=True` फ़ील्ड वाला पूरा ऐप [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) में देखें।

## HasOne & HasMany

रिलेशनल फ़ील्ड जो `select2` इनपुट की तरह रेंडर होते हैं और संबंधित व्यू के सर्च एंडपॉइंट पर आधारित हैं।

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

`key` पैरामीटर मैचिंग `ModelView` की ओर इशारा करता है। keys के रिज़ॉल्व होने के लिए दोनों व्यू एक ही `Admin` इंस्टेंस पर रजिस्टर करें।

---

## आगे क्या है {#whats-next}

* [फ़िल्टर](filters.md): अपने लिस्ट पेजों का फ़िल्टर बिल्डर कस्टमाइज़ करें।
* [फ़ाइल स्टोरेज](file-storage.md): `FileField` और `ImageField` के लिए स्टोरेज बैकएंड कॉन्फ़िगर करें।
* [कस्टम फ़ील्ड](../advanced/custom-fields.md): एक कस्टम फ़ील्ड बनाएँ।
