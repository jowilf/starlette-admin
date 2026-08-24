---
title: टेम्पलेट
description: starlette-admin में Jinja2 टेम्पलेट को ओवरराइड करके किसी खास व्यू या
  फ़ील्ड की HTML संरचना को पूरी तरह कस्टमाइज़ करें।
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# टेम्पलेट {#templates}

एडमिन का हर पेज एक Jinja2 टेम्पलेट है जिसे आप ओवरराइड कर सकते हैं। बिल्ट-इन टेम्पलेट ट्री को fork किए बिना किसी एक list पेज, किसी फ़ील्ड के table cell, या किसी dashboard widget को बदलें।

## Template loader कैसे काम करता है {#how-the-template-loader-works}

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` एक Jinja2 `ChoiceLoader` बनाता है जो पहले आपकी `templates_dir` को देखता है और उसके बाद बिल्ट-इन `starlette_admin/templates/` package directory को। `my_templates/` के अंतर्गत कोई फ़ाइल उसी relative path पर रखें जिस पर वह `starlette_admin/templates/` के अंदर होती है, और आपकी फ़ाइल बिल्ट-इन फ़ाइल को shadow कर देगी। बाकी सभी टेम्पलेट बिल्ट-इन directory से render होते रहते हैं।

!!! note
    Loader chain `@starlette-admin` key के अंतर्गत एक `PrefixLoader` भी register करती है, जो हमेशा बिल्ट-इन टेम्पलेट पर resolve होता है, चाहे `templates_dir` में उन्हें कुछ भी shadow कर रहा हो। इन तक `@starlette-admin/<name>.html` path format से पहुँचें, prefix पर trailing slash छोड़कर। इसका उपयोग किस लिए है, यह जानने के लिए नीचे [किसी एक पेज का template ओवरराइड करना](#overriding-a-single-page-template) देखें।

## Template directory map

| Path | किसके लिए render होता है |
| --- | --- |
| `base.html` | Outer HTML layout (`<html>`, `<head>`, scripts) |
| `layout.html` | Sidebar और topbar chrome (`base.html` को extend करता है) |
| `index.html` | Dashboard या home पेज |
| `list.html` | मॉडल list पेज (table, filter bar, pagination) |
| `detail.html` | एक record का detail (read-only) view |
| `create.html` | Create form |
| `edit.html` | Edit form |
| `login.html` | Login पेज |
| `error.html` | HTTP error पेज (403, 404, आदि) |
| `actions.html` | Bulk-action modal |
| `row-actions.html` | Per-row action dropdown |
| `inline.html` | Create/edit पेज पर inline formset |
| `inline_detail.html` | Detail पेज पर inline table |
| `inline_row.html` | Inline formset के अंदर एक single row |
| `_filter_bar.html` | List के ऊपर active filter chips की bar |
| `_filter_builder.html` | Filter builder modal |
| `_pagination.html` | Pagination controls |
| `_column_header.html` | Sortable column header cell |
| `_form_footer.html` | Save, Save and continue, या Add another buttons |
| `_form_group.html` | Create/edit form पर किसी एक [form layout](form-layout.md) group का fieldset |
| `_form_group_fields.html` | Form layout group के अंदर render होने वाले field inputs |
| `fields/list/<type>.html` | किसी field type के लिए list column cell |
| `fields/detail/<type>.html` | किसी field type के लिए detail पेज display |
| `fields/form/<type>.html` | किसी field type के लिए form input widget |
| `widgets/<name>.html` | Dashboard widget template |
| `modals/actions.html` | Action confirmation modal |
| `modals/delete.html` | Delete confirmation modal |
| `modals/error.html` | Error modal |
| `modals/import.html` | Import modal |
| `macros/views.html` | पेजों के बीच shared Jinja2 macros |

!!! note
    बिल्ट-इन tree में `modals/loading.html` (एक generic loading-state modal) भी शामिल है, और `fields/list/`, `fields/detail/`, तथा `fields/form/` में कई field-specific टेम्पलेट भी। कोई generic `<type>.html` फ़ाइल override करने से पहले अपने इंस्टॉल किए version के लिए `starlette_admin/templates/` में exact filenames देख लें।

## किसी एक पेज का template ओवरराइड करना {#overriding-a-single-page-template}

```
my_templates/
└── list.html   ← shadows the built-in list.html

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Custom banner above the list.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` वापस आपकी अपनी `my_templates/list.html` पर resolve हो जाएगा, क्योंकि `templates_dir` को पहले check किया जाता है, और वह circular reference infinite recursion error उठाता है। `@starlette-admin/` prefix हमेशा बिल्ट-इन copy की ओर point करता है, इसलिए किसी override के अंदर हर `extends` और `include` को bare filename की जगह इसी का उपयोग करना चाहिए।

## Overridable blocks

हर बिल्ट-इन पेज `layout.html` को extend करता है, जो `base.html` को extend करता है। पेज का बाकी हिस्सा duplicate किए बिना किसी एक fragment को बदलने के लिए पूरी फ़ाइल की जगह केवल एक `{% block %}` को ओवरराइड करें:

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Custom report</a>
{% endblock %}

```

