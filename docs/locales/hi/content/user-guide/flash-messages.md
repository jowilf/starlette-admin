---
title: फ़्लैश संदेश
description: starlette-admin में एक्शन पूरे होने के बाद उपयोगकर्ताओं को अस्थायी सफलता,
  चेतावनी, या त्रुटि अलर्ट भेजें।
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# फ़्लैश संदेश {#flash-messages}

फ़्लैश संदेश उपयोगकर्ताओं को कोई एक्शन करने के बाद अस्थायी, एक बार दिखने वाला फ़ीडबैक देते हैं, जैसे "Post created successfully" या "Invalid file type"। एक संदेश एक HTTP रीडायरेक्ट तक टिकता है, और डिस्प्ले होने के बाद एडमिन उसे हटा देता है।

`flash()` वर्तमान रिक्वेस्ट पर एक संदेश को कतार (queue) में डालता है। एडमिन इस संदेश को उपयोगकर्ता के अगले पेज पर रेंडर करता है, फिर कतार साफ़ कर देता है। यह पैटर्न Flask-Admin से लिया गया है।


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash

class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Queue the message for the next page load
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")

```

## संदेश श्रेणियाँ {#message-categories}

हर फ़्लैश संदेश को एक श्रेणी (category) चाहिए। श्रेणी डिफ़ॉल्ट थीम में बैनर का रंग तय करती है, ताकि उपयोगकर्ता गंभीरता को एक नज़र में समझ सकें।

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

`category` आर्ग्युमेंट का डिफ़ॉल्ट `"info"` होता है। यह ठीक-ठीक `success`, `info`, `warning`, या `error` में से एक होना चाहिए। कोई अन्य मान `ValueError` उठाता है।

## बिल्ट-इन CRUD संदेश {#built-in-crud-messages}

सामान्य CRUD ऑपरेशनों के लिए आपको `flash()` कॉल करने की आवश्यकता नहीं है। निम्नलिखित एक्शन पूरे होने पर एडमिन स्वतः एक `success` संदेश दिखाता है:

| एक्शन | डिफ़ॉल्ट संदेश |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "`<repr>` किसे दर्शाता है"
    स्वचालित संदेश `view.repr()` द्वारा परिभाषित पंक्ति प्रतिनिधित्व (row representation) का उपयोग करते हैं, मॉडल के क्लास नाम का नहीं। उदाहरण के लिए, कोई post बनाने पर *"The item 'My First Post' was added successfully"* दिखता है, न कि सामान्य *"Post was added successfully"*।

## कस्टम एक्शन में फ़्लैश संदेशों का उपयोग {#using-flash-messages-in-custom-actions}

कस्टम एक्शन (`@action` और `@row_action`) के हैंडलर डिफ़ॉल्ट रूप से `None` रिटर्न करते हैं। उपयोगकर्ता को फ़ीडबैक देने के लिए, हैंडलर के रिटर्न होने से पहले `flash()` कॉल करें।

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash

class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Notify the user that the custom action succeeded
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **यदि आप `flash()` छोड़ दें:** एक्शन फिर भी चलता है, लेकिन पेज रीडायरेक्ट होने के बाद उपयोगकर्ता को कोई विज़ुअल पुष्टि नहीं मिलती।
* **यदि एक्शन विफल हो जाए:** जब आपका कस्टम एक्शन `ActionFailed` उठाता है, तो एडमिन उस एक्सेप्शन को इंटरसेप्ट करके एक्सेप्शन स्ट्रिंग को एरर बैनर के रूप में दिखाता है। `ActionFailed` ब्रांच में `flash()` कॉल न करें, क्योंकि रिक्वेस्ट रीडायरेक्ट नहीं होती।

## कस्टम टेम्पलेट में संदेश रेंडर करना {#rendering-messages-in-custom-templates}

एडमिन का बेस टेम्पलेट फ़्लैश संदेशों को आपके लिए पॉप और रेंडर कर देता है। आपको उन्हें स्वयं प्राप्त करने की आवश्यकता तभी होती है जब आप कोई पूर्ण [custom view](custom-views.md) बनाते हैं।

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

फ़्लैश कतार को पढ़ना **विध्वंसक (destructive)** है। `get_flashed_messages(request)` का पहला कॉल कतार को पॉप और साफ़ कर देता है। उसी रिक्वेस्ट के दौरान बाद के कॉल एक खाली लिस्ट `[]` रिटर्न करते हैं।

!!! important "संदेश छोटे रखें"
    फ़्लैश संदेश सर्वर सेशन में नहीं, बल्कि `admin_flash` नाम की एक साइन की गई, `httponly` कुकी में रहते हैं। ब्राउज़र कुकी का आकार लगभग 4 KB तक सीमित रखते हैं, इसलिए फ़्लैश संदेशों का उपयोग केवल संक्षिप्त फ़ीडबैक के लिए करें। लंबी स्ट्रिंग और बड़े डेटा पेलोड से बचें। कुकी-आधारित दृष्टिकोण का यह भी मतलब है कि फ़्लैश संदेश `SessionMiddleware` के बिना भी काम करते हैं।

> hooks और कस्टम एक्शन से `flash()` कॉल करने वाले रन करने योग्य ऐप के लिए [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) देखें।

---

## आगे क्या {#whats-next}

* **[एक्शन](actions.md)**: बल्क या row एक्शन से बिज़नेस लॉजिक ट्रिगर करें।
* **[Security](security.md)**: देखें कि `secret_key` फ़्लैश कुकी और CSRF टोकन — दोनों को कैसे सुरक्षित रखता है।
* **[Templates](../advanced/templates.md)**: अपने लेआउट के अंदर फ़्लैश बैनर रेंडर करें।
