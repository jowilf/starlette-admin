---
title: माइग्रेशन गाइड
description: starlette-admin के पुराने वर्शनों से नवीनतम रिलीज़ पर माइग्रेट करने की
  अपग्रेड गाइड — breaking changes और new features सहित।
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# माइग्रेशन गाइड {#migration-guide}

यह पेज `starlette-admin` रिलीज़ों के बीच upgrade instructions collect करता है। जिस वर्शन से आप upgrade कर रहे हैं, उससे match करने वाले section पर जाएँ।

---

## 0.17.x से 1.0.0 {#from-017x-to-100}

यह रिलीज़ `starlette-admin` के internals refactor करती है और new features का बड़ा set introduce करती है। High-level API largely unchanged रहते हुए भी, सबसे महत्त्वपूर्ण update list page rendering का rewrite है। हमने DataTables को server-rendered table के पक्ष में हटा दिया है। बाकी ज़्यादातर updates renames या minor signature changes हैं।

यह guide हर breaking change को उसी क्रम में cover करता है जिसमें आप उन्हें सबसे पहले encounter करने की संभावना रखते हैं। प्रत्येक section पुराने API को उसके replacement के साथ compare करता है। यदि आपका implementation basics या light customizations (जैसे एक `Admin` instance, कुछ `ModelView` subclasses, `fields`, और `searchable_fields`) पर टिका है, तो आपकी migration शायद केवल [Requirements](#requirements) और [The Admin constructor](#the-admin-constructor) sections तक सीमित रहेगी, साथ में कुछ renames.

पुराने list page के customizations सबसे अधिक ध्यान माँगते हैं। DataTables options और JavaScript render functions का कोई direct equivalent नहीं है; उन्हें server-side templates पर port करना होगा ([DataTables Removal](#datatables-removal) देखें)।

!!! tip
    Dependencies को एक step में upgrade करें और application start करें। Removed/renamed attributes ज़्यादातर startup पर clear errors raise करते हैं, runtime पर silently fail होने के बजाय।

### What's new

नीचे outlined breaking changes से परे, इस रिलीज़ में:

* **Native list tables:** DataTables हटाकर built-in, server-rendered implementation आई है। Table state अब पूरी तरह URL-driven है — page, filter, और sort configurations तुरंत shareable और bookmarkable.
* **[Filters](user-guide/filters.md):** Nested `AND`/`OR` filter builder DataTables SearchBuilder की जगह लेता है। Filters field types से derive होते हैं और pure Python में पूरी तरह extensible. JavaScript की ज़रूरत के बिना filter class लिख सकते हैं।
* **[Import and Server-Side Export](user-guide/export-import.md):** CSV, JSON, Excel, आदि से per-row error reporting के साथ data import करें, और client-side DataTables buttons की जगह server-side exporters (CSV, JSON, Excel, PDF आदि) उपयोग करें।
* **[Events](advanced/events.md):** `before_create`, `after_edit_committed`, `after_login`, और various action events जैसे lifecycle hooks की सदस्यता लें।
* **[Themes](advanced/custom-themes.md) और [Plugins](advanced/plugins.md):** Custom aesthetics और behaviors package/reuse करें। जल्दी शुरुआत के लिए Cookiecutter templates भी उपलब्ध हैं।
* **[Widgets and Dashboards](user-guide/custom-views.md):** `StatWidget`, `ChartWidget`, `TableWidget`, आदि से index pages और custom views बनाएँ।
* **[Form Layout](advanced/form-layout.md):** Create/edit forms को rows, columns, fieldsets, और tabs से logically arrange करें।
* **[Inline Edit](user-guide/inline-edit.md):** List page से ही single field edit करें।
* **[Inline Forms](user-guide/inline-forms.md):** Parent form के भीतर related models को `InlineModelView` से edit करें।
* **Other Enhancements:** [Flash messages](user-guide/flash-messages.md), [OAuth login](user-guide/auth.md), एक [Tortoise ORM backend](integrations/tortoise.md), new fields (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), field-level `validators`, और किसी भी field पर clipboard copy functionality.
* **[Logging](user-guide/admin.md#debugging):** Package अब internally `starlette_admin` namespace के अंतर्गत log करता है, default silent. Request routing, middleware, और permission decisions console में देखने के लिए `Admin(debug=True)` pass करें या `starlette_admin.logging.configure_logging()` कॉल करें — migration के दौरान विशेष रूप से उपयोगी।
* **Expanded Test Coverage:** Test suite अब substantially बड़ी है, जिसमें admin interface के critical workflows validate करने वाले Playwright end-to-end tests शामिल हैं।
* **Lighter Package**: PyPI पर published package size ~50% कम हुई है।

### आवश्यकताएँ {#requirements}

* **Python Support:** Python 3.11 या newer चाहिए। Python 3.9 और 3.10 support हट गया है।
* **Core Dependencies:** `itsdangerous` अब core dependency है, admin cookies (CSRF tokens और flash messages) sign करने के लिए।
* **New Optional Extras:**

    | Extra | Enables |
    | --- | --- |
    | `starlette-admin[email]` | `EmailField` server-side validation via `email-validator` |
    | `starlette-admin[pdf]` | PDF export via `reportlab` |
    | `starlette-admin[s3]` | S3 file storage via `aiobotocore` |
    | `starlette-admin[tinymce]` | `TinyMCEEditorField` HTML sanitization via `nh3` |
    | `starlette-admin[i18n]` | Translations via `babel` (unchanged) |

* **Beanie Backend:** Beanie 2.0+ चाहिए।
* **Odmantic Backend:** हट गया। यदि आप उस पर depend करते हैं, तो `starlette-admin<=0.17.1` पर रहें और [issue खोलकर](https://github.com/jowilf/starlette-admin/issues) interest दिखाएँ; पर्याप्त demand होने पर support फिर जोड़ा जा सकता है।

### Admin कंस्ट्रक्टर {#the-admin-constructor}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` rename होकर `static_dir` हुआ।
* **`secret_key` सेट करें।** यह key CSRF और flash-message cookies sign करती है। Omitted होने पर startup पर random key generate होती है (development के लिए ठीक), पर signed values हर restart और multiple workers में invalidate हो जाएँगी। Production में stable secret always pass करें।
* `logo_url`, `login_logo_url`, और `favicon_url` अब callable `(request) -> str | None` accept करते हैं। यह `AdminConfig` द्वारा पहले दी जाने वाली per-request branding replace करता है।
* **New optional parameters:** `theme`, `plugins`, `additional_loaders`, `import_config`, और `export_config`.
* **SQLAlchemy specifics:** पहला argument अब `session_provider` है। वह `Engine` या `AsyncEngine` accept करता है, अब `sessionmaker` या `async_sessionmaker` भी। मौजूदा `Admin(engine)` calls continue करते रहेंगे।
* `timezone_config` का default `None` के बजाय `TimezoneConfig()` है। Datetimes अब default रूप से viewer के local timezone में display होते हैं। Raw values retain करने के लिए `timezone_config=None` pass करें।

### Renamed view identifiers

Views के लिए naming convention अब unified है। अपने `ModelView` constructors और class attributes उसी अनुसार update करें:

| Before | After |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

ध्यान दें कि `Link` और `DropDown` भी `label` के बजाय `menu_label` उपयोग करते हैं।

### DataTables removal

List page अब DataTables का उपयोग नहीं करता। पहले उसे configure करने वाले attributes पूरी तरह removed हैं:

| Removed | Replacement |
| --- | --- |
| `datatables_options` | None. The table is server-rendered. Customize via templates. |
| `search_builder` | The new [filter builder](user-guide/filters.md), enabled by `searchable_fields`. |
| `responsive_table` | None. The table handles overflow natively. |
| `save_state` | Always on. List state (page, sort, filters, search, visible columns) now lives in the URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (a list of filter classes). |
| `BaseField.render_function_key` | `BaseField.list_template` (server-side Jinja template). |

यदि आपने पहले custom JavaScript render functions या DataTables plugins लिखे थे, तो उन्हें `list_template` overrides में port करें। हर field अब अपना list cell सीधे `templates/fields/list/*.html` से render करता है।

### Actions

Batch action handlers अब primary keys की list के बजाय एक `ActionSelection` object receive करते हैं। इससे नए "select all matching" banner — current filter से match करने वाली हर row को client side पर materialize किए बिना target करने वाला — support मिलता है।

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* `selection.rows()`, `selection.pks()`, और `selection.count()` जैसे methods target rows lazily resolve करते हैं। यह तब भी लागू है जब user ने rows individually check की हों और तब भी जब all matching rows select की हों।
* `selection.is_select_all`, `selection.filters`, और `selection.q` जैसी properties operation को single bulk query के रूप में push down करने देती हैं।
* Success message string return करना [flash messages](user-guide/flash-messages.md) से replace हुआ है।
* Row action handlers अपनी original `(request, pk)` signature retain करते हैं।
* **New `@action` options:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size`, और per-request `form` callables.

### Authentication

`starlette_admin/auth.py` module अब `starlette_admin.auth` package है। `starlette_admin.auth` से existing imports continue करते रहेंगे, पर provider contract बदल गया है।

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* Methods `is_authenticated`, `get_admin_user`, और `get_admin_config` एक single `authenticate(request) -> AdminUser | None` method में merge हो गई हैं। `None` return unauthenticated state दर्शाता है।
* `login` और `logout` methods prepared `response` receive या return नहीं करते। Default redirect के लिए `None` return करें, या behavior override करने के लिए custom `Response` return करें।
* `AdminConfig` removed है। Per-request titles और logos को `Admin` instance के `logo_url` और `login_logo_url` के callable form से handle करें।
* Built-in [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) OAuth2/OIDC login flows box से बाहर handle करता है।
* `login_not_required` decorator unchanged रहता है।

### Export and Import

Exports client-side DataTables buttons से server-side streaming endpoints पर चले गए हैं। Import functionality पूरी तरह नई है, और `ExportType` अब मौजूद नहीं है।

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` अब `exporters` है। यह format names या `BaseExporter` instances की list accept करता है। Supported built-ins: `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml`, और `pdf`. `csv`/`json` के अलावा formats को `tablib` चाहिए, PDF को `pdf` extra.
* `importers` format names या `BaseImporter` instances की list accept करता है। Supported built-ins: `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf`, और `html`. `csv`, `tsv`, `json` के अलावा formats को `tablib` चाहिए।
* `export_fields` (include list) replace होकर `exclude_fields_from_export` (exclude list) हुआ। यह बाकी `exclude_fields_from_*` attributes की naming convention से match करता है।
* Fields individually भी `exclude_from_export` और `exclude_from_import` accept करते हैं।
* Global limits `Admin` instance पर `ExportConfig` और `ImportConfig` से configure करें। Details के लिए [Export & Import](user-guide/export-import.md) documentation देखें।

### Custom fields and template overrides

Field templates reorganize हो गए हैं। यदि आप built-in templates override करते हैं या custom fields ship करते हैं, तो paths update करें:

| Before | After |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (client-side render function) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (path) | Same attribute name, new path prefix `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

Explore करने लायक new per-field capabilities: `validators`, `filters`, `default`, hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard`, और arbitrary metadata के लिए एक `extra` dictionary. अधिक जानकारी के लिए [Custom Fields](advanced/custom-fields.md) documentation देखें।

### CustomView

`CustomView` class अब `template_path` और `methods` accept नहीं करती। Simple pages [widgets](user-guide/custom-views.md) से बनाएँ। Full control चाहने वाले pages के लिए `CustomView` subclass करके routes सीधे declare करें।

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

`@route` decorator किसी भी view को extra endpoints expose करने देता है — JSON chart data या webhooks जैसी requirements के लिए।

### Custom backends

यदि आपने custom datasource के विरुद्ध `BaseModelView` implement किया है, तो updated data-access contract ध्यान में रखें:

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* String-typed `where` parameter split होकर `q` (full-text search terms के लिए) और `filters` (filter builder द्वारा दिया गया typed `FilterGroup` tree) हो गया।
* `order_by` parameter (पहले `"field direction"` strings की list) अब `sorts` है — `(field_name, direction)` tuples की list लेता है।
* हर backend अब field types को filter implementations से map करने वाला filter registry ship करता है। Full contract और working example के लिए [Custom Backend](integrations/custom-backend.md) documentation देखें।

### Behavior changes to review

* **Timezones:** Datetimes default रूप से viewer के local timezone में render होते हैं (Admin Constructor section का `timezone_config` note देखें)।
* **URL State:** List state अब URL में रहती है। पिछले versions के bookmarked admin URLs default list states पर पहुँचेंगे, क्योंकि saved DataTables states migrate नहीं होतीं।
* **Email Validation:** `email-validator` इंस्टॉल होने पर `EmailField` अब server पर validate करता है।
* **CSRF Protection:** CSRF protection built-in और cookie-based है। यदि आपने पहले admin को custom CSRF middleware से wrap किया था, तो उसे safely remove कर सकते हैं। Tokens server restarts survive करें, इसके लिए `secret_key` सेट होना सुनिश्चित करें।
* **FileField Upload Size:** `FileField.max_size` अब unlimited के बजाय 50 MB default. पुराना unbounded behavior restore करने के लिए `max_size=None` pass करें, या cap बदलने के लिए explicit value सेट करें।

### Removed with no replacement

* `AdminConfig` ([Authentication](#authentication) देखें).
* `datatables_options`, `responsive_table`, और `save_state` ([DataTables Removal](#datatables-removal) देखें).
* Odmantic backend ([Requirements](#requirements) देखें).

## Getting help

यदि आपको ऐसा migration issue मिले जो इस guide में covered नहीं, तो [issue खोलें](https://github.com/jowilf/starlette-admin/issues)। Problem का minimal reproduction include करें और बताएँ कि आप किस version से upgrade कर रहे हैं। [`Admin(debug=True)`](user-guide/admin.md#debugging) के साथ चलाने पर cause अक्सर सीधे दिख जाता है, और resulting logs report के लिए बढ़िया addition बनते हैं।
