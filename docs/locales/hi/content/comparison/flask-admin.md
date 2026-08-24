---
title: Flask-Admin से आ रहे हैं
description: Flask-Admin से starlette-admin तक सीधा migration guide, जो दिखाता है
  कि अपनी ModelView कॉन्फ़िगरेशन को ASGI ecosystem में कैसे लाएँ।
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Flask-Admin से आ रहे हैं {#coming-from-flask-admin}

starlette-admin की शुरुआत Flask-Admin की concepts को ASGI ecosystem में port करने से हुई थी, इसलिए migration सीधा रहता है। आप फिर भी एक `ModelView` subclass करते हैं, उसे class attributes से कॉन्फ़िगर करते हैं, और एक `Admin` instance पर register करते हैं। ज़्यादातर काम attributes के नाम बदलने और Flask के implicit request context से Starlette के explicit `request` object पर आने का है।

यह guide Flask-Admin API को attribute-दर-attribute उसके starlette-admin समकक्ष से मैप करती है।

## मानसिक मॉडल {#mental-model}

| Flask-Admin concept | starlette-admin समकक्ष |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, फिर `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; engine और database sessions का मालिक `Admin` instance होता है |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee / pymongo backends | Beanie, Tortoise ORM, SQLModel, या [custom backend](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Flask request context (`flask.request`) | हर हुक पर explicit `request: Request` parameter |
| Sync methods | `async` methods; जहाँ callables स्वीकार किए जाते हैं वहाँ sync भी चलता है |

## सेटअप {#setup}

=== "Flask-Admin"

    ```python
    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    admin = Admin(app, name="My Admin", template_mode="bootstrap4")
    admin.add_view(ModelView(Post, db.session))
    ```

=== "starlette-admin"

    ```python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    app = Starlette()  # or FastAPI()
    admin = Admin(engine, title="My Admin", secret_key="change-me")
    admin.add_view(ModelView(Post))
    admin.mount_to(app)
    ```

यहाँ कोई `template_mode` switch नहीं है। UI [Tabler](https://tabler.io) (Bootstrap 5) उपयोग करता है और डार्क मोड शामिल है। दिखावट बदलने के लिए कस्टम [`BaseTheme`](../advanced/custom-themes.md) लिखें या [templates override करें](../advanced/templates.md)।

## लिस्ट पेज की attributes {#list-page-attributes}

| Flask-Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `column_list` | `fields` | Detail और form pages भी इसी से चलते हैं। प्रति-पेज variations के लिए `exclude_fields_from_*` attributes उपयोग करें। |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | उदाहरण के लिए, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Field definition पर लागू होता है। |
| `column_formatters` | फ़ील्ड पर [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | उदाहरण के लिए, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / export formatters | `RequestAction` के अनुसार keyed वही `formatter=` dict | एक mapping list, detail और export formatting — तीनों को cover करती है। जिन actions की entry नहीं होती, वे raw value रखते हैं। |
| `column_type_formatters` | प्रति-फ़ील्ड `formatter=`, या कस्टम field subclass | कोई per-type registry नहीं है। Formatter हर फ़ील्ड से attach करें, या [field को subclass करें](../advanced/custom-fields.md) और reuse करें। |
| `column_list` में model properties या callables | किसी भी फ़ील्ड पर [`ComputedField`](../user-guide/fields.md#computedfield) या `getter=` | Subclass के बिना virtual columns जोड़ता है, या किसी existing field की value lookup redirect करता है। |
| कस्टम WTForms fields (value coercion) | फ़ील्ड पर [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | प्रत्येक `RequestAction` के लिए field की डिफ़ॉल्ट form या import parsing replace करता है। |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | प्रति-फ़ील्ड `filters=` के साथ संयुक्त `searchable_fields` | Flat filter list की जगह nested `AND`/`OR` ग्रुप सपोर्ट करने वाला [visual builder](../user-guide/filters.md) आता है। |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | उदाहरण के लिए, `[("created_at", True)]` descending order में sort करता है। |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | उपयोगकर्ता सेल चुनकर वहीं edit कर सकते हैं। |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | डिफ़ॉल्ट `[10, 25, 50, 100]`। Users इन्हीं options में से चुनते हैं। |
| `column_display_pk` | `fields` में primary key शामिल करें |  |
| `column_details_list` | `exclude_fields_from_detail` घटाकर `fields` | Detail page इनबिल्ट है। कोई `can_view_details` opt-in नहीं। |

## फ़ॉर्म attributes {#form-attributes}

| Flask-Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `form_columns` | `exclude_fields_from_create` और `exclude_fields_from_edit` घटाकर `fields` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | हर फ़ॉर्म के लिए अलग visibility controls। |
| `form_overrides` | `fields` में explicit field instances | उदाहरण के लिए, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | फ़ील्ड के constructor arguments | उदाहरण के लिए, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | उदाहरण के लिए, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | `fields` में extra entries | Database column से backed न होने वाला कोई भी फ़ील्ड support करता है, जैसे [`ComputedField`](../user-guide/fields.md#computedfield)। |
| `form_widget_args` | Field attributes | `read_only`, `disabled` या `placeholder` सीधे फ़ील्ड पर set करें। |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Flat rules की जगह fieldsets, tabs और responsive grids। |
| `create_modal` / `edit_modal` | उपलब्ध नहीं | Create और edit views पूरे pages की तरह render होते हैं। |
| `on_form_prefill` | `before_edit` हुक |  |

## एक्सपोर्ट और इंपोर्ट {#export-and-import}

=== "Flask-Admin"

    ```python
    class PostView(ModelView):
        can_export = True
        export_types = ["csv", "xlsx"]
        export_max_rows = 10000
    ```

=== "starlette-admin"

    ```python
    class PostView(ModelView):
        exporters = ["csv", "xlsx", "pdf"]
        importers = ["csv", "xlsx"]
        exclude_fields_from_export = ["internal_notes"]
    ```

CSV और JSON एक्सपोर्ट डिफ़ॉल्ट रूप से चालू रहते हैं। Row caps अपने-आप लागू होते हैं, और spreadsheet formula escaping exporter की opt-in setting है। इंपोर्ट, जो Flask-Admin देता ही नहीं है, में प्रति-पंक्ति सत्यापन वाला preview step और primary key से existing records के optional अपडेट शामिल हैं। [Export और Import](../user-guide/export-import.md) देखें।

## एक्शन {#actions}

=== "Flask-Admin"

    ```python
    from flask_admin.actions import action


    class PostView(ModelView):
        @action("publish", "Publish", "Publish selected posts?")
        def action_publish(self, ids):
            query = Post.query.filter(Post.id.in_(ids))
            for post in query.all():
                post.published = True
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class PostView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Publish",
            confirmation="Publish selected posts?",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            for post in await selection.rows():
                post.published = True
            flash(request, "Posts published")
    ```

Handler को raw IDs की जगह एक [`ActionSelection`](../user-guide/actions.md) object मिलता है। वह rows lazily resolve करता है, active filters expose करता है, और जब user pages के पार सभी matching records select करता है तब भी इसी तरह काम करता है। एक्शन confirmation dialog के अंदर कस्टम HTML फ़ॉर्म भी render कर सकते हैं। प्रति-पंक्ति operations के लिए [`@row_action` और `@link_row_action`](../user-guide/actions.md#row-actions) custom column formatters की जगह लेते हैं।

## अनुमतियाँ और access control {#permissions-and-access-control}

Flask-Admin के `can_*` class flags starlette-admin में [per-request methods](../user-guide/views.md#security-and-authorization) बन जाते हैं, इसलिए authorization निर्णय signed-in user पर निर्भर हो सकते हैं।

| Flask-Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | View को menu से छिपाता है और direct access रोकता है। |
| `inaccessible_callback()` | Authentication flow सँभालता है | Unauthenticated requests sign-in page पर redirect हो जाते हैं। |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` और `can_delete` भी इसी pattern पर चलते हैं। |
| `can_view_details` | `can_view_detail(request)` | Detail page डिफ़ॉल्ट रूप से मौजूद होता है। |
| `can_export` | `can_export(request)`, साथ में `can_import(request)` |  |
| कोई समकक्ष नहीं | `can_access_field(request, field)` | User के अनुसार field-level visibility नियंत्रित करता है। |
| कोई समकक्ष नहीं | `is_action_allowed(request, name)` | प्रति-एक्शन authorization देता है। |

Flask-Admin में Flask-Login आप ख़ुद integrate करते हैं। starlette-admin ready-made sign-in page वाला एक [`AuthProvider`](../user-guide/auth.md) देता है, और आप `login`, `logout` और `authenticate` methods अपने user store के आधार पर implement करते हैं। `OAuthProvider` OIDC redirect flows cover करता है। Signed-in user हर जगह `request.state.admin_user` के रूप में उपलब्ध रहता है।

## Model lifecycle हुक {#model-lifecycle-hooks}

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, SQLAlchemy backend के लिए specific |
| `handle_view_exception` | `FormValidationError` या `ActionFailed` raise करें |

Per-view हुक से आगे, [event system](../advanced/events.md) किसी एक handler को हर view observe करने देता है। Flask-Admin का कोई समकक्ष नहीं है।

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## कस्टम views और index page {#custom-views-and-the-index-page}

| Flask-Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Raw templates लिखे बिना [widgets](../user-guide/custom-views.md) से pages compose करें। |
| कस्टम template rendering | `CustomView` subclass | Routes और responses पर पूरा नियंत्रण देता है। |
| `AdminIndexView` | `Admin(index_view=...)` | `StatWidget`, `ChartWidget`, `TableWidget` और layout widgets से dashboards बनाएँ। |
| `MenuLink` | [`Link`](../user-guide/views.md#link) view | उदाहरण के लिए, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Menu में categories | [`DropDown`](../user-guide/views.md#sidebar-organization) view | Views को sidebar में एक साथ group करता है। |
| `FileAdmin` | उपलब्ध नहीं | Attachments [local या S3 storage](../user-guide/file-storage.md) वाले file और image fields सँभालते हैं। Server file browser नहीं है। |

## इनलाइन मॉडल {#inline-models}

=== "Flask-Admin"

    ```python
    class ArticleView(ModelView):
        inline_models = [Comment]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import InlineModelView, ModelView


    class CommentInline(InlineModelView):
        model = Comment
        fields = ["author", "body"]


    class ArticleView(ModelView):
        inlines = [CommentInline]
    ```

Explicit class हर inline model को पूरी `ModelView` कॉन्फ़िगरेशन surface देता है: field selection, सत्यापन और composite foreign key समर्थन। [Inline Forms](../user-guide/inline-forms.md) देखें।

## अंतर्राष्ट्रीयकरण {#internationalization}

Flask-Admin Flask-Babel और उसके आस-पास के Flask environment पर निर्भर करता है। starlette-admin इसकी जगह एक कॉन्फ़िगरेशन object उपयोग करता है:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Timezone-aware datetime rendering भी इसी तरह चलता है, `TimezoneConfig` के ज़रिए। [अंतर्राष्ट्रीयकरण और Timezones](../user-guide/i18n.md) देखें।

## बदलने से आपको क्या मिलता है {#what-you-gain-by-switching}

* **एक async स्टैक.** FastAPI और Starlette पर नेटिव रूप से चलता है, async SQLAlchemy, Beanie और Tortoise ORM के समर्थन सहित। Flask-Admin synchronous है।
* **इनबिल्ट security features.** CSRF सुरक्षा, upload filename sanitization, image content verification और export row limits `Admin` instantiate करते ही चालू हो जाती हैं, और आप exporters पर spreadsheet formula escaping enable कर सकते हैं। [Security](../user-guide/security.md) देखें।
* **डेटा इंपोर्ट.** Preview step कुछ भी लिखे जाने से पहले हर पंक्ति validate करता है। Flask-Admin में import फ़ीचर है ही नहीं।
* **डैशबोर्ड widget system.** Templates हाथ से लिखने की जगह Python में index pages और custom views बनाएँ।
* **आधुनिक design.** सक्रिय रूप से maintained codebase, polished UI, इनबिल्ट डार्क मोड और first-class type hints के साथ।

## जिनसे आपको ढलना होगा {#what-you-must-adapt-to}

* **Explicit request objects.** कोई ambient request context नहीं होता। हर हुक और permission method को parameter के रूप में request मिलती है।
* **Async handlers.** हुक और एक्शन coroutines होते हैं, इसलिए blocking calls इनमें न रखें या वह काम thread में move कर दें।
* **कोई `FileAdmin` नहीं.** अगर आपका workflow server file system browse करने पर टिका है, तो starlette-admin इसे cover नहीं करता।
* **कोई create या edit modal नहीं.** फ़ॉर्म popup modals की जगह पूरे pages की तरह render होते हैं।
