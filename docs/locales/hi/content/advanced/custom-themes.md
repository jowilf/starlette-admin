---
title: कस्टम थीम
description: Tabler CSS वेरिएबल को ओवरराइड करें, कस्टम स्टाइलशीट इंजेक्ट करें, और
  अपने starlette-admin डैशबोर्ड की समग्र look को बदलें।
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# कस्टम थीम {#custom-themes}

आप थीम सेटिंग्स, कस्टम टेम्पलेट, और स्टैटिक फ़ाइलों के ज़रिए एडमिन को री-स्टाइल कर सकते हैं। `DefaultTheme` एक `TablerSettings` object से `<html>` टैग पर data attributes लिखकर डिफ़ॉल्ट रूप को नियंत्रित करता है। गहरे बदलावों के लिए, अपने टेम्पलेट, स्टैटिक एसेट, और icon sets को बंडल करने के लिए `BaseTheme` को सबक्लास करें, या अपनी टेम्पलेट और स्टैटिक डायरेक्टरी `Admin` को पास करें।

## थीम लागू करना {#applying-a-theme}

अपनी color palette, border radius, और color mode सेट करने के लिए `TablerSettings` का उपयोग करें। इसे `DefaultTheme` को पास करें, फिर उसे अपने `Admin` इंस्टेंस के `theme` parameter में पास करें।

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

हर स्टार्टअप पर एक यादृच्छिक थीम चुनने वाला रन करने योग्य ऐप देखने के लिए [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) देखें।

यह कॉन्फ़िगरेशन `data-bs-theme*` attributes सीधे रूट `<html>` एलिमेंट पर लागू करता है:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## `TablerSettings` संदर्भ {#tablersettings-reference}

| Attribute | Type | Default | Valid values |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## class map के साथ कंपोनेंट री-स्टाइल करना {#restyling-components-with-a-class-map}

कोर टेम्पलेट कंपोनेंट स्टाइलिंग को हार्डकोड नहीं करते। वे `cls('role.name')` Jinja हेल्पर के ज़रिए class attributes रेंडर करते हैं, जो `form.save_button` या `list.table` जैसी सिमेंटिक रोल को एक CSS class string में बदल देता है। हर रोल का डिफ़ॉल्ट मान `starlette_admin.theme.CoreClasses` में मौजूद है।

किसी रोल को री-स्टाइल करने के लिए, एक `ClassMap` सबक्लास लिखें। जो रोल आप मैप नहीं करते, वे `CoreClasses` पर फ़ॉलबैक हो जाते हैं, इसलिए आंशिक ओवरराइड सुरक्षित हैं। ध्यान रखें कि बटन रोल variant, size, और spacing समेत एलिमेंट की पूरी class attribute सेट करता है, इसलिए उसे मैप करने से बटन का रूप पूरी तरह बदल जाता है।

Class maps को पूरी कस्टम थीम की ज़रूरत नहीं होती। डिफ़ॉल्ट थीम को अनुकूलित करने के लिए, `DefaultTheme` को सबक्लास करें और `get_class_map()` से अपना मैप रिटर्न करें:

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

रोल की पूरी सूची के लिए `starlette_admin/theme.py` में `CoreClasses.classes` पढ़ें। रोल तीन प्रकार की स्टाइलिंग को कवर करते हैं:

* **बटन:** हर बटन लोकेशन के लिए एक रोल, जो form footer, list toolbar, फ़िल्टर bar, एक्शन modal, और inline editing को कवर करता है। आपका सेट किया मान बटन की पूरी class attribute बन जाता है।
* **कंपोनेंट classes:** फ़्रेमवर्क-विशिष्ट classes जिन्हें कोई दूसरा CSS फ़्रेमवर्क अपने अनुसार बदल देता है, जैसे `list.table`, `modal.base`, या `filter.chip`।
* **रनटाइम classes:** classes जिन्हें कोर JavaScript डायनामिक रूप से लागू करता है, जैसे `alert.success` या `import.status_badge`।

## कस्टम थीम बनाना और साझा करना {#building-and-sharing-custom-themes}

आप एक प्लगइन की तरह ही थीम को package करके PyPI पर प्रकाशित कर सकते हैं। कई प्रोजेक्ट्स में एडमिन के लेआउट और स्टाइलिंग को बदलने वाला पुन: प्रयोज्य Python पैकेज बनाने के लिए, या दूसरों के साथ एक visual system साझा करने के लिए `BaseTheme` को सबक्लास करें।

### Cookiecutter से स्कैफ़ोल्डिंग {#scaffolding-with-cookiecutter}

आधिकारिक cookiecutter टेम्पलेट से शुरुआत करें। यह सही डायरेक्टरी संरचना और कॉन्फ़िगरेशन फ़ाइलों वाला प्रकाशित करने योग्य पैकेज जनरेट करता है।

