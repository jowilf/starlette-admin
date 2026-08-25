---
title: Django Admin से आ रहे हैं
description: Django Admin की concepts को starlette-admin के समकक्षों से मैप करने वाली
  विस्तृत migration guide, declarative एडमिन इंटरफ़ेस बनाने के लिए।
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Django Admin से आ रहे हैं {#coming-from-django-admin}

अगर आप Django Admin जानते हैं, तो starlette-admin आपको जाना-पहचाना लगेगा। दोनों declarative, प्रति-मॉडल कॉन्फ़िगरेशन से एडमिन इंटरफ़ेस जनरेट करते हैं, और दोनों इनलाइन एडिटिंग, बैच एक्शन और per-request अनुमतियाँ सपोर्ट करते हैं।

फ़र्क़ संरचनात्मक हैं। starlette-admin को Django की ज़रूरत नहीं है और वह किसी भी ASGI ऐप्लिकेशन पर चलता है, कई ORMs के साथ काम करता है, और इनबिल्ट user model थोपने के बजाय आपको अपना प्रमाणीकरण प्लग करने देता है।

यह guide हर प्रमुख `ModelAdmin` concept को उसके starlette-admin समकक्ष से मैप करती है, side-by-side कोड के साथ।

## मानसिक मॉडल {#mental-model}

| Django Admin concept | starlette-admin समकक्ष |
| --- | --- |
| `AdminSite` | आपके ऐप्लिकेशन पर माउंट किया गया [`Admin`](../api/admin.md) इंस्टेंस |
| `ModelAdmin` | [`ModelView`](../user-guide/views.md) subclass |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `urlpatterns` में `admin.site.urls` | `admin.mount_to(app)` |
| Django ORM | `starlette_admin.contrib.*` के ज़रिए SQLAlchemy, SQLModel, MongoEngine, Beanie या Tortoise ORM |
| model पर `__str__` | `__admin_repr__(self, request)`, जो async और request-aware है |
| model fields से inferred form fields | backend converter द्वारा infer किए गए [Fields](../user-guide/fields.md), प्रति फ़ील्ड अनुकूलन योग्य |

## मॉडल रजिस्टर करना {#registering-a-model}

=== "Django Admin"

    ```python
    from django.contrib import admin
    from .models import Post


    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import Admin, ModelView


    class PostView(ModelView):
        fields = ["id", "title", "content", "published", "created_at"]
        exclude_fields_from_list = ["content"]
        searchable_fields = ["title", "content"]


    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)  # app is your FastAPI or Starlette instance
    ```

दो संरचनात्मक फ़र्क़ साफ़ दिखते हैं:

1. **एक फ़ील्ड लिस्ट हर पेज को सँभालती है।** `fields` एकमात्र source of truth है। फिर प्रति-पेज variations के लिए आप [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create`, और `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) उपयोग करते हैं।
2. **`Admin` इंस्टेंस के पास database engine होता है।** आप हर view को session पास नहीं करते।

## लिस्ट पेज के विकल्प {#list-page-options}

| Django Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `list_display` | `fields` में से [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) घटाकर | एक ही फ़ील्ड लिस्ट हर पेज को सँभालती है। |
| callable या `@admin.display` वाला `list_display` | [`ComputedField`](../user-guide/fields.md#computedfield), या किसी भी फ़ील्ड पर `getter=` | उदाहरण के लिए, `ComputedField("full_name", getter=lambda request, obj: ...)`. date या image field जैसे typed फ़ील्ड पर `getter=` उपयोग करें ताकि उस type की rendering बनी रहे। |
| डिस्प्ले के लिए real column को reformat करना | फ़ील्ड पर [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | एक `dict[RequestAction, callable]`, इसलिए list, detail और export अलग-अलग format कर सकते हैं। Django को sorting बनाए रखने के लिए callable के साथ `admin_order_field` चाहिए; यहाँ कॉलम sortable ही रहता है। |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | फ़ुल-टेक्स्ट सर्च और filter builder दोनों को power देता है। |
| `list_filter` | प्रति-फ़ील्ड `filters=` के साथ संयुक्त `searchable_fields` | fixed sidebar की जगह nested `AND`/`OR` ग्रुप वाला visual builder मिलता है। [Filters](../user-guide/filters.md) देखें। |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | उदाहरण के लिए, `fields_default_sort = [("created_at", True)]` descending order में sort करता है। |
| `admin_order_field` / sortability | [`sortable_fields`](../user-guide/views.md#search-and-sort) | हर फ़ील्ड डिफ़ॉल्ट रूप से sortable होता है। |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | उपयोगकर्ता किसी सेल को चुनकर वहीं edit कर सकते हैं। |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | pagination limits नियंत्रित करता है। |
| `date_hierarchy` | Date filters, जैसे `between` और `in the past` | कोई dedicated drill-down bar नहीं है; filter builder यह case cover कर लेता है। |
| `empty_value_display` | कोई `formatter=` entry, या `null_template` | Formatters को `None` values मिलती हैं, इसलिए वे placeholder बदल सकते हैं। `null_template` rendered markup को ही बदल देता है। |

## फ़ॉर्म {#forms}

| Django Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | फ़ॉर्म fields की visibility नियंत्रित करता है। |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | `FieldsetWidget`, `TabsWidget`, `GridWidget` और `RowWidget` से आज़ादी से compose करें। |
| `readonly_fields` | फ़ील्ड पर `read_only=True` | फ़ील्ड को create और edit views से exclude भी कर सकते हैं। |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | वही live slugification behavior। |
| `autocomplete_fields`, `raw_id_fields` | [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) का डिफ़ॉल्ट behavior | Relation widgets शुरू से server-side search वाले Select2 inputs होते हैं। |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Searchable multi-select component की तरह render होता है। |
| `formfield_overrides` | `fields` लिस्ट में explicit entries | Auto-detect किए गए field को सीधे replace करें: `fields = ["id", TextAreaField("bio")]` |
| कस्टम form validation | फ़ील्ड पर `validators=`, या hooks में `FormValidationError` | [Validators](../api/validators.md) देखें। |
| Form field `to_python()` / custom coercion | फ़ील्ड पर [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | प्रत्येक `RequestAction` के लिए field की डिफ़ॉल्ट form या import parsing replace करता है। |
| Model form help text | `help_text=` | किसी भी field definition पर उपलब्ध। |

### Fieldsets उदाहरण {#fieldsets-example}

=== "Django Admin"

    ```python
    class PostAdmin(admin.ModelAdmin):
        fieldsets = [
            ("Content", {"fields": ["title", "body"]}),
            ("Publication", {"fields": ["published", "created_at"]}),
        ]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import FieldsetWidget


    class PostView(ModelView):
        fields = ["id", "title", "body", "published", "created_at"]
        form_layout = [
            FieldsetWidget(legend="Content", children=["title", "body"]),
            FieldsetWidget(legend="Publication", children=["published", "created_at"]),
        ]
    ```

`form_layout` fieldsets से भी आगे जाता है: आप tabs, responsive grids और nested layouts बना सकते हैं। [Form Layout](../advanced/form-layout.md) देखें।

## Inlines

=== "Django Admin"

    ```python
    class CommentInline(admin.TabularInline):
        model = Comment
        extra = 1


    class ArticleAdmin(admin.ModelAdmin):
        inlines = [CommentInline]
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

starlette-admin foreign key तब detect कर लेता है जब वह unambiguous हो, और composite foreign keys सपोर्ट करता है। Advanced configurations के लिए [Inline Forms](../user-guide/inline-forms.md) देखें।

## एक्शन {#actions}

=== "Django Admin"

    ```python
    @admin.action(description="Mark selected articles as published")
    def make_published(modeladmin, request, queryset):
        queryset.update(published=True)


    class ArticleAdmin(admin.ModelAdmin):
        actions = [make_published]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class ArticleView(ModelView):
        actions = ["make_published", "delete"]

        @action(
            name="make_published",
            text="Mark selected articles as published",
            confirmation="Publish the selected articles?",
        )
        async def make_published(
            self, request: Request, selection: ActionSelection
        ) -> None:
            for article in await selection.rows():
                article.published = True
            flash(request, "Articles published")
    ```

जहाँ Django Admin `QuerySet` पास करता है, वहीं starlette-admin handler को एक [`ActionSelection`](../user-guide/actions.md) object मिलता है। वह rows, primary keys और active filters lazily resolve करता है, और जब user सभी matching records select करता है तब भी इसी तरह व्यवहार करता है।

एक्शन confirmation dialog के अंदर कस्टम HTML फ़ॉर्म भी render कर सकते हैं, जो Django Admin में intermediate page बनाने जितना काम है। प्रति-पंक्ति operations के लिए [`@row_action` और `@link_row_action`](../user-guide/actions.md#row-actions) उपयोग करें, जिनका Django Admin में कोई समकक्ष नहीं है।

## अनुमतियाँ और प्रमाणीकरण {#permissions-and-authentication}

Django Admin काम `django.contrib.auth` को सौंप देता है। starlette-admin इस समस्या को दो हिस्सों में बाँटता है: [`AuthProvider`](../user-guide/auth.md) 'यह user कौन है' का जवाब देता है, और [per-view methods](../user-guide/views.md#security-and-authorization) 'वह क्या कर सकता है' का।

| Django Admin | starlette-admin |
| --- | --- |
| `django.contrib.auth` login | `AuthProvider` (इनबिल्ट sign-in page) या `OAuthProvider` (OIDC redirect flow) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | view पर `is_accessible(request)` |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| प्रति user `get_readonly_fields` | `can_access_field(request, field)` |
| कोई समकक्ष नहीं | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

निम्नलिखित view deletion को `admin` role वाले users तक सीमित करता है:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

हर `can_*` method को request मिलती है, इसलिए आपके authorization निर्णय current user, HTTP headers या request पर मौजूद किसी भी चीज़ को पढ़ सकते हैं।

## सेव हुक और signals {#save-hooks-and-signals}

| Django Admin | starlette-admin | नोट्स |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | view पर [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) | Async-native, और model instance के साथ parsed form data मिलता है। |
| `delete_model` | `before_delete` | Deletion से पहले का logic सँभालता है। |
| `post_save` और अन्य signals | [इवेंट](../advanced/events.md) | उदाहरण के लिए, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` सभी views पर broadcast करता है। |
| `LogEntry` परिवर्तन इतिहास | Event system से ख़ुद बनाइए | अपनी audit table भरने के लिए `AFTER_CREATE`, `AFTER_EDIT` और `AFTER_DELETE` subscribe करें। |
| `messages.success(request, ...)` | `flash(request, ...)` | [Flash Messages](../user-guide/flash-messages.md) देखें। |

## साइट-व्यापी कॉन्फ़िगरेशन {#site-wide-configuration}

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Template override से कस्टम logo | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | rich dashboard के लिए [widgets](../user-guide/custom-views.md) के साथ `Admin(index_view=...)` |
| `templates/admin/` में template overrides | `Admin(templates_dir="...")`, [Templates](../advanced/templates.md) देखें |
| Multiple `AdminSite` instances | अलग-अलग application paths पर माउंट किए गए multiple `Admin` instances |
| `ModelAdmin.get_queryset` | SQLAlchemy backend के लिए `get_list_query`, `get_count_query` या `get_detail_query` |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, [i18n और Timezones](../user-guide/i18n.md) देखें |

## बदलने से आपको क्या मिलता है {#what-you-gain-by-switching}

* **End-to-end async:** Handlers, lifecycle हुक और widget callbacks — सभी coroutines हो सकते हैं जो आपके existing event loop पर, आपके FastAPI एंडपॉइंट के साथ चलते हैं।
* **Database flexibility:** चाहे आप SQLAlchemy, SQLModel, MongoEngine या Beanie के ज़रिए MongoDB, या Tortoise ORM उपयोग करें, एक ही एडमिन कॉन्फ़िगरेशन लागू होता है।
* **इनबिल्ट एक्सपोर्ट और इंपोर्ट:** CSV, JSON और PDF, साथ ही `tablib` के ज़रिए Excel और अन्य formats। Records सीधे एक्सपोर्ट करें, या preview-first wizard के ज़रिए bulk data इंपोर्ट करें जो row-level सत्यापन लागू करता है और optional primary key upserts सपोर्ट करता है। [Export और Import](../user-guide/export-import.md) देखें।
* **डैशबोर्ड विजेट:** Stat cards, ApexCharts और layout grids मिलकर index pages और custom views बनाते हैं, इसलिए dashboard बनाने के लिए किसी external theme package की ज़रूरत नहीं। [Custom Views और Widgets](../user-guide/custom-views.md) देखें।
* **आधुनिक user interface:** Tabler (Bootstrap 5) आपको डिफ़ॉल्ट रूप से डार्क मोड, column visibility toggles और search highlighting देता है।

## जो आपको ख़ुद लाना होगा {#what-you-must-bring-yourself}

* **प्रमाणीकरण:** कोई bundled user model या permission database नहीं है। अपने ऐप्लिकेशन के existing data store के आधार पर `AuthProvider.authenticate()` implement करें।
* **Audit logging:** starlette-admin कोई `LogEntry` table generate नहीं करता। [event system](../advanced/events.md) को अपनी audit table से जोड़ें।
* **Model-level UI कॉन्फ़िगरेशन:** Model-level `choices`, `verbose_name` और validators जैसी Django सुविधाएँ transfer नहीं होतीं। इन्हें इसकी जगह starlette-admin field पर declare करें, `EnumField`, `label=` और `validators=` के साथ।
