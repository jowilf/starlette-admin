---
title: एक्शन
description: लिस्ट व्यू से सीधे कस्टम पुष्टि और फ़ॉर्म के साथ बैच तथा पंक्ति-स्तरीय
  ऑपरेशन निष्पादित करें।
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# एक्शन {#actions}

एक्शन आपको एडमिन UI से सीधे अपने डेटाबेस रिकॉर्ड के साथ काम करने का तरीका देते हैं, जिससे उपयोगकर्ता बल्क डिलीशन, बल्क अपडेट और ईमेल भेजने जैसे ऑपरेशन चला सकते हैं।

## `ActionSelection` को समझना {#understanding-actionselection}

`ActionSelection` एक्शन API की केंद्रीय वस्तु है। प्राइमरी की (primary keys) की कच्ची सूची के बजाय, आपका हैंडलर एक `ActionSelection` इंस्टेंस प्राप्त करता है।

यह वस्तु lazy तरीके से रिज़ॉल्व होती है और उसी तरह व्यवहार करती है चाहे उपयोगकर्ता पंक्तियाँ एक-एक करके चुना हो या "सभी मेल खाती पंक्तियाँ चुनें" (select all matching) का उपयोग किया हो। यह आपके हैंडलर को लिस्ट पेज के सक्रिय फ़िल्टर भी उपलब्ध कराती है।

### `ActionSelection` API संदर्भ {#actionselection-api-reference}

| मेथड या प्रॉपर्टी         | विवरण                                                                 |
| ------------------------- | --------------------------------------------------------------------- |
| `await selection.rows()`  | लक्षित पंक्तियों को प्राप्त करता है। एक बार फ़ेच होता है, फिर कैश हो जाता है। |
| `await selection.pks()`   | लक्षित पंक्तियों की प्राइमरी की (primary keys) प्राप्त करता है।        |
| `await selection.count()` | एक्शन की लक्षित पंक्तियों की कुल संख्या लौटाता है।                    |
| `selection.is_select_all` | एक बूलियन जो बताता है कि उपयोगकर्ता ने "सभी मेल खाती पंक्तियाँ चुनें" (select all matching) चुना था या नहीं। |
| `selection.filters`       | सक्रिय `FilterGroup`, जो `ListParams.filters` के समान है।             |
| `selection.q`             | सक्रिय फ़ुल-टेक्स्ट खोज शब्द, या खोज निष्क्रिय होने पर `None`।         |

## बैच एक्शन {#batch-actions}

डिफ़ॉल्ट रूप से, उपयोगकर्ता किसी ऑब्जेक्ट को लिस्ट पेज पर चुनकर और उसे अलग से एडिट करके अपडेट करते हैं। एक ही बदलाव कई ऑब्जेक्ट पर एक साथ लागू करने के लिए, एक कस्टम **बैच एक्शन** जोड़ें।

!!! note
    `starlette-admin` डिफ़ॉल्ट रूप से एक `delete` बैच एक्शन जोड़ता है।

अपने `ModelView` में कोई कस्टम बैच एक्शन जोड़ने के लिए, अपने लॉजिक के साथ एक async फ़ंक्शन लिखें और उसे `@action` डेकोरेटर में लपेटें।

!!! important
    बैच एक्शन के नाम एक `ModelView` के भीतर अद्वितीय (unique) होने चाहिए।

### बैच एक्शन उदाहरण {#batch-action-example}

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

