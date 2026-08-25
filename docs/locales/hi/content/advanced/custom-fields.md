---
title: कस्टम फ़ील्ड
description: starlette-admin में विशेष डेटा प्रकारों और कस्टम UI विजेट को संभालने
  के लिए कस्टम फ़ील्ड प्रकार बनाना सीखें।
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# कस्टम फ़ील्ड {#custom-fields}

इनबिल्ट फ़ील्ड आपके सामने आने वाले अधिकांश कॉलम को कवर कर लेते हैं, लेकिन जब उनमें से कोई ठीक बैठे नहीं, तो आप [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField) को सबक्लास करके अपना खुद का फ़ील्ड बना सकते हैं। कोई फ़ील्ड वास्तव में तीन मेथड होता है जो डेटा को आपके मॉडल और ब्राउज़र के बीच आगे-पीछे ले जाते हैं, साथ ही टेम्पलेट पथों का एक सेट होता है जो उसे रेंडर करता है। आप सीधे `BaseField` को सबक्लास कर सकते हैं, या अपनी ज़रूरत के सबसे क़रीब के इनबिल्ट फ़ील्ड (जैसे `StringField` या `EnumField`) को बढ़ाकर केवल उन्हीं हिस्सों को ओवरराइड कर सकते हैं जो अलग हैं।

## न्यूनतम उदाहरण {#minimal-example}

```python
from dataclasses import dataclass
from dataclasses import field as dc_field

from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

अपने `Admin` इंस्टेंस को templates डायरेक्टरी की ओर इंगित करें, फिर अपने व्यू में इस फ़ील्ड का इस्तेमाल करें:

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

चूँकि `StatusBadgeField`, `BaseField` की बजाय `EnumField` को सबक्लास करता है, उसे `choices`, इन choices के विरुद्ध फ़ॉर्म सत्यापन, और create तथा edit फ़ॉर्म के लिए डिफ़ॉल्ट `fields/form/enum.html` टेम्पलेट इनहेरिट हो जाता है। इनमें से कुछ भी बदलने की ज़रूरत नहीं है, इसलिए क्लास केवल list और detail रेंडरिंग एट्रिब्यूट ही ओवरराइड करती है।

इस पेज का बाक़ी हिस्सा बताता है कि जब फ़ील्ड को केवल टेम्पलेट बदलने से ज़्यादा की ज़रूरत हो, तो क्या ओवरराइड करें। पूरा चलने वाला कोड, साथ ही एक दूसरा फ़ील्ड (`AvatarNameField`) जो सचमुच डेटा मेथड ओवरराइड करता है, [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields) में देखें।

## तीन डेटा मेथड {#the-three-data-methods}

| मेथड | कब कॉल होता है | सिग्नेचर |
| --- | --- | --- |
| `parse_form_data` | कोई create/edit फ़ॉर्म सबमिट होता है | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | डिस्प्ले के लिए मॉडल इंस्टेंस से वैल्यू पढ़ी जाती है | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | फ़्रंटएंड (list, detail, API, export) के लिए वैल्यू फ़ॉर्मैट की जाती है | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` इनमें से किसी को भी ओवरराइड नहीं करता, क्योंकि `EnumField` सबमिट की गई वैल्यू को `choices` के विरुद्ध पहले ही पार्स कर लेता है और रॉ स्ट्रिंग `obj.status` से पढ़ लेता है। बैज उस स्ट्रिंग के ऊपर की प्रस्तुति मात्र है। जब वैल्यू को दोबारा रेंडर करने की बजाय compute किया जाना हो या उसकी बनावट बदलनी हो, तब इन तीनों मेथड को ओवरराइड करें।

