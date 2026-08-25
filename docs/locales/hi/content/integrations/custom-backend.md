---
title: कस्टम बैकएंड इंटीग्रेशन
description: starlette-admin के लिए एक कस्टम बैकएंड अडैप्टर बनाना सीखें, ताकि अपने
  स्वयं के ORM या API डेटास्टोर को एडमिन UI से जोड़ सकें।
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# कस्टम बैकएंड {#custom-backends}

`starlette-admin` SQLAlchemy, SQLModel, Beanie, MongoEngine, और Tortoise ORM के लिए बिल्ट-इन बैकएंड प्रदान करता है, लेकिन एडमिन पैनल पूरी तरह स्टोरेज-अज्ञेयवादी (storage-agnostic) है। प्रत्येक बैकएंड वास्तव में `BaseModelView` की एक सबक्लास होता है। यह क्लास मानक CRUD ऑपरेशनों को उन कमांड में बदलती है जिन्हें आपका विशिष्ट डेटा स्रोत समझता है। चाहे आप REST API, Redis, ORM-रहित कोई लेगेसी डेटाबेस, या TinyDB जैसा कोई हल्का डॉक्यूमेंट स्टोर उपयोग कर रहे हों, इंप्लीमेंटेशन की प्रक्रिया एक जैसी ही रहती है।

## आवश्यक मेथड {#required-methods}

`BaseModelView` के लिए आपको छह abstract मेथड इंप्लीमेंट करने होते हैं। ये छह मेथड देकर, आप स्वचालित रूप से एडमिन की पूरी फ़ीचर श्रृंखला इनहेरिट कर लेते हैं: listing, searching, sorting, filtering, pagination, creation, editing, importing, exporting, और deletion.

```python
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.filters import FilterGroup
from starlette_admin.views import BaseModelView


class MyBackendView(BaseModelView):
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        ...

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        ...

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        ...

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        ...

    async def create(self, request: Request, data: dict) -> Any:
        ...

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        ...

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ...

```

| मेथड | कब कॉल होता है | क्या लौटाता है |
| --- | --- | --- |
| **`find_all`** | लिस्ट पेज, export | `q`, `sorts`, और `filters` से मैच करने वाले रिकॉर्ड का एक पेज |
| **`count`** | लिस्ट पेज pagination, export cap जाँच | `q` और `filters` से मैच करने वाले रिकॉर्ड की कुल संख्या |
| **`find_by_pk`** | Detail, edit, single delete, row actions | एक रिकॉर्ड, या न मिलने पर `None` |
| **`find_by_pks`** | Bulk actions, bulk delete, export-selected | दिए गए primary key से मैच करने वाले रिकॉर्ड का अनुक्रम |
| **`create`** | Create फ़ॉर्म सबमिशन, import | नया बनाया गया रिकॉर्ड |
| **`edit`** | Edit फ़ॉर्म सबमिशन | अपडेट किया गया रिकॉर्ड |
| **`delete`** | Bulk delete, row delete | डिलीट किए गए रिकॉर्ड की संख्या, या `None` |

रिक्वेस्ट की query string (जैसे `?page=2&sort=views__desc&q=fire`) को पार्स करना एडमिन स्वयं आंतरिक रूप से संभालता है। आपको raw request parameter कभी पार्स करने की ज़रूरत नहीं पड़ेगी। जब तक `find_all` या `count` कॉल होता है, एडमिन इनपुट पहले ही प्रोसेस कर चुका होता है:

* **Pagination**, `skip` और `limit` में बदल दिया जाता है (`skip = (page - 1) * page_size`)।
* **Search** सादे string `q` के रूप में दिया जाता है।
* **Sorting**, `(field_name, direction)` tuples की प्राथमिकता-क्रमित सूची के रूप में फ़ॉर्मेट किया जाता है।
* **Filters**, एक संरचित `FilterGroup` ट्री में पार्स किए जाते हैं।

आपका एकमात्र कार्य इन संरचित arguments को अपने बैकएंड की native query language में बदलना है।

## View key, display name, और fields {#view-key-display-name-and-fields}

रेंडरिंग से पहले, डेटा की संरचना और routing को समझने के लिए एक `ModelView` को चार core attributes की आवश्यकता होती है:

| Attribute | उद्देश्य |
| --- | --- |
| **`key`** | Unique URL slug (जैसे, `/admin/post/list`) और event subscriptions के लिए internal key. |
| **`display_name`** / **`menu_label`** | UI के लिए प्रदर्शित नाम। `display_name` फ़ॉर्म titles के लिए singular होता है, जबकि `menu_label` navigation और लिस्ट पेजों के लिए plural होता है। |
| **`pk_attr`** | वह विशिष्ट फ़ील्ड नाम जो एक रिकॉर्ड को unique रूप से पहचानता है। |
| **`fields`** | दिखाने और संपादित करने के लिए columns परिभाषित करने वाले `BaseField` instances की सूची। |

बिल्ट-इन बैकएंड आपके models की introspection करके इन attributes को स्वचालित रूप से populate करते हैं। उदाहरण के लिए, SQLAlchemy `ModelView` mapper के columns और primary key पढ़ता है। यह introspection एक `BaseModelConverter` सबक्लास द्वारा संभाली जाती है। ये converters native column types को उनके संगत `BaseField` समकक्षों में मैप करने के लिए `@converts(...)` decorators का उपयोग करते हैं।

REST API या साधारण dictionary store जैसे introspectable model के बिना बैकएंड बनाते समय, आपको इन चारों attributes को class attributes के रूप में स्पष्ट रूप से सेट करना होगा:

```python
class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
    ]

```

fields को स्पष्ट रूप से सूचीबद्ध करना one-off views के लिए सबसे सरल तरीका है। हालाँकि, यदि आप कस्टम बैकएंड पर कई models के लिए designed एक reusable `ModelView` base class बना रहे हैं, तो आपको इसके बजाय एक कस्टम `BaseModelConverter` लिखना चाहिए। `convert()` और `convert_fields_list()` मेथड इंप्लीमेंट करें, अपने type handlers को `@converts(...)` से decorate करें, और initialization के दौरान converter को invoke करें। इससे concrete views फ़ील्ड परिभाषाएँ स्वचालित रूप से इनहेरिट कर लेते हैं, जो बिल्ट-इन बैकएंड के व्यवहार से मेल खाता है।

## फ़िल्टर ट्री प्रोसेस करना {#processing-filter-trees}

फ़िल्टर आपके मेथड को एक `FilterGroup` के रूप में पास किए जाते हैं। यह संरचना logical AND/OR nodes का एक ट्री होती है जिसमें `FilterRule` leaf objects होते हैं:

```python
@dataclass
class FilterRule:
    field: str
    filter: str         # The slug of the BaseFilter to apply (e.g., "contains", "gte")
    value: Any = None
    value2: Any = None  # Only populated for filters with has_value2 (e.g., "between")

@dataclass
class FilterGroup:
    logic: str = "and"  # Accepts "and" or "or"
    rules: list["FilterGroup | FilterRule"] = field(default_factory=list)

```

इस ट्री को डेटाबेस क्वेरी में बदलने के लिए, आपको इसे recursively walk करना होगा। प्रत्येक `FilterRule` के लिए, अपनी `FilterRegistry` से मैचिंग concrete filter class प्राप्त करें और उसकी `apply()` मेथड कॉल करें। नेस्टेड `FilterGroup` nodes के लिए, recurse करें और उपयुक्त logical operator का उपयोग करके resulting फ़्रैगमेंट को संयोजित करें।

TinyDB reference example द्वारा उपयोग किया जाने वाला यही `build_query` pattern है:

```python
def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (combined | fragment) if group.logic == "or" else (combined & fragment)
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)

```

प्रत्येक concrete filter पर `apply(ctx)` मेथड एक `FilterApplyContext` object प्राप्त करती है जिसमें `query`, `field name`, और `values` होते हैं। यह आपके बैकएंड language के लिए विशिष्ट एक query fragment लौटाती है। चूँकि यह प्रक्रिया shared state को mutate करने से बचती है, आपका underlying डेटाबेस architecture चाहे जो भी हो, resulting rules को cleanly संयोजित कर सकते हैं।

