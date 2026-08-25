---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# FastAPI & starlette-admin के साथ सॉफ़्ट डिलीट और ट्रैश व्यू {#soft-deletes-and-a-trash-view-with-fastapi-starlette-admin}

_2026-07-10_

मानक `DELETE` ऑपरेशन कठोर होता है। अगर ऑपरेटर ग़लत जगह क्लिक कर दे, या कोई ऑटोमेटेड क्लीनअप जॉब ग़लत फ़िल्टर पर चल जाए, तो डेटा चला गया — जब तक आप कोई जटिल डेटाबेस रीस्टोर न करें। "सॉफ़्ट डिलीट" लागू करने से यह जोखिम कम हो जाता है: रिकॉर्ड को डेटाबेस से हमेशा के लिए हटाने की बजाय उसे डिलीटेड फ़्लैग कर दिया जाता है। इस तरीक़े से डेटा रिकवरी एक साधारण अपडेट ऑपरेशन बन जाती है।

यह गाइड दिखाती है कि `starlette-admin` का इस्तेमाल करते हुए FastAPI ऐप्लिकेशन में सॉफ़्ट डिलीट पैटर्न कैसे लागू करें। हम एक पूरा समाधान बनाएँगे, जिसमें शामिल होंगे:

- एक ही डेटाबेस मॉडल
- दो अलग-अलग एडमिनिस्ट्रेटिव व्यू
- एक `deleted_at` टाइमस्टैम्प
- रिकॉर्ड रीस्टोर करने या हमेशा के लिए परमानेंटली पर्ज करने के लिए एक समर्पित Trash इंटरफ़ेस

**पूरा चलने योग्य कोड देखें:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete)।

## मॉडल {#the-model}

जिस टेबल को आप सुरक्षित रखना चाहते हैं, उसमें एक nullable टाइमस्टैम्प कॉलम जोड़ें। `NULL` वैल्यू का मतलब है एक्टिव रिकॉर्ड, जबकि भरी हुई टाइमस्टैम्प का मतलब है डिलीट किया हुआ रिकॉर्ड:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

इस तरीक़े में न अलग ट्रैश टेबल की ज़रूरत है, न किसी एक्सटर्नल सॉफ़्ट-डिलीट मिक्सिन लाइब्रेरी की। एक ही कॉलम पूरी स्टेट मशीन संभाल लेता है।

## एक्टिव व्यू से डिलीट की गई रो छिपाना {#hiding-deleted-rows-from-the-active-view}

`ModelView` क्लास अपनी लिस्ट, काउंट और डिटेल क्वेरी ओवरराइड करने योग्य मेथड से बनाती है। `get_detail_query` डिफ़ॉल्ट रूप से `get_list_query` पर चलता है, इसलिए लिस्ट क्वेरी को फ़िल्टर करने से डिटेल पेज भी फ़िल्टर हो जाता है — सीधे URL खोलने की स्थिति में भी। `get_count_query` स्वतंत्र है और उसे अलग से फ़िल्टर करना पड़ता है। इन क्वेरी को सिर्फ़ `deleted_at IS NULL` वाले रिकॉर्ड शामिल करने के लिए फ़िल्टर करके, आप सॉफ़्ट-डिलीट की गई रो को लिस्ट पेज, पेजिनेशन काउंट और सीधे डिटेल लिंक से प्रभावी ढंग से छिपा सकते हैं:

```python title="app.py" hl_lines="7-8 10-11"
class PostView(ModelView):
    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at", "created_at"]
    exclude_fields_from_edit = ["deleted_at", "created_at"]
    fields_default_sort = [("created_at", True)]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(Post.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(Post.deleted_at.is_(None))
```

`deleted_at` को क्रिएट और एडिट फ़ॉर्म से भी बाहर रखना होगा। ऑपरेटर को यह फ़ील्ड कभी मैन्युअली सेट नहीं करना चाहिए; इसे सिर्फ़ प्रोग्रामेटिक रूप से, `delete()` मेथड और रीस्टोर एक्शन से बदला जाना चाहिए।

!!! warning
`get_count_query` छूट जाए तो डेटा विज़िबिलिटी लीक हो जाता है: पेजिनेशन और सर्च-रिज़ल्ट के टोटल में डिलीट की गई रो शामिल हो जाएँगी, भले ही वे लिस्ट में रेंडर न हों। यहाँ `get_detail_query` को अलग से ओवरराइड करने की ज़रूरत नहीं, क्योंकि वह डिफ़ॉल्ट रूप से `get_list_query` पर चलता है और वही फ़िल्टर अपने आप विरासत में पाता है। लेकिन अगर आप किसी व्यू को कस्टम `get_detail_query` देते हैं, तो वह `get_list_query` से इनहेरिट करना बंद कर देता है और `deleted_at` को ख़ुद फ़िल्टर करना ज़रूरी हो जाता है।

