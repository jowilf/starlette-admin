---
title: मूल अवधारणाएँ
description: starlette-admin के आर्किटेक्चरल डिज़ाइन सिद्धांतों को समझें — declarative
  views, URL-based state, और backend-agnostic models सहित।
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# मूल अवधारणाएँ {#core-concepts}

`PostView` लिखकर और admin instance mount करके Quickstart पूरा करने के बाद, फ़्रेमवर्क के आर्किटेक्चरल डिज़ाइन सिद्धांत जानें। ये मूल अवधारणाएँ शेष documentation की नींव provide करती हैं।

## One class per resource

Admin जिस resource को manage करता है, वह single, dedicated class के माध्यम से expose होती है। `ModelView` subclass करके उसे database model की ओर point करते ही, आप सभी standard CRUD operations (list, detail, create, edit, delete) के लिए paginated, sortable, filterable views automatically generate कर लेते हैं।

इससे custom routes या HTML templates लिखने की ज़रूरत ख़त्म हो जाती है। Resource कैसा दिखे, validate कैसे हो, और कैसे behave करे — यह सब govern करने वाला कुछ भी इसी एक view class के भीतर रहता है।

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## The same view, any backend

Views आपके data से adaptable backend layer के माध्यम से interface करते हैं। आपका application SQLAlchemy, SQLModel, Beanie, MongoEngine, या Tortoise ORM में से कुछ भी उपयोग करे, configuration API ठीक वही रहता है।

Fields, filters, permissions, और lifecycle hooks data चाहे कहीं भी रहे, consistently काम करते हैं। एक backend पर अर्जित ज्ञान दूसरों पर सीधे transfer होता है। underlying data source swap करने के लिए import statements update करना ही काफ़ी है।

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## URL-based list state

Sorting, filtering, pagination, और search criteria URL query string से सीधे sync रहते हैं। Server list states पूरी तरह इन URL parameters से render करता है, इसलिए हर view state inherently bookmarkable और shareable होता है।