### `base.html`

| Block | Contains |
| --- | --- |
| `favicon` | favicon `<link>` tag |
| `title` | `<title>` tag |
| `head_meta` | `<head>` element के भीतर `<meta>` tags |
| `head_css` | Stylesheet `<link>` tags |
| `head` | `<head>` element के भीतर एक free-form insertion point |
| `body` | पूरी `<body>` content (इसे `layout.html` override करता है) |
| `modal` | Modals के लिए page-level insertion point |
| `script` | Closing `</body>` tag से ठीक पहले स्थित `<script>` tags |
| `tail` | `<body>` के एकदम अंत में, `script` के बाद एक खाली insertion point |

### `layout.html`

| Block | Contains |
| --- | --- |
| `sidebar` | पूरा sidebar `<aside>` element (nav brand, menu, और footer सहित) |
| `brand` | Sidebar के nav brand link के अंदर logo image (या `app_title` fallback) |
| `sidebar_menu` | Sidebar के अंदर views links की सूची |
| `sidebar_footer` | Sidebar का निचला हिस्सा |
| `user_menu_trigger` | User-menu button पर दिखाया गया avatar और username। इसे एक बार define किया जाता है और `self.user_menu_trigger()` के ज़रिए mobile sidebar और desktop navbar दोनों पर reuse किया जाता है, इसलिए इसे override करने से दोनों update हो जाते हैं |
| `user_menu_items` | User menu में स्थित dropdown items |
| `navbar` | Top navigation bar |
| `navbar_extra` | Navbar में user menu के बगल में रखी गई अतिरिक्त content |
| `header` | `content` के ऊपर positioned page header area (title और breadcrumbs सहित) |
| `flash_messages` | Flash messages render करने के लिए designated area |
| `content_before` | `content` के ठीक पहले एक insertion point |
| `content` | मुख्य पेज content (यही वह block है जिसे `list.html`, `detail.html`, आदि populate करते हैं) |
| `content_after` | `content` के ठीक बाद एक insertion point |
| `page_footer` | Page content के नीचे स्थित footer area |

### `list.html`

| Block | Contains |
| --- | --- |
| `header` | Page header (title और breadcrumbs सहित) |
| `page_title` | Header के अंदर `<h1>` heading |
| `breadcrumbs` | Header के अंदर breadcrumb trail |
| `modal` | Delete, action, और import modals |
| `content` | List पेज का पूरा body |
| `list_search` | Search input area |
| `list_toolbar` | Filters, export, import, और create buttons वाली toolbar row |
| `list_toolbar_extra` | Toolbar के एकदम अंत में एक extra insertion point |
| `list_before_table` | Table से पहले एक insertion point |
| `list_table` | `<table>` element स्वयं |
| `list_header` | Checkbox और column header cells वाली `<thead>` row |
| `list_row` | Results table में एक single `<tr>` (एक scoped block; इसे `row`, `row_pk`, और `row_clickable` तक access है) |
| `list_row_actions_before` | Row-actions cell जब `row_actions_position` = `BEFORE_COLUMNS` हो (एक scoped block) |
| `list_row_actions_after` | Row-actions cell जब `row_actions_position` = `AFTER_COLUMNS` हो (एक scoped block) |
| `list_empty` | "No data" placeholder (खाली states के लिए render होने वाला एक scoped block) |
| `list_after_table` | Table के बाद एक insertion point |
| `list_footer` | Pagination और range footer |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `detail.html`