## डिलीट को नए सिरे से परिभाषित करना {#redefining-delete}

बिल्ट-इन बैच डिलीट एक्शन और रो-लेवल डिलीट बटन, दोनों ही `ModelView.delete()` को कॉल करते हैं। इस मेथड को ओवरराइड करने से डिलीशन का व्यवहार सभी एंट्री पॉइंट पर ग्लोबली फिर से तय हो जाता है — कोई अतिरिक्त कॉन्फ़िगरेशन किए बिना:

```python title="app.py" hl_lines="6-7 11"
async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()
    for obj in objs:
        await self._emit_after_delete(request, obj.id, obj)
    return len(objs)
```

`_emit_before_delete` और `_emit_after_delete` कॉल पक्का करते हैं कि [इवेंट बस](../../advanced/events.md) ठीक उसी तरह चले जिस तरह हार्ड डिलीट में चलती। नतीजतन, किसी `AdminEvent.AFTER_DELETE` सबस्क्राइबर (जैसे ऑडिट लॉग या वेबहुक) को यह जानने की ज़रूरत नहीं रहती कि डिलीट सॉफ़्ट थी। डेटाबेस रो लेवल पर असर बदल जाता है, लेकिन लाइफ़साइकिल इवेंट एक जैसे बने रहते हैं।

### AFTER_DELETE_COMMITTED को अलग वायरिंग चाहिए {#after_delete_committed-needs-its-own-wire}

`BEFORE_DELETE` और `AFTER_DELETE` इवेंट पूरी लाइफ़साइकिल नहीं दर्शाते। बेस SQLAlchemy `ModelView.delete()` मेथड एक `on_commit` कॉलबैक भी रजिस्टर करता है। ट्रांज़ेक्शन सफलतापूर्वक कमिट होते ही यह कॉलबैक `AFTER_DELETE_COMMITTED` इवेंट चलाता है, जिससे सबस्क्राइबर सुरक्षित रूप से मान सकते हैं कि रो स्थायी रूप से हट चुकी है।

चूँकि `PostView` उदाहरण `delete()` को पूरी तरह ओवरराइड कर देता है, डिफ़ॉल्ट `on_commit` रजिस्ट्रेशन बाईपास हो जाता है। नतीजा यह कि सॉफ़्ट-डिलीट वाले व्यू पर `AdminEvent.AFTER_DELETE_COMMITTED` सुनने वाला हैंडलर चुपचाप चलना बंद कर देगा।

यह फ़ंक्शनैलिटी वापस लाने के लिए आपको वही कॉलबैक मैन्युअली रजिस्टर करना होगा जिसका इस्तेमाल बेस इम्प्लीमेंटेशन करता है:

```python title="app.py" hl_lines="16-17 20 22"
from collections.abc import Callable

from starlette_admin.helpers import on_commit


async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()

    def _make_after_delete_committed(obj: Post, pk: Any) -> Callable[[], Any]:
        return lambda: self._emit_after_delete_committed(request, pk, obj)

    for obj in objs:
        pk = obj.id
        await self._emit_after_delete(request, pk, obj)
        on_commit(request, _make_after_delete_committed(obj, pk))
    return len(objs)
```

`_make_after_delete_committed` हेल्पर फ़ंक्शन `obj` और `pk` को साधारण पैरामीटर की तरह लेता है। इसे हर रो के लिए एक बार, उसी रो की वैल्यू के साथ कॉल किया जाता है। यह स्ट्रक्चर बेहद ज़रूरी है। अगर आप लैम्ब्डा सीधे लूप के अंदर बनाते, तो वह उस ख़ास इटरेशन की वैल्यू के बजाय लूप वेरिएबल ख़ुद को कैप्चर कर लेता। नतीजतन, लूप पूरा होने के बाद हर कॉलबैक `obj` और `pk` की फ़ाइनल वैल्यू के साथ चलता। उन्हें बाहरी फ़ंक्शन के आर्ग्युमेंट की तरह पास करने से कॉल के समय की उनकी सही स्थिति कैप्चर हो जाती है।