```

## ग्लोबल एक्शन {#global-actions}

एक सामान्य बैच एक्शन को सक्रिय सिलेक्शन की ज़रूरत होती है: **With selected** ड्रॉपडाउन तभी दिखता है जब कम से कम एक पंक्ति चुनी गई हो। जब कोई एक्शन पूरे कलेक्शन को लक्षित करता हो, जैसे पूर्ण डेटाबेस सिंक, तो उसे ग्लोबल एक्शन बनाएँ।

`@action` डेकोरेटर में `allow_empty_selection=True` सेट करें। ग्लोबल एक्शन हमेशा दिखने वाले **Actions** ड्रॉपडाउन में रेंडर होते हैं और बिना किसी पंक्ति सिलेक्शन के चलते हैं।

**ग्लोबल एक्शन के लिए हैंडलर का व्यवहार:**

- **खाली सिलेक्शन:** `selection` ऑब्जेक्ट शून्य पंक्तियों पर रिज़ॉल्व हो सकता है।
- **आकस्मिक सिलेक्शन:** अगर उपयोगकर्ता ने ग्लोबल एक्शन ट्रिगर करते समय कुछ पंक्तियाँ चुनी हों, तो हैंडलर को वे पंक्तियाँ फिर भी मिल जाती हैं। जब आपका लॉजिक पूरे कलेक्शन को लक्षित करे, तो `selection` को स्पष्ट रूप से अनदेखा करें।

बाकी हर पैरामीटर (`confirmation`, `form`, `custom_response`, और `is_action_allowed`) ठीक वैसे ही काम करता है जैसे सामान्य बैच एक्शन में करता है।

**समर्पित टूलबार बटन:** किसी ग्लोबल एक्शन को **Actions** ड्रॉपडाउन की एंट्री के बजाय उसके अलग टूलबार बटन के रूप में रेंडर करने के लिए `dedicated_button=True` जोड़ें। बिल्ट-इन एक्सपोर्ट एक्शन इसी विकल्प का उपयोग करता है। `dedicated_button=True` को केवल-सिलेक्शन वाले एक्शन के साथ मिलाने पर स्टार्टअप पर त्रुटि आती है।

### ग्लोबल एक्शन उदाहरण {#global-action-example}

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

```

### "सभी मेल खाती पंक्तियाँ चुनें" सुविधा {#the-select-all-matching-feature}

जब उपयोगकर्ता मौजूदा पेज की हर पंक्ति चुन ले और फ़िल्टर से और अधिक पंक्तियाँ मेल खाती हों, तो UI सभी मेल खाती पंक्तियाँ चुनने का विकल्प देता है।

यह विकल्प प्राइमरी की की सूची के बजाय एक्शन API को `all=1` भेजता है। अपने लॉजिक की शाखा (branch) बनाने के लिए `selection.is_select_all` का उपयोग करें, या `selection.rows()` को दोनों ही स्थितियों में डेटा रिज़ॉल्व करने दें:

```python
    @action(name="archive", text="Archive")
    async def archive_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        if selection.is_select_all:
            await self.bulk_archive_where(request, selection.filters, selection.q)
        else:
            await self.bulk_archive_pks(request, await selection.pks())

```

!!! important "मटेरियलाइज़ेशन सीमाएँ"
    select-all मोड में, `selection.rows()`, `pks()`, और `count()` की सीमा `action_select_all_limit` से तय होती है, जिसका डिफ़ॉल्ट 1000 है। सीमा पार करने पर `ActionFailed` अपवाद (exception) उठता है। ऐसा हैंडलर जो केवल `selection.filters` और `selection.q` पढ़ता है, कुछ भी मटेरियलाइज़ नहीं करता, इसलिए यह सीमा लागू नहीं होती।

## पंक्ति एक्शन {#row-actions}

पंक्ति एक्शन उपयोगकर्ताओं को लिस्ट व्यू से सीधे किसी एक आइटम पर काम करने देते हैं। `starlette-admin` में डिफ़ॉल्ट रूप से तीन पंक्ति एक्शन शामिल हैं: `view`, `edit`, और `delete`।

कोई कस्टम पंक्ति एक्शन जोड़ने के लिए, अपना लॉजिक लिखें और `@row_action` डेकोरेटर लगाएँ। जब एक्शन केवल उपयोगकर्ता को किसी दूसरे URL पर भेजता हो, तो इसके बजाय `@link_row_action` डेकोरेटर का उपयोग करें। यह लिंक को HTML `href` एट्रिब्यूट में एम्बेड कर देता है और एक्शन API को छोड़ देता है।

