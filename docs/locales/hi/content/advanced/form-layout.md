---
title: फ़ॉर्म लेआउट
description: starlette-admin में TabsWidget, FieldsetWidget, और grid कॉलम का उपयोग
  करके जटिल, responsive फ़ॉर्म लेआउट डिज़ाइन करें।
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# फ़ॉर्म लेआउट {#form-layouts}

डिफ़ॉल्ट रूप से, create औ edit फ़ॉर्म `fields` में सब कुछ एक flat लिस्ट के रूप में रेंडर करते हैं। `form_layout` attribute से आप उन inputs को वहीं composable widgets से व्यवस्थित कर सकते हैं जिनका उपयोग आप [dashboards](../user-guide/custom-views.md) में करते हैं: side-by-side rows, titled या collapsible panels, tabs, static content, और अपने कस्टम widgets।

## Basic usage

सबसे सरल layout को किसी widget की ज़रूरत नहीं होती। किसी field को string नाम से reference करने पर वह अपनी line पर रहता है; names को tuple में group करने पर वे एक row में side-by-side आ जाते हैं।

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

ऊपर दिए layout में:

* `("first_name", "last_name")` एक row बनाता है जो दोनों inputs के बीच समान रूप से बँटता है।
* `"email"` ठीक नीचे अपनी line पर render होता है।
* `("salary", "notes")` एक और multi-column row बनाता है।

आप एक row में कितने भी fields डाल सकते हैं और single-column तथा multi-column rows को freely mix कर सकते हैं।

Container widgets इस shorthand को स्वयं expand करते हैं: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget`, और `Col` — construct होते समय tuples को rows और lists को stacked columns में बदल देते हैं। इसलिए shorthand nested `children` attributes के अंदर और [`CustomView.widget`](../user-guide/custom-views.md) dashboard के अंदर भी काम करता है।

## Fields को group करना {#grouping-fields}

### Titled panels

Fields के किसी group को title देने या उसे collapsible बनाने के लिए उसे `PanelWidget` में लपेटें। Widget top level वही string और tuple shorthand स्वीकार करता है।

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` ये attributes लेता है:

| Attribute | Description |
| --- | --- |
| `title` | The heading shown in the panel's card header. |
| `children` | The widgets rendered inside the panel, in order. Accepts the shorthand above or nested widgets. Add a `TextWidget(card=False)` child to put explanatory text below the title. |
| `collapsible` | Lets people expand and collapse the panel. |
| `collapsed` | Starts the panel collapsed. Applies only when `collapsible=True`. |

जिस group को title नहीं चाहिए, उसके लिए `ColumnWidget` उपयोग करें। वह styled card में लपेटे बिना children को vertically stack करता है।

### Fieldsets

`FieldsetWidget` fields को `PanelWidget` की तरह ही group करता है, लेकिन styled card के बजाय native HTML `<fieldset>` और `<legend>` render करता है। सरल, bordered grouping चाहने पर इसका उपयोग करें।

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

`legend` attribute `<legend>` element में caption सेट करता है। `disabled=True` container पर HTML `disabled` attribute लगाता है, जिससे हर nested form control disable हो जाता है। `FieldsetWidget` वही `children` shorthand सपोर्ट करता है जो `PanelWidget`, पर panel-specific options जैसे `collapsible` और `icon` नहीं।

## स्पष्ट column widths {#explicit-column-widths}

Tuple shorthand हमेशा row को समान बाँटता है। Column widths पर बारीक नियंत्रण के लिए row को `RowWidget`, `Col`, और `FieldRef` से explicitly बनाएँ:

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Field labels छिपाना {#hiding-field-labels}

`FieldRef` को explicitly construct करने पर `show_label` parameter मिलता है, जो आस-पास का layout जब field का उद्देश्य पहले से स्पष्ट कर दे, `<label>` element हटा देता है।

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` का डिफ़ॉल्ट `True` है। String और tuple shorthand labels हमेशा render करते हैं, क्योंकि वे कोई keyword argument नहीं लेते।

## Input groups

`prepend` और `append` parameters input के किसी ओर एक [input group](https://docs.tabler.io/ui/forms/form-elements#input-group) addon attach करते हैं। प्रत्येक plain text या raw HTML — जैसे Font Awesome icon — स्वीकार करता है।

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Addons उन fields पर काम करते हैं जिनका form template native `<input>` element render करता है: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, numeric fields (`IntegerField`, `DecimalField`, `FloatField`), और date/time fields। अन्य types — जैसे `EnumField`, `TextAreaField`, और `BooleanField` — उन्हें silently ignore करते हैं।

!!! warning
    Addon values unescaped render होते हैं ताकि icon markup जैसा HTML काम कर सके। केवल trusted content पास करें जो आपने स्वयं लिखा हो — user input कभी नहीं।

## Tabs

Sections को tabbed interface में बाँटने के लिए `TabsWidget` का उपयोग करें। यह `(label, widgets)` pairs की list लेता है।

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Static content

Layout में कहीं भी arbitrary content render करने के लिए `HtmlWidget` और `TextWidget` का उपयोग करें: instructions, warnings, या dividers.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Custom widgets

चूँकि `form_layout` dashboards के साथ `BaseWidget` hierarchy share करता है, आप `BaseWidget` subclass करके अपने elements बना सकते हैं। built-in widgets से बाहर की किसी भी चीज़ — read-only previews, embedded charts, या custom macros — के लिए यही escape hatch है।

सामान्य pattern के लिए [Custom Views & Widgets](../user-guide/custom-views.md) और subclass override कर सकने वाले methods के लिए [Widgets API reference](../api/widgets.md) देखें। `form_layout` के custom widgets field visibility rules कुछ भी कहें, हमेशा render होते हैं।

## Access control और visibility {#access-control-and-visibility}

`form_layout` आपके field-level access rules का सम्मान करता है। हर `FieldRef` सामान्य `can_access_field` check से गुज़रता है, और `exclude_from_create`, `exclude_from_edit`, तथा role-based permissions सभी लागू रहते हैं।

* **Row expansion:** जब किसी request के लिए multi-column row का कोई field hidden हो, बाकी visible fields space भरने के लिए फैल जाती हैं।
* **Empty containers:** जब किसी container (row, panel, fieldset, column, grid, या tab) के सारे fields hidden हों, container omit हो जाता है — खाली shell कभी नहीं मिलती।
* **Static rendering:** `HtmlWidget`, `TextWidget`, और custom `BaseWidget` subclasses जैसे static components हमेशा render होते हैं, क्योंकि वे form fields पर निर्भर नहीं।

## Omitted fields संभालना {#handling-omitted-fields}

`fields` में declared किंतु `form_layout` से बाहर छूटा field declaration order में form के निचले हिस्से में append हो जाता है — कोई field चुपचाप खोता नहीं।

एक ही field को दो बार reference करने, या ऐसा नाम reference करने पर जो `fields` में नहीं है, view construct होते समय `ValueError` आता है।

---

## आगे क्या {#whats-next}

* **[Custom Views & Widgets](../user-guide/custom-views.md):** वह widget hierarchy जिस पर `form_layout` बना है, और अपना widget लिखना।
* **[Templates](templates.md):** `_form_group.html` override करके layout group का markup बदलें।
* **[फ़ील्ड्स](../user-guide/fields.md):** वे field types और visibility rules जिन्हें एक layout arrange करता है।