| Block | Contains |
| --- | --- |
| `header` | Page header (title, breadcrumbs, और actions सहित) |
| `page_title` | Header के अंदर `<h1>` heading |
| `breadcrumbs` | Header के अंदर breadcrumb trail |
| `modal` | Delete और action modals |
| `content` | Detail पेज का पूरा body |
| `detail_before` | Detail card से पहले एक insertion point |
| `detail_title` | Detail card के अंदर title area |
| `detail_actions` | Detail card के अंदर action buttons |
| `details_table` | Primary field और value table |
| `detail_after` | Detail card के बाद एक insertion point |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `create.html` / `edit.html`

| Block | Contains |
| --- | --- |
| `header` | Page header (title और breadcrumbs सहित) |
| `page_title` | Header के अंदर `<h1>` heading |
| `breadcrumbs` | Header के अंदर breadcrumb trail |
| `content` | Form पेज का पूरा body |
| `form_before` | Form card से पहले एक insertion point |
| `create_card_header` / `edit_card_header` | Form card के अंदर header area |
| `create_form` / `edit_form` | [Form layout](form-layout.md) groups (हर एक `_form_group.html` के ज़रिए render) और उनके field input elements |
| `create_inlines` / `edit_inlines` | Inline formset area |
| `form_footer` | Save, Save and continue, और Add another buttons |
| `form_after` | Form card के बाद एक insertion point |
| `head_css` | Page-specific stylesheet additions |
| `script` | Page-specific script additions |

### `login.html`

| Block | Contains |
| --- | --- |
| `header` / `sidebar` | खाली छोड़ा गया (login पेज standard application chrome छिपा देता है) |
| `content` | Login पेज का पूरा body |
| `login_logo` | Login form के ऊपर displayed logo |
| `login_title` | Login पेज का title text |
| `login_form_before` | Form fields से पहले एक insertion point |
| `login_fields` | Username और password input fields |
| `login_form_footer` | Fields के बाद लेकिन form के भीतर एक insertion point |
| `login_card_footer` | Login card के ठीक नीचे स्थित एक insertion point |
| `script` | Page-specific script additions |

### `index.html`

| Block | Contains |
| --- | --- |
| `head_css` | Widget-specific stylesheet additions |
| `content` | Dashboard widget grid |
| `script` | Widget-specific script additions |

### `error.html`

| Block | Contains |
| --- | --- |
| `header` / `sidebar` | खाली छोड़ा गया (error पेज standard application chrome छिपा देता है) |
| `content` | Error message और संबंधित actions |
| `error_actions` | Error message के नीचे दिखाए गए action buttons (जैसे "Go back" button) |

!!! tip
    Override के अंदर `{{ super() }}` call करें ताकि बिल्ट-इन block की content बनी रहे और उसे replace करने की बजाय उसमें जोड़ा जा सके। ऊपर दिया गया `list_toolbar_extra` example ऐसा ही करता है, और बिल्ट-इन `index.html` तथा `create.html` भी `head_css` block के लिए यही pattern अपनाते हैं।

### Example: sidebar logo को inline SVG से replace करना {#example-replacing-the-sidebar-logo-with-an-inline-svg}

Logo set करने का सबसे तेज़ तरीका `Admin(logo_url=...)` को URL pass करना है, जो external `.svg` files सहित ज़्यादातर cases को cover करता है। लेकिन बिल्ट-इन टेम्पलेट उस URL को एक `<img>` tag के अंदर render करता है, इसलिए SVG आस-पास के पेज से CSS properties inherit नहीं कर सकता।

जब आप चाहते हैं कि logo बाकी UI के साथ respond करे, तब **inline `<svg>` markup** के साथ `brand` block को ओवरराइड करें।

#### कार्यान्वयन {#implementation}

अपनी templates directory में एक `layout.html` फ़ाइल बनाएँ। एडमिन का हर पेज `layout.html` से inherit होता है, इसलिए यह एक override sitewide लागू होता है।

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "navbar-logo class रखें"
    अपने custom `<svg>` element पर `navbar-logo` CSS class लगी रहने दें। यह आपके inline graphic को framework की alignment, padding, और sizing बिना किसी अपने CSS के दे देती है।

