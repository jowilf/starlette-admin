---
title: इवेंट
description: AFTER_CREATE जैसे ग्लोबल लाइफ़साइकिल इवेंट की सदस्यता लेकर ऑडिट लॉग,
  webhook, और असिंक्रोनस वर्कफ़्लो बनाएँ।
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# इवेंट {#events}

`before_create` जैसा method hook केवल उसी view के लिए चलता है जो उसे परिभाषित करता है। इवेंट सिस्टम से उस view के बाहर का कोड उसके अंदर हुई चीज़ों पर प्रतिक्रिया दे सकता है — यानी एक audit log, webhook, या cache invalidation एक ही जगह रह सकता है, आपके द्वारा लिखे गए हर `ModelView` में copy-paste होने के बजाय।

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

इसे एक बार, अपने `admin` इंस्टेंस के पास रजिस्टर करें — और हर view का create endpoint इसे कॉल करेगा, जिनमें आपके द्वारा बाद में जोड़े गए views भी शामिल हैं।

## View vs. admin level

हर view में एक `events` attribute होता है जिसकी आप सीधे सदस्यता ले सकते हैं — केवल उस view तक सीमित। `Admin` इंस्टेंस के पास भी एक होता है, जो उस पर रजिस्टर हर view तक पहुँचता है, और `keys=` पास करने पर एक subset तक।

* **`view.events.on(...)`**: केवल उसी view के लिए चलता है।
* **`admin.events.on(...)`**: हर वर्तमान और भविष्य के view के लिए चलता है, जब तक आप इसे `keys=` से सीमित न करें।

आप `admin.events` पर `admin.add_view(...)` से पहले भी रजिस्टर कर सकते हैं और बाद में भी। क्रम मायने नहीं रखता: पहले रजिस्टर किया गया handler भी view जोड़ते ही उस से जुड़ जाता है।

## Method hooks vs. event subscriptions

दोनों request lifecycle में एक ही बिंदु पर चलते हैं। अंतर कोड की जगह और उसकी पहुँच (कितने views) में है।