सॉफ़्ट डिलीट का एक फ़ायदा यहीं काम आता है। हार्ड डिलीट में कमिटेड कॉलबैक शेड्यूल करने से पहले ऑब्जेक्ट को डिटैच करना पड़ता है (`session.expunge`)। हार्ड-डिलीट की गई रो कमिट के समय तक चली जाती है, इसलिए किसी अनलोडेड एट्रिब्यूट को एक्सेस करने पर `ObjectDeletedError` आता है। चूँकि सॉफ़्ट डिलीट रो कभी हटाती नहीं, ऑब्जेक्ट अटैच्ड रहता है और कॉलबैक के अंदर सभी एट्रिब्यूट सुरक्षित रूप से पढ़े जा सकते हैं।

लेकिन `on_commit` का मुख्य नियम यहाँ भी लागू रहता है: कॉलबैक को `request.state.session` का इस्तेमाल करके डेटाबेस में कुछ लिखना नहीं चाहिए। वह सेशन पहले ही पूरा हो चुका होता है। उस सेशन में फ्लश की गई कोई भी चीज़ नया ट्रांज़ेक्शन शुरू करती है, जो सेशन बंद होने पर ख़ारिज हो जाता है।

## उसी टेबल के लिए दूसरा व्यू {#a-second-view-for-the-same-table}

`TrashView` उसी `Post` मॉडल को टारगेट करता है लेकिन एक अलग `key` के तहत रजिस्टर होता है। यह कॉन्फ़िगरेशन `starlette-admin` को उसे एक अलग रिसोर्स की तरह ट्रीट करने का निर्देश देती है, जिसका अपना अलग URL और मेन्यू एंट्री है:

```python title="app.py" hl_lines="8 11"
class TrashView(ModelView):
    menu_label = "Trash"
    icon = "fa fa-trash"
    fields_default_sort = [("deleted_at", True)]
    actions = ["restore", "delete"]

    def get_list_query(self, request: Request):
        return select(Post).where(Post.deleted_at.isnot(None))

    def get_count_query(self, request: Request):
        return select(func.count()).select_from(Post).where(Post.deleted_at.isnot(None))

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False
```

ये क्वेरी `PostView` की क्वेरी का सीधा उलटा हैं — `IS NULL` की जगह `IS NOT NULL` पर फ़िल्टर करती हैं। `get_detail_query` यहाँ भी डिफ़ॉल्ट रूप से `get_list_query` पर चलता है, इसलिए ट्रैश किए गए रिकॉर्ड अपने डिटेल पेज पर बिना अलग ओवरराइड के ठीक से खुलते हैं। `can_create` और `can_edit` मेथड `False` लौटाते हैं, क्योंकि ऑपरेटर को ट्रैश के भीतर सीधे रिकॉर्ड बनाने या एडिट करने की अनुमति कभी नहीं होनी चाहिए। रिकॉर्ड ट्रैश में सिर्फ़ `PostView.delete()` के ज़रिए आ सकते हैं और रीस्टोर एक्शन या परमानेंट पर्ज से बाहर निकल सकते हैं।

## रीस्टोर, और असली डिलीट की ज़रूरत {#restoring-and-the-case-for-a-real-delete}

`TrashView` अपनी `actions` लिस्ट में बिल्ट-इन `delete` एक्शन को रखे रहता है और उसे ओवरराइड नहीं करता। ट्रैश व्यू के भीतर `delete` चलाने पर एक मानक SQL `DELETE` होता है। यही परमानेंट पर्ज है। एक बार रो ट्रैश से निकल गई, तो वह पूरी तरह समाप्त।

किसी रिकॉर्ड को रीस्टोर करने के लिए एक छोटे [कस्टम एक्शन](../../user-guide/actions.md) की ज़रूरत होती है जो `deleted_at` टाइमस्टैम्प साफ़ कर दे:

```python title="app.py" hl_lines="12"
@action(
    name="restore",
    text="Restore",
    confirmation="Restore the selected posts?",
    submit_btn_text="Yes, restore",
    submit_btn_class="btn btn-success",
)
async def restore_action(self, request: Request, pks: list[Any]) -> None:
    session: Session = request.state.session
    objs = await self.find_by_pks(request, pks)
    for obj in objs:
        obj.deleted_at = None
        session.add(obj)
    session.flush()
    count = len(objs)
    flash(request, f"{count} post{'s' if count != 1 else ''} restored.", "success")
```

`deleted_at = None` सेट करते ही रो अगली रिक्वेस्ट पर एक्टिव `PostView` लिस्ट में वापस आ जाती है, क्योंकि प्राइमरी व्यू सिर्फ़ `NULL` वैल्यू पर क्वेरी करता है।

## दोनों व्यू को उसी टेबल से जोड़ना {#wiring-both-views-to-the-same-table}

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