`cookiecutter` को अपने पैकेज मैनेजर से इंस्टॉल करें। विवरण के लिए [आधिकारिक इंस्टॉलेशन गाइड](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) देखें:

```bash
pip install cookiecutter

```

फिर किसी भी डायरेक्टरी से टेम्पलेट चलाएँ:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

टेम्पलेट आपसे थीम का नाम, पैकेज slug, version, और कुछ अन्य वेरिएबल पूछता है। यह पूरा होने पर आपके पास एक self-contained पैकेज होता है, जिसमें शामिल हैं:

* थीम class, icon set, और class map वाली एक `src/` डायरेक्टरी।
* पूर्व-कॉन्फ़िगर की गई `templates/`, `static/`, और translation फ़ोल्डर।
* एक test suite और रन करने योग्य उदाहरण ऐप्लिकेशन।

### `BaseTheme` आर्किटेक्चर {#basetheme-architecture}

थीम rendering chain की जड़ पर होती है, और हर `Admin` इंस्टेंस में ठीक एक सक्रिय थीम होती है। एक `BaseTheme` सबक्लास इन हिस्सों को कॉन्फ़िगर करता है:

* **टेम्पलेट:** पैकेज के `templates/` फ़ोल्डर में replacement टेम्पलेट, जो `base.html`, `layout.html`, या `list.html` जैसे bare relative paths का उपयोग करते हैं। Jinja की loader chain में सक्रिय थीम प्लगइन्स के ऊपर होती है, इसलिए यह कोर और प्लगइन दोनों टेम्पलेट को री-स्टाइल कर सकती है।
* **स्टैटिक एसेट:** पैकेज की `static/` डायरेक्टरी में stylesheets, scripts, और images।
* **icon set:** `get_icon_set()` से रिटर्न होने वाला कस्टम `IconSet` सबक्लास, जो `list.new` या `auth.logout` जैसी semantic keys को CSS classes में मैप करता है।
* **Class map:** `get_class_map()` से रिटर्न होने वाला एक `ClassMap` सबक्लास, जैसा कि [class map के साथ कंपोनेंट री-स्टाइल करना](#restyling-components-with-a-class-map) में वर्णित है।
* **टेम्पलेट globals:** `template_globals()` को ओवरराइड करके Jinja को expose किए गए global वेरिएबल।

### उदाहरण थीम पैकेज {#example-theme-package}

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### टेम्पलेट loader पदानुक्रम {#template-loader-hierarchy}

टेम्पलेट इंजन फ़ाइलों को इस क्रम में resolve करता है:

1. आपकी `templates_dir`, जो इसके नीचे की हर चीज़ को ओवरराइड करती है।
2. सक्रिय थीम की `templates/`, जो कोर और प्लगइन टेम्पलेट को री-स्टाइल करती है।
3. Namespaced प्लगइन `templates/`।
4. कोर `starlette_admin` डिफ़ॉल्ट टेम्पलेट।

User override या थीम सबक्लास से कोई थीम टेम्पलेट extend करने के लिए, `@theme` Jinja prefix का उपयोग करें, जैसे `{% extends "@theme/layout.html" %}`।

## कस्टम टेम्पलेट डायरेक्टरी {#custom-templates-directory}

पूरी थीम बनाए बिना डिफ़ॉल्ट HTML को ओवरराइड करने के लिए, `templates_dir` को एक डायरेक्टरी पथ पास करें।

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

उस डायरेक्टरी में आपकी रखी गई कोई भी फ़ाइल उसी relative path पर बिल्ट-इन टेम्पलेट को shadow कर देती है, और बिल्ट-इन ट्री का बाकी हिस्सा पहले की तरह render होता रहता है। ओवरराइड करने योग्य टेम्पलेट की पूरी सूची के लिए [टेम्पलेट](templates.md) देखें।

## कस्टम स्टैटिक डायरेक्टरी {#custom-static-directory}

पूरी थीम बनाए बिना अपनी CSS, JavaScript, या images जोड़ने के लिए, `static_dir` को एक डायरेक्टरी पथ पास करें।

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

इस डायरेक्टरी की फ़ाइलें `/admin/static/` के अंतर्गत बिल्ट-इन एसेट के साथ serve की जाती हैं। उदाहरण के लिए, `my_static/custom.css` पर मौजूद फ़ाइल `/admin/static/custom.css` पर उपलब्ध हो जाती है।

अपने टेम्पलेट से stylesheet को इस तरह reference करें:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## आगे क्या {#whats-next}

* **[टेम्पलेट](templates.md):** पूरे टेम्पलेट ट्री को fork किए बिना एक single पेज, सेल, या विजेट को ओवरराइड करें।
* **[एक्सटेंशन पॉइंट्स](extension-points.md):** बुनियादी थीम से आगे hooks और customization points देखें।
* **[क्विकस्टार्ट](../getting-started/quickstart.md):** शुरुआत से एक चालू एडमिन इंटरफ़ेस बनाएँ।