!!! important
    पंक्ति एक्शन के नाम एक `ModelView` के भीतर अद्वितीय होने चाहिए।

### पंक्ति एक्शन उदाहरण {#row-action-example}

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### पंक्ति एक्शन को प्रतिबंधित करना {#restricting-row-actions}

दो हुक तय करते हैं कि कोई पंक्ति एक्शन उपलब्ध है या नहीं। दोनों डिफ़ॉल्ट रूप से एक्शन की अनुमति देते हैं।

1. **`is_row_action_allowed(request, name)`**: हर एक्शन नाम के लिए एक बार चलता है। इसका उपयोग उन प्रतिबंधों के लिए करें जो पंक्ति पर निर्भर नहीं हैं, जैसे भूमिका-आधारित एक्सेस कंट्रोल।
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: पहली जाँच पास करने वाले एक्शनों के लिए हर पंक्ति पर एक बार चलता है। इसका उपयोग डेटा-आधारित प्रतिबंधों के लिए करें, जैसे पहले से प्रकाशित आर्टिकल पर **Publish** बटन छिपाना।

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView

class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)

```

!!! warning
    उन एक्शन नामों के लिए हमेशा `super()` कॉल करें जिन्हें आपका ओवरराइड हैंडल नहीं करता। ऐसा न करने पर बिल्ट-इन एक्शन की अनुमति जाँचें चुपचाप अक्षम हो जाती हैं।

## पंक्ति एक्शन के लिए UI कॉन्फ़िगरेशन {#ui-configuration-for-row-actions}

### डिस्प्ले टाइप {#display-types}

`row_actions_display_type` पैरामीटर तय करता है कि एक्शन लिस्ट पेज पर कैसे दिखेंगे। डिटेल पेज के एक्शन हमेशा पूरे बटनों के रूप में रेंडर होते हैं।

| डिस्प्ले टाइप  | विवरण                                                                 |
| -------------- | --------------------------------------------------------------------- |
| `ICON_LIST`    | केवल आइकन वाले बटनों की एक क्षैतिज सूची रेंडर करता है।                |
| `DROPDOWN`     | एक्शन को लेबल वाले ड्रॉपडाउन मेन्यू में समूहित करता है।               |
| `KEBAB`        | एक्शन को `⋮` आइकन से खुलने वाले ड्रॉपडाउन मेन्यू में समूहित करता है।  |
| `INLINE_LINKS` | एक्शन लेबल को आइकन के नीचे, मध्य बिंदु (middle dot) से अलग करके रेंडर करता है। |

### कॉलम पोज़िशनिंग {#column-positioning}

डिफ़ॉल्ट रूप से, एक्शन कॉलम आपके डेटा कॉलम से पहले रेंडर होता है। इसे टेबल की दाईं ओर ले जाने के लिए `RowActionsPosition` का उपयोग करें:

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## डायनामिक एक्शन फ़ॉर्म {#dynamic-action-forms}

`@action` और `@row_action` दोनों डेकोरेटर पर `form` पैरामीटर एक callable स्वीकार करता है, जिससे आप HTML को रिक्वेस्ट के समय जनरेट कर सकते हैं।

callable सिंक्रोनस या एसिंक्रोनस हो सकता है, और उसे एक स्ट्रिंग लौटानी चाहिए।

- **`@action` सिग्नेचर**: `(request) -> str`
- **`@row_action` सिग्नेचर**: `(request, obj) -> str`

जब आप फ़ॉर्म इनपुट को किसी पंक्ति के मौजूदा मानों से प्रीफ़िल करना चाहें, तो callable का उपयोग करें।

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]

```

!!! important
    पंक्ति एक्शन का फ़ॉर्म callable लिस्ट पेज पर हर पंक्ति के लिए एक बार चलता है। इसे तेज़ रखें और इसके भीतर डेटाबेस क्वेरी से बचें। आपको जो पंक्ति डेटा चाहिए, वह `obj` पैरामीटर से पहले से उपलब्ध होता है।