## Field templates ओवरराइड करना {#overriding-field-templates}

हर field context तीन subdirectories का उपयोग करती है:

| Directory | Used in |
| --- | --- |
| `fields/list/<type>.html` | List table cell (compact, read-only) |
| `fields/detail/<type>.html` | Detail पेज display (full, read-only) |
| `fields/form/<type>.html` | Create और edit form input |

Text fields का list cell आप form या detail display को छुए बिना ओवरराइड कर सकते हैं:

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Type को हर जगह override करने की जगह किसी एक **field instance** को अपने टेम्पलेट की ओर point करने के लिए, field पर ही `list_template`, `detail_template`, `form_template`, `null_template`, या `empty_template` set करें:

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (default `"fields/detail/_null.html"`) और `empty_template` (default `"fields/detail/_empty.html"`) अलग slots हैं। जब भी field की value `None` हो या खाली list या tuple हो, list और detail पेज उन्हें `list_template` या `detail_template` की जगह render करते हैं:

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Widget templates ओवरराइड करना {#overriding-widget-templates}

Widgets भी वही override pattern अपनाते हैं। अपनी files `widgets/` directory के अंतर्गत रखें:

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Global template variables

ये variables हर टेम्पलेट में बिना pass किए available होते हैं। `Admin` उन्हें setup के दौरान एक बार Jinja2 globals के रूप में install करता है:

| Variable | Type | Description |
| --- | --- | --- |
| `views` | `list[BaseView]` | सभी registered views (sidebar render करने के लिए उपयोग) |
| `app_title` | `str` | Admin का title (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True` यदि कोई auth provider configured है |
| `__name__` | `str` | Admin का route name prefix (जैसे, `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → किसी built-in static asset का URL। `v` argument एक `?v=` cache-busting query parameter append करता है। |
| `logo_url` | `callable` | `logo_url(request)` → Sidebar logo का URL, unset होने पर `None` |
| `login_logo_url` | `callable` | `login_logo_url(request)` → Login पेज logo का URL, unset होने पर `None` |
| `favicon_url` | `callable` | `favicon_url(request)` → Favicon का URL, unset होने पर `None` |
| `list_url` | `callable` | `list_url(request, **overrides)` → Query string में `overrides` merge करके URL (sort, pagination, या search links के लिए उपयोग)। कोई key drop करने के लिए `None` pass करें। |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → किसी record के detail पेज का URL |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → किसी record के edit पेज का URL |
| `export_url` | `callable` | `export_url(request, key, fmt)` → Export download URL जो current list पेज की filter/sort/search state carry करता है |
| `import_url` | `callable` | `import_url(request, key)` → Import POST URL |
| `get_locale` | `callable` | `get_locale()` → Active locale string (`request` argument की ज़रूरत नहीं) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Locale string का human-readable नाम |
| `i18n_config` | `I18nConfig` | Admin का i18n configuration object |
| `get_timezone` | `callable` | `get_timezone()` → Active timezone string (`request` argument की ज़रूरत नहीं) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Timezone string का human-readable नाम |
| `timezone_config` | `TimezoneConfig | None` | Admin का timezone configuration |
| `theme_settings` | `TablerSettings` | `DefaultTheme` द्वारा expose की गई active Tabler theme configuration (base, primary, radius, mode) |
| `csrf_input` | `callable` | `csrf_input(request)` → Hidden CSRF `<input>` render करता है |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone`, और `get_timezone_display_name` कोई `request` parameter नहीं लेते। ये locale और timezone को `Request` object से नहीं, बल्कि उन `contextvars` से पढ़ते हैं जिन्हें `LocaleMiddleware` request की अवधि के लिए populate करता है।

## Per-page context variables

ऊपर दिए गए globals के अलावा, हर पेज अपना context dictionary `TemplateResponse` को pass करता है।

### `list.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | Current view |
| `title` | `str` | Page title |
| `fields` | `list[BaseField]` | फ़िलहाल visible columns |
| `all_fields` | `list[BaseField]` | सभी list fields (hidden सहित) |
| `rows` | `list[dict]` | Serialized row data |
| `total` | `int` | Pagination के लिए match करने वाले कुल records |
| `total_pages` | `int` | कुल पेज count |
| `range_start` | `int` | इस पेज का पहला record number (1-based) |
| `range_end` | `int` | इस पेज का आख़िरी record number |
| `list_params` | `ListParams` | Parsed URL state (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Active top-level filter group के लिए `"and"` या `"or"` में evaluate होता है |
| `filter_chips` | `list` | Active filter chip descriptors |
| `filter_builder_fields` | `list` | Filter builder UI में available fields |
| `raw_filter` | `str | None` | URL से raw JSON filter string |
| `_actions` | `list` | Available bulk actions |
| `row_actions` | `dict[Any, list]` | Record के हिसाब से available row actions, pk द्वारा keyed |

### `detail.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | Current view |
| `title` | `str` | Page title |
| `obj` | `dict` | Serialized record |
| `raw_obj` | `Any` | Serialization से पहले का raw model object |
| `inlines` | `list[dict]` | Inline context (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Available row actions |

### `create.html` / `edit.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | Current view |
| `title` | `str` | Page title |
| `obj` | `dict` | Current field values (create पर defaults, edit पर existing values) |
| `raw_obj` | `Any` | Raw model object (केवल edit पर, create पर absent) |
| `errors` | `dict[str, list[str]]` | Validation errors, field name द्वारा keyed (केवल failed submit के बाद present) |
| `inlines` | `list[dict]` | Inline formset context |

## अपने globals और filters जोड़ना {#adding-your-own-globals-and-filters}

Templates में अपने variables और functions जोड़ने के लिए, `Admin` को subclass करें और `__init__` को override करें। पहले `super().__init__()` call करें, ताकि जोड़ने से पहले `self.templates` मौजूद हो:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## Built-in Jinja2 filters

हर admin instance `_setup_templates` के दौरान ये filters register करता है:

| Filter | Signature | Description |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | यदि resource एक `CustomView` है तो `True` return करता है |
| `is_link` | `view | is_link` | यदि resource एक `Link` है तो `True` return करता है |
| `is_model_view` | `view | is_model_view` | यदि resource एक `BaseModelView` है तो `True` return करता है |
| `is_dropdown` | `view | is_dropdown` | यदि resource एक `DropDown` है तो `True` return करता है |
| `tojson` | `value | tojson` | HTML-safe JSON serialization (Jinja2 के default `tojson` की जगह) |
| `file_icon` | `mime_type | file_icon` | MIME type के लिए full icon class return करता है (जैसे, `application/pdf` → `fa-solid fa-fw fa-file-pdf`); अपना icon set उपयोग करने के लिए `self.templates.env.filters["file_icon"]` को override करें |
| `to_view` | `key | to_view` | Key string से registered `BaseModelView` ढूँढता है; न मिलने पर 404 `HTTPException` raise करता है |
| `is_iter` | `value | is_iter` | यदि value `list` या `tuple` है तो `True` return करता है |
| `is_str` | `value | is_str` | यदि value एक `str` है तो `True` return करता है |
| `is_dict` | `value | is_dict` | यदि value एक `dict` है तो `True` return करता है |
| `ra` | `value | ra` | String को `RequestAction` enum member में convert करता है |
| `safe_url` | `url | safe_url` | URL केवल तब return करता है जब वह safe-URL check pass करे, अन्यथा `""` return करता है |
| `sanitize_html` | `html | sanitize_html` | HTML string से disallowed tags strip करके एक `Markup` return करता है |

---

## आगे क्या {#whats-next}

* **[Form Layouts](form-layout.md):** Create और edit forms को titled, optionally collapsible groups में split करें, और उनका markup बदलने के लिए `_form_group.html` को ओवरराइड करें।
* **[Custom Themes](custom-themes.md):** अलग-अलग टेम्पलेट को छुए बिना admin को restyle करें।
* **[Custom Fields](custom-fields.md):** किसी field की Python class को उसके अपने `list_template` या `form_template` से pair करें।
* **[Extension Points](extension-points.md):** Templates से आगे pluggable surfaces की पूरी सूची।