## TinyDB reference example {#the-tinydb-reference-example}

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) [TinyDB](https://github.com/msiemens/tinydb) पर आधारित एक पूर्ण रूप से runnable एडमिन पैनल है। TinyDB एक document store है जो डेटा को एक local JSON फ़ाइल में सहेजता है। यह एक उत्कृष्ट reference point का काम करता है क्योंकि इसमें कोई ORM नहीं होता, यानी प्रत्येक मेथड सीधे data store के साथ interact करती है।

### Model परिभाषा (`models.py`) {#model-definition-modelspy}

data model एक मानक Python dataclass होता है जिसमें कोई admin-specific logic नहीं होता:

```python
@dataclass
class Post:
    title: str
    body: str
    tags: list[str]
    views: int = 0
    comments: list[Comment] = field(default_factory=list)
    cover: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags))
        )

```

`search_query` मेथड relevant fields पर full-text search जनरेट करके `q` parameter को संभालती है।

### View इंप्लीमेंटेशन (`view.py`) {#view-implementation-viewpy}

`PostView` इंप्लीमेंटेशन search query को फ़िल्टर ट्री के साथ merge करने के लिए `_build_query` का उपयोग करता है। TinyDB search निष्पादित करने से पहले `find_all` और `count` दोनों इस helper पर निर्भर करते हैं:

```python
async def _build_query(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> QueryInstance | None:
    query = None
    if q is not None:
        query = Post.search_query(q)
    if filters is not None and not filters.is_empty():
        fields_by_name = {field.name: field for field in self.get_fields_list(request)}
        filter_query = build_query(filters, fields_by_name, self.get_filter_registry())
        if filter_query is not None:
            query = filter_query if query is None else (query & filter_query)
    return query

async def find_all(
    self,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sorts: list[tuple[str, str]] | None = None,
    filters: FilterGroup | None = None,
) -> Sequence[Any]:
    query = await self._build_query(request, q, filters)
    docs = self.db.search(query) if query is not None else self.db.all()
    values = [Post.from_document(doc) for doc in docs]
    for sort_by, sort_dir in reversed(sorts or []):
        values.sort(
            key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
            reverse=(sort_dir == "desc"),
        )
    if limit > 0:
        return values[skip : skip + limit]
    return values[skip:]

async def count(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> int:
    query = await self._build_query(request, q, filters)
    return len(self.db.search(query)) if query is not None else len(self.db.all())

```

चूँकि TinyDB में native sorting capabilities नहीं होतीं, sorting logic Python में निष्पादित होती है। sorts को reverse order में apply करने से एक विश्वसनीय multi-key sort बनता है।

Write operations (`create`, `edit`, `delete`) डेटाबेस को सीधे modify करते हैं। सबसे महत्वपूर्ण बात, ये view के event hooks भी fire करते हैं, जिससे lifecycle events सही ढंग से trigger होते हैं:

```python
async def create(self, request: Request, data: dict) -> Any:
    await self.validate_data(data)
    obj = Post(**data)
    await self._emit_before_create(request, data, obj)
    new_id = self.db.insert(obj.to_dict())
    obj = await self.find_by_pk(request, new_id)
    await self._emit_after_create(request, obj)
    return obj

async def delete(self, request: Request, pks: list[Any]) -> int | None:
    ids = list(map(int, pks))
    objs = [Post.from_document(self.db.get(doc_id=i)) for i in ids if self.db.contains(doc_id=i)]
    for obj in objs:
        await self._emit_before_delete(request, await self.get_pk_value(request, obj), obj)
    removed = self.db.remove(doc_ids=ids)
    for obj in objs:
        await self._emit_after_delete(request, await self.get_pk_value(request, obj), obj)
    return len(removed)

```

### ऐप्लिकेशन wiring (`app.py`) {#application-wiring-apppy}

आपको एक विशेष `Admin` सबक्लास की आवश्यकता नहीं है। बेस `Admin` universally काम करता है क्योंकि `BaseModelView` सभी बैकएंड details को abstract कर देता है:

```python
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB
from view import PostView

db = TinyDB(Path(__file__).parent / "db.json")

app = Starlette()
admin = Admin(debug=True, secret_key="123456")
admin.add_view(PostView(db))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

इस इंप्लीमेंटेशन का परीक्षण करने के लिए, example directory से `uv run app.py` चलाएँ और `http://localhost:8000/admin/` पर जाएँ।

## कस्टम फ़ील्ड फ़िल्टर {#custom-field-filters}

फ़िल्टर आपके विशिष्ट बैकएंड syntax से गहराई से जुड़े होते हैं। एक "contains" operation के लिए TinyDB, SQL, और MongoDB में पूरी तरह अलग कोड चाहिए। प्रत्येक कस्टम बैकएंड को अपनी `BaseFilter` सबक्लास को एक `FilterRegistry` में register करना होगा और उन्हें `get_filter_registry()` के माध्यम से लौटाना होगा।

एक फ़िल्टर बनाने के लिए, `EqualFilter` या `ContainsFilter` जैसे base type को subclass करें और `apply` मेथड इंप्लीमेंट करें:

```python
import re

from starlette_admin.filters import FilterApplyContext
from starlette_admin.filters.string import ContainsFilter
from tinydb import Query
from tinydb.queries import QueryInstance


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return Query()[ctx.field_name].search(re.escape(ctx.value), flags=re.IGNORECASE)

```

registry बनाने की सर्वोत्तम प्रथा यह है कि `FilterRegistry` को subclass किया जाए और field-specific methods को `@filters(...)` से decorate किया जाए। shipped बैकएंड द्वारा उपयोग किया जाने वाला यही सटीक pattern है:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterRegistry, filters
from starlette_admin.filters.generic import IsNotNullFilter, IsNullFilter
from starlette_admin.filters.numeric import EqualFilter, GreaterThanFilter, LessThanFilter


class TinyDBFilterRegistry(FilterRegistry):
    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type]:
        # Ensures every field is filterable by null-ness, even without specific registrations.
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type]:
        return [TinyDBContainsFilter, EqualFilter, IsNullFilter, IsNotNullFilter]

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type]:
        return [EqualFilter, GreaterThanFilter, LessThanFilter, IsNullFilter, IsNotNullFilter]