आप कोई specific administrative link colleague को भेजें, तो वह बिल्कुल वही filtered rows और sorting configuration देखता है जो आप देखते हैं।

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Fields स्वयं render होना जानते हैं {#fields-know-how-to-render-themselves}

Fields self-rendering components हैं। प्रत्येक field type तीन distinct contexts में अपनी display logic manage करता है: list table के भीतर एक cell, detail view में एक row, और form के भीतर input element.

View build करते समय आप field instances declare करते हैं या attribute names pass करते हैं जिन्हें backend automatically fields पर map करता है। Data model से match करने वाला type चुनें — rendering framework handle कर लेगा:

* text strings के लिए `StringField`
* numerical data के लिए `IntegerField`
* file uploads के लिए `ImageField`

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Declarative form layouts

डिफ़ॉल्ट रूप से `fields` attribute create/edit forms को flat, vertical list के रूप में render करता है। Underlying data definitions बदले बिना user interface reorganize करने के लिए `form_layout` attribute का उपयोग करें।

### Tuple shorthand {#the-tuple-shorthand}

Basic grid layouts के लिए field names को tuple में group करें ताकि वे एक row में side by side render हों। इससे complex widget classes import करने की ज़रूरत नहीं रहती।

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Advanced layout widgets

Forms के complexity बढ़ने पर उन्हें layout widgets से structure कर सकते हैं। Tuple shorthand इन components के अंदर natively काम करता है:

* **`PanelWidget` या `FieldsetWidget`:** Related fields को clear heading के अंतर्गत group करने या sections collapsible बनाने के लिए इन components का उपयोग करें।
* **`TabsWidget`:** जब resource में data की distinct categories (जैसे shipping और SEO metadata) हों जिन्हें simultaneously visible होने की ज़रूरत नहीं, तब इस component का उपयोग करें।

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

## Filters field types से जुड़े होते हैं {#filters-are-attached-to-field-types}

Filtering capabilities सीधे data types पर map होती हैं, जिससे users केवल relevant query options देखते हैं। `StringField` contextual text options देता है — *contains*, *starts with*, *equals*, *is null*. Integer field numerical constraints देता है — *greater than* या *between*.

आप `filters` parameter से किसी individual field पर इन defaults को restrict या override कर सकते हैं, या unique data types के लिए custom filters register कर सकते हैं।

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Bring your own authentication

Built-in user model छोड़कर framework आपके user schema के मामले में पूरी तरह agnostic रहता है। Authentication के लिए single method implement करनी होती है: `authenticate(request)`.

इस method को अपने existing authentication infrastructure से connect करें — local database table, OAuth provider, या upstream single sign-on (SSO) proxy header. `AdminUser` object return करने पर interface access मिलता है; `None` return करने पर access deny होता है।

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Actions selected rows पर चलते हैं {#actions-run-on-selected-rows}

Batch actions top toolbar से select की गई multiple rows पर operate करते हैं, और row actions individual records पर inline execute होते हैं। View method को `@action` या `@row_action` से decorate करने पर method बिना manual route registration के automatically user interface में expose हो जाता है।

Action method से message string return करने के बजाय built-in `flash()` utility से सीधे user notifications trigger करें।

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Native data export और import {#native-data-export-and-import}

हर list page में export dialog होता है जिससे users scope (selected rows या current page), fields, format, और filename चुन सकते हैं। Active filters और search terms preserve रहते हैं — exported file बिल्कुल वही होती है जो screen पर दिखती है।

Framework natively CSV, JSON, और PDF formats support करता है। Excel (`xlsx`) जैसे additional formats के लिए framework `tablib` से integrate होकर compatible file types support करता है। Formats plain extension strings के रूप में declare होते हैं। Access control `can_export` hook से granular level पर manage होता है।

Import wizard इन्हीं formats में bulk data safely ingest करता है। Wizard upload को पहले preview step में validate करता है — database writes commit होने से पहले errors को row by row highlight करता है — और optional primary key upserts support करता है। इस feature तक access `can_import` hook से restrict कर सकते हैं।

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Flexible file storage

`FileField` और `ImageField` के माध्यम से media management underlying `Storage` abstraction layer पर टिकी है। Local disk writes के लिए `LocalStorage`, या optional S3 integration `pip install starlette-admin[s3]` चलाकर इंस्टॉल करें।

Storage configuration की ओर point करते ही field file uploads, backend validation, और frontend rendering को automatically coordinate कर देता है।

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Custom views और dashboard widgets {#custom-views-and-dashboard-widgets}

Database model से explicitly tied न होने वाले pages — metrics dashboards या custom reports — `CustomView` से बनते हैं। Content `widget` parameter से populate होता है। यह parameter static `BaseWidget` instance या dynamic callable accept करता है; content incoming request पर निर्भर हो तो callable उस समय execute होता है।

Layout primitives और data visualization widgets को clean hierarchy में arrange करके complex user interfaces compose कर सकते हैं।

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## Events और method hooks {#events-and-method-hooks}

Framework create/update/delete cycles के दौरान code execute कराने के लिए दो distinct extension points देता है:

1. **Lifecycle methods:** Specific entity तक सीमित logic के लिए view class पर ही `before_create` जैसी local methods override करें।
2. **Event listeners:** Audit logs, cache invalidation, या webhooks जैसी global concerns के लिए `admin.events` system की सदस्यता लें।

दोनों patterns identical execution points पर trigger होते हैं, इसलिए आप application architecture के लिए सबसे उपयुक्त approach चुन सकते हैं।

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**आगे क्या**

* **[व्यूज़](../user-guide/views.md):** हर `ModelView` configuration option.
* **[फ़ील्ड्स](../user-guide/fields.md):** पूरा field type catalog.
* **[Form Layouts](../advanced/form-layout.md):** Create/edit forms को rows, panels, और tabs से arrange करें।
* **[एक्शन](../user-guide/actions.md):** Batch और row actions विस्तार से।