यह कॉन्फ़िगरेशन एक ही डेटाबेस टेबल के लिए दो अलग एडमिनिस्ट्रेटिव व्यू क़ायम करता है। एक ही कॉलम तय करता है कि कोई ख़ास रो कौन सा व्यू दिखाएगा।

## यह पैटर्न कहाँ टूटता है {#where-this-pattern-breaks-down}

- **यूनीक कंस्ट्रेंट:** `slug` जैसे किसी फ़ील्ड पर `UNIQUE` कंस्ट्रेंट ऑपरेटर को वही slug दोबारा इस्तेमाल करके नई एक्टिव पोस्ट बनाने से रोकता है, जब तक सॉफ़्ट-डिलीट किया हुआ वर्ज़न ट्रैश में पड़ा है। इसे हल करने के लिए या तो partial index की मदद से `deleted_at IS NOT NULL` वाली रो को यूनीक इंडेक्स से बाहर रखें (अगर आपका डेटाबेस इंजन सपोर्ट करता है), या `deleted_at` कॉलम को यूनीक कंस्ट्रेंट में ही शामिल कर लें।
- **फ़ॉरेन की:** सॉफ़्ट-डिलीट किया हुआ `Post` दूसरी टेबल के फ़ॉरेन की रिलेशनशिप के लिए एक वैध रो बना रहता है। चाइल्ड रिकॉर्ड उसी से जुड़े रहेंगे। यह अक्सर मनचाहा व्यवहार होता है, लेकिन सॉफ़्ट डिलीट को संबंधित रो तक कैस्केड कराने के लिए साफ़-साफ़ कस्टम लॉजिक लिखना पड़ता है। डेटाबेस हार्ड डिलीट के `ON DELETE CASCADE` की तरह यह अपने आप नहीं संभालेगा।
- **क्वेरी अनुशासन:** `Post` मॉडल को टारगेट करने वाली हर नई डेटाबेस क्वेरी में `deleted_at IS NULL` फ़िल्टर साफ़ तौर पर शामिल करना होगा। अगर कोई रॉ क्वेरी, एक्सपोर्ट जॉब, या कोई दूसरा एडमिन व्यू यह फ़िल्टर छोड़ दे, तो डिलीट किया हुआ डेटा एक्टिव वर्कफ़्लो में रिसाव हो जाएगा।
- **डेटाबेस का बढ़ना:** सॉफ़्ट-डिलीट की गई रो टेबल और इंडेक्स की जगह खाती रहती हैं। अगर आपकी ऐप्लिकेशन ज़्यादातर सॉफ़्ट-डिलीट रो को रीस्टोर करने की बजाय पर्ज करती है, तो एक शेड्यूल्ड बैकग्राउंड जॉब बनाने पर विचार करें। यह जॉब एक तय रिटेंशन अवधि से पुराने रिकॉर्ड को हार्ड-डिलीट करके डेटाबेस के बेलगाम बढ़ने से रोक सकती है।

## अन्य बैकएंड तक विस्तार {#extending-to-other-backends}

इस पैटर्न के मूल सिद्धांत सिर्फ़ SQLAlchemy तक सीमित नहीं हैं। आप यह तरीक़ा किसी भी बैकएंड पर अपना सकते हैं जो लिस्ट, काउंट और डिटेल क्वेरी के साथ-साथ `delete()` मेथड को ओवरराइड करने देता है। उदाहरण के लिए, अगर आप Beanie, MongoEngine, या Tortoise ORM इस्तेमाल कर रहे हैं, तो समतुल्य ओवरराइड `deleted_at` फ़ील्ड पर बिल्कुल उसी तरह क्वेरी फ़िल्टर करेंगे। क्वेरी सिंटैक्स बदल जाता है, लेकिन आर्किटेक्चरल पैटर्न एक जैसा रहता है।

---

## आगे क्या {#whats-next}

- **[इवेंट्स](../../advanced/events.md):** समझें कि `_emit_before_delete` और `_emit_after_delete` व्यू के बाहर एक्सटर्नल सबस्क्राइबर से कैसे जुड़ते हैं।
- **[एक्शन](../../user-guide/actions.md):** `restore_action` के पीछे के डेकोरेटर को जानें, जिसमें कन्फ़र्मेशन डायलॉग और फ़्लैश-मैसेज हेल्पर लागू करने का तरीक़ा शामिल है।
- **[व्यू](../../user-guide/views.md):** `ModelView` में उपलब्ध क्वेरी और परमिशन हुक का पूरा सेट देखें।