| Feature | Method hook (`before_create`, ...) | Event subscription (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Where the code lives** | Inside the view class | Anywhere, for example a module-level function or a subscriber class |
| **Scope** | That specific view | One view (`view.events`) or every view (`admin.events`) |
| **Good for** | Logic specific to that resource (slugify a title, stamp a timestamp) | Cross-cutting concerns (audit logs, notifications, plugins) |
| **Multiples allowed?** | No, one method per view | Yes, any number of handlers per event, ordered by priority |

जब logic model की अंतर्निहित (intrinsic) हो, method hook का उपयोग करें। जब वह किसी एक view से संबंधित न हो, या आप उसे कई एडमिन में reusable रूप से शिप कर रहे हों, event subscription का उपयोग करें।

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## AdminEvent values

`AdminEvent` एक string enum है। निम्नलिखित members view lifecycle द्वारा सक्रिय रूप से emit किए जाते हैं:

| Event | Fired when | Context class |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Record created | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Create transaction committed | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Record updated | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Edit transaction committed | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Record deleted | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Delete transaction committed | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Batch or row action run | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Export triggered | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Import triggered | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Login succeeds | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED`, और `AFTER_DELETE_COMMITTED` केवल उन बैकएंड के लिए चलते हैं जो commit को request के अंत तक टालते हैं — आज इसका अर्थ है SQLAlchemy backend। इन्हें emit करने वाले `after_create_committed`, `after_edit_committed`, और `after_delete_committed` hook methods के लिए [Views](../user-guide/views.md#lifecycle-hooks) देखें।

`AFTER_DELETE_COMMITTED` के लिए `ctx.obj` एक detached instance होता है: उसके पहले से लोड attributes readable रहते हैं, लेकिन delete से पहले जो attribute लोड नहीं हुआ था, उसे पढ़ने पर exception आता है, क्योंकि उसके पीछे की row अब गई चुकी है।

हर context एक dataclass है जो `EventContext` से inherit करती है; वह सभी events के common fields carry करती है:

| Attribute | Type | Description |
| --- | --- | --- |
| `event` | `AdminEvent` or `str` | The event that fired |
| `request` | `Request` | The request in flight |
| `view_key` | `str` | The view's `key` |
| `extra` | `dict` | Empty by default, free for you to stash data in a custom handler chain |

प्रत्येक subclass उस event से संबंधित fields जोड़ती है।

[inline edit](../user-guide/inline-edit.md) से लिस्ट पेज पर fire हुए edit events `extra["inline"] = True` carry करते हैं, और उनके `data` / `old_data` payloads में केवल edited field होती है। बाकी सब सामान्य edit जैसा ही है, इसलिए existing handlers में कोई बदलाव ज़रूरी नहीं।

## Decorator से सदस्यता {#subscribing-with-a-decorator}

`view.events.on()` decorator और सीधे function call — दोनों रूपों में काम करता है:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

इस तरह रजिस्टर करने पर `log_deletion` केवल `order_view` के लिए चलता है, एडमिन के अन्य views के लिए नहीं। `on()` मेथड handler को decorator form के बिना, सीधे भी स्वीकार करता है:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: handlers को group करना {#admineventsubscriber-grouping-handlers}

जब एक concern कई events पर प्रतिक्रिया दे, तो `AdminEventSubscriber` उन्हें module-level functions में बिखेरने के बजाय एक ही क्लास में रखता है। methods को `@on(AdminEvent.X)` से decorate करें — यह bus मेथड नहीं बल्कि `starlette_admin.events` का module-level `on` है — फिर एक बार `subscribe()` कॉल करें:

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` `view.events` और `admin.events` — दोनों पर उपलब्ध है। subscriber को किसी एक view तक सीमित रखने के लिए इसे `view.events` पर कॉल करें।

एक method कई events handle कर सकती है: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` वही method दोनों के लिए रजिस्टर करता है।

## admin.events: views को delegate करना {#adminevents-delegating-to-views}

`admin.events.on()` वही arguments लेता है जो `view.events.on()`, साथ में `keys=` — उन view keys की list जिन तक subscription सीमित करनी है। इसे unset छोड़ें (`None`, डिफ़ॉल्ट) और हर वर्तमान व भविष्य के model view को handler मिल जाता है:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

केवल वही view — जिसे `key="order"` दिया गया है या जिसका default key `"order"` resolve होता है — यह handler कॉल करता है। किसी अन्य view पर आया `AFTER_CREATE` इसे trigger नहीं करेगा।

`admin.events.subscribe()` भी `keys=` स्वीकार करता है, ताकि आप उसी तरह `AdminEventSubscriber` को views के किसी subset तक सीमित कर सकें:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` केवल ऊपर की तालिका के view-lifecycle events को प्रभावित करता है: create, edit, delete, action, export, और import। `admin.events` इसी तरह तय करता है कि handler किन views पर लागू होगा। `AFTER_LOGIN` admin-level है और किसी view से बंधा नहीं है, इसलिए उसके लिए `keys=` कुछ नहीं करता।

## Priority

`on()` एक `priority` keyword लेता है — integer, डिफ़ॉल्ट `0`। एक ही event के handlers descending priority order में चलते हैं, यानी बड़ी संख्या पहले fire होती है:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

एक ही priority वाले handlers registration order में चलते हैं। `AdminEventSubscriber` methods priority को `@on(AdminEvent.X, priority=10)` के माध्यम से लेती हैं, जिसे उसी तरह forward किया जाता है।

!!! warning
    कोई भी `BEFORE_DELETE` handler — या कोई भी `BEFORE_*` handler — exception उठाने पर ऑपरेशन को रोक देता है, और उस event के बाद के handlers नहीं चलते। Exception उठाने वाला `AFTER_*` handler पहले से committed बदलाव को failed request में बदल देता है। यदि किसी failure को admin error के रूप में सामने नहीं आना चाहिए, तो network calls या third-party APIs जैसे risky logic को handler के अंदर अपने `try`/`except` ब्लॉक में लपेटें।

## Extended example

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) इस पेज के हर pattern को एक साथ चलाता है: `PostView` पर hook overrides, हर view के लिए `admin.events` पर रजिस्टर एक `AuditSubscriber`, delete/export/import warnings के लिए सीधा handler registration, `post_view.events` तक सीमित एक handler, और `comment_view.events` तक सीमित एक `CommentModerationSubscriber`। Priority और scope का परस्पर संवाद देखने के लिए इसे चलाएँ।

---

## आगे क्या {#whats-next}

* **[व्यूज़](../user-guide/views.md)**: इस पेज की नींव बनने वाले `before_*` और `after_*` method hooks.
* **[एक्शन](../user-guide/actions.md)**: Batch और row actions, जो `BEFORE_ACTION` / `AFTER_ACTION` emit करते हैं।
* **[Inline Forms](../user-guide/inline-forms.md)**: Parent के साथ बनाए जाने वाले nested records.