!!! tip "हुक या सबक्लासिंग"
    किसी एक फ़ील्ड में कोई एकबारगी बदलाव करने के लिए आपको शायद ही कभी सबक्लास की ज़रूरत पड़े। इसके बजाय पढ़ने, डिस्प्ले फ़ॉर्मैटिंग, और इनपुट पार्सिंग को संभालने के लिए [`getter`, `formatter`, और `parser` हुक](../user-guide/fields.md#computing-formatting-and-parsing-values) को कंस्ट्रक्टर आर्ग्युमेंट की तरह पास करें।
    **सबक्लास कब करें:** केवल तब, जब एक से ज़्यादा व्यू में वही लॉजिक चाहिए हो, या जब टेम्पलेट बदलने हों।

`parse_form_data` को रिक्वेस्ट से रॉ `FormData` (`starlette.datastructures` से) मिलता है और वह वही डेटा लौटाता है जो `view.create()` या `view.edit()` को इस फ़ील्ड के लिए मिलना चाहिए। डिफ़ॉल्ट इम्प्लीमेंटेशन `form_data.get(self.id)` पढ़ता है और उसे बिना बदले लौटा देता है। अधिकांश फ़ील्ड को केवल टाइप coercion जोड़ने की ज़रूरत होती है:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` को मॉडल इंस्टेंस मिलता है और वह दिखाई जाने वाली वैल्यू लौटाता है। डिफ़ॉल्ट रूप से वह `getattr(obj, self.name, None)` लौटाता है। ऐसे फ़ील्ड के लिए इसे ओवरराइड करें जो किसी एक मॉडल एट्रिब्यूट से मेल नहीं खाते, जैसे कोई फ़ील्ड जो दो कॉलम को जोड़ता है। उदाहरण के लिए, `AvatarNameField` एक `name` स्ट्रिंग को उस row के अपलोड किए गए avatar के साथ जोड़ता है:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` को जो कुछ भी `parse_obj` (या ORM लेयर) ने बनाया है वह मिलता है और वह उसे मौजूदा रिक्वेस्ट के लिए फ़ॉर्मैट करता है। इसे list पेज, detail पेज, JSON API, और डेटा एक्सपोर्ट — सबके लिए अलग-अलग कॉल किया जाता है, इसलिए जब आकार context के हिसाब से अलग होना हो तो `request.state.action` पर शाखा करें। `AvatarNameField` को avatar इमेज केवल list पेज पर चाहिए, और हर दूसरी जगह वह सादे टेक्स्ट पर लौट आता है:

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    `serialize_value` जो कुछ भी `RequestAction.LIST` और `RequestAction.RELATION_LOOKUP` के लिए लौटाता है, वह सीधे JSON रिस्पॉन्स में चला जाता है, इसलिए वह JSON-serializable होना चाहिए।

## टेम्पलेट पथ {#template-paths}

हर फ़ील्ड में नीचे दिए गए टेम्पलेट एट्रिब्यूट होते हैं। हर एक एक पथ है जिसे एडमिन का Jinja2 लोडर resolve करता है: वह पहले आपकी `templates_dir` की जाँच करता है (अगर आपने एक सेट की है), फिर इनबिल्ट `starlette_admin/templates/` डायरेक्टरी पर चला जाता है। विवरण के लिए [टेम्पलेट](templates.md) देखें।

| एट्रिब्यूट | डिफ़ॉल्ट | किसके लिए रेंडर होता है |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | list पेज पर हर row का कॉलम वैल्यू |
| `detail_template` | `"fields/detail/text.html"` | read-only detail पेज |
| `form_template` | `"fields/form/input.html"` | create/edit फ़ॉर्म का इनपुट |
| `null_template` | `"fields/detail/_null.html"` | list और detail पेज, जब वैल्यू `None` हो |
| `empty_template` | `"fields/detail/_empty.html"` | list और detail पेज, जब वैल्यू खाली list या tuple हो |

ये पाँचों टेम्पलेट `field` इंस्टेंस और मौजूदा `data` वैल्यू पाते हैं। `list_template` और `detail_template` के लिए `data` कभी `None` या खाली नहीं होता, क्योंकि वे मामले type-specific टेम्पलेट के include होने से पहले `null_template` या `empty_template` की ओर भेज दिए जाते हैं। `form_template` को `error` भी मिलता है (`FormValidationError` का संदेश, अगर हुआ हो) और `action` भी (`RequestAction.CREATE`, `RequestAction.EDIT`, या `RequestAction.INLINE_EDIT`, जब list पेज के [इनलाइन एडिट](../user-guide/inline-edit.md) popover के भीतर रेंडर हो)। ये तीनों form actions हैं, इसलिए `action.is_form()` का नतीजा `True` होता है। जिस फ़ील्ड कोड को form-value निरूपण चाहिए, वह `action == RequestAction.EDIT` की बजाय इसी पर शाखा करे।

`null_template` और `empty_template` तब ओवरराइड करें जब ग़ायब वैल्यू का रूप डिफ़ॉल्ट म्यूट `-null-` और `-empty-` लेबल से अलग होना चाहिए — उदाहरण के लिए कोई empty-state आइकन या "Not provided" बैज जो फ़ील्ड की अपनी स्टाइलिंग से मेल खाए:

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

चूँकि `null_template` और `empty_template`, `list_template` की तरह साधारण फ़ील्ड एट्रिब्यूट हैं, वे list, detail, और इस फ़ील्ड को रेंडर करने वाले किसी भी दूसरे व्यू में साझा होते हैं — जैसे किसी संबंधित व्यू की इनलाइन टेबल।

`StatusBadgeField` `list_template` और `detail_template` — दोनों को ही एक ही टेम्पलेट देता है, क्योंकि एक ही बैज दोनों contexts में काम करता है:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` केवल `list_template` ओवरराइड करता है। इस टेम्पलेट में `data` वेरिएबल वह डिक्शनरी है जिसे `parse_obj` ने बनाया और `serialize_value` ने नया रूप दिया — कोई सादी स्ट्रिंग नहीं:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

`inline-edit-value` क्लास [इनलाइन एडिट](../user-guide/inline-edit.md) की अंडरलाइन के लिए ऑप्ट-इन मार्कर है। जब तक फ़ील्ड inline-editable न हो, यह निष्क्रिय रहता है, इसलिए इसे avatar पर नहीं बल्कि नाम पर लगाने का यहाँ कोई ख़र्च नहीं होता, और अगर फ़ील्ड कभी editable हो जाए तो affordance का दायरा भी ठीक रहता है।

`form_template` को डिफ़ॉल्ट रखते हुए `list_template` और `detail_template` को ओवरराइड करना — ठीक यही `StatusBadgeField` `EnumField` को extend करके करता है। डिफ़ॉल्ट `fields/form/enum.html`, `field.choices` से भरा एक `<select>` ड्रॉपडाउन रेंडर करता है, इसलिए status को edit करना बिना किसी और बदलाव के काम करता है।

## कन्वर्टर रजिस्ट्री में पंजीकृत करना {#registering-with-the-converter-registry}

किसी व्यू की `fields = [...]` लिस्ट फ़ील्ड ऑब्जेक्ट के साथ-साथ सादे एट्रिब्यूट नाम भी स्वीकार करती है। कोई भी आइटम जो पहले से `BaseField` नहीं है, एक **कन्वर्टर रजिस्ट्री** से गुज़रता है जो कॉलम टाइप को फ़ील्ड क्लास से मैप करती है। हर ORM बैकएंड अपनी रजिस्ट्री के साथ आता है (`starlette_admin.contrib.sqla.converters.ModelConverter` और `beanie`, `mongoengine`, तथा `tortoise` के बराबर संस्करण), जो सब एक ही बेस पर बनी हैं:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

`@converts(*types)` डेकोरेटर किसी मेथड को एक या एक से अधिक type key के लिए कन्वर्टर चिह्नित करता है। `BaseModelConverter.__init__` इंस्टेंस में इन decorated मेथड को खोजता है और उन्हीं से अपनी `converters` डिक्शनरी बनाता है। SQLAlchemy बैकएंड के लिए type keys कॉलम टाइप के **नाम** हैं (`"String"`, `"Integer"`, `"Enum"`, आदि), क्योंकि SQLAlchemy में सभी dialects के बीच कोई एक साझा बेस क्लास नहीं है।

अपनी mappings जोड़ने के लिए बैकएंड के कन्वर्टर को सबक्लास करें। यह उदाहरण हर `Enum` कॉलम को डिफ़ॉल्ट `EnumField` की बजाय `StatusBadgeField` की ओर भेजता है:

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

सबक्लास को `ModelView(converter=...)` में पास करें ताकि `fields = [...]` के स्ट्रिंग फ़ील्ड नाम डिफ़ॉल्ट कन्वर्टर की बजाय आपके कन्वर्टर से होते हुए resolve हों:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

अगर आप फ़ील्ड हमेशा स्पष्ट रूप से बनाते हैं, जैसा ऊपर न्यूनतम उदाहरण में है, तो आप कन्वर्टर रजिस्ट्री को छोड़ सकते हैं। इसकी ज़रूरत केवल तब है जब आप चाहते हों कि `fields = ["status"]` जैसी कोई एंट्री अंतर्निहित कॉलम टाइप से `StatusBadgeField` बना दे।

---

## आगे क्या {#whats-next}

* **[फ़ील्ड](../user-guide/fields.md):** पूरा इनबिल्ट फ़ील्ड रेफ़रेंस और `BaseField` एट्रिब्यूट टेबल।
* **[टेम्पलेट](templates.md):** टेम्पलेट लोडर `list_template`, `detail_template`, `form_template`, `null_template`, और `empty_template` को कैसे resolve करता है।
* **[एक्सटेंशन पॉइंट](extension-points.md):** `starlette-admin` की बाक़ी हर प्लग करने योग्य सतह।