class PostView(BaseModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return TinyDBFilterRegistry()

```

यदि किसी field की कोई मैचिंग registry entry नहीं है और उसमें explicit `filters=[]` override भी नहीं है, तो वह filterable नहीं होगा। TinyDB example `filters=[]` override technique का उपयोग करके जान-बूझकर `id` field को unfilterable छोड़ता है।

dynamic schemas के लिए जहाँ filterable types runtime तक अज्ञात रहते हैं, `FilterRegistry` एक imperative `register(field_type, *filter_classes)` मेथड प्रदान करता है।

## Lifecycle events प्रबंधित करना {#managing-lifecycle-events}

आपका कस्टम बैकएंड `create`, `edit`, और `delete` मेथड को पूरी तरह स्वयं संभालता है। चूँकि `BaseModelView` कभी भी सीधे आपके data source को छूता नहीं, write होते समय आपको उसे स्पष्ट रूप से सूचित करना होगा। ऐसा न करने से दो core systems चुपचाप टूट जाते हैं:

1. **Method hooks:** अपनी `ModelView` पर `before_create` और `after_create` overrides.
2. **Event subscribers:** `view.events` या `admin.events` पर registered handlers.

Notification `BaseModelView` पर परिभाषित paired helper methods को कॉल करके की जाती है। प्रत्येक helper संगत method hook को invoke करता है और एक `AdminEvent` emit करता है।

| मेथड | Pre-Write Helper | Post-Write Helper |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

Pre-write call submitted data से बनाई गई in-memory object को स्वीकार करती है। यह handlers को exception raise करके write को reject करने का अंतिम अवसर देती है। Post-write call के लिए persisted object, जैसा वह डेटाबेस से वापस पढ़ा गया है, आवश्यक है। इसीलिए TinyDB की `create` मेथड initial in-memory object लौटाने के बजाय record को दोबारा fetch करती है।

दो अतिरिक्त helpers, `_emit_after_create_committed` और `_emit_after_edit_committed`, two-phase commits या session semantics वाले बैकएंड का समर्थन करते हैं। जब तक आपका डेटाबेस सख़्त transaction boundary enforce नहीं करता, इन्हें पूरी तरह छोड़ दें।

Export और import operations को manual event wiring की आवश्यकता नहीं होती। `BaseAdmin` class इन lifecycle events को स्वचालित रूप से संभालता है।

---

### अतिरिक्त संसाधन {#additional-resources}

* **[Views](../user-guide/views.md)**: बैकएंड से स्वतंत्र `BaseModelView` कॉन्फ़िगरेशन विकल्प देखें।
* **[Custom Filters](../advanced/custom-filters.md)**: शुरुआत से custom फ़िल्टर लिखना और register करना सीखें।
* **[Events](../advanced/events.md)**: method hooks, event bus, और execution priorities सहित पूर्ण event subscription API को समझें।
