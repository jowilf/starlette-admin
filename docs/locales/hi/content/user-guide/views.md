---
title: व्यूज़
description: starlette-admin में list और detail views कॉन्फ़िगर करना सीखें — search,
  sorting, और pagination सहित।
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Views

`starlette-admin` अपना sidebar तीन प्रकार के views से बनाता है: `ModelView` database model expose करता है, `CustomView` standalone page render करता है, और `Link` hyperlink जोड़ता है।

## ModelView

Database model को admin में expose करने का तरीका है `ModelView` subclass। उस view पर class attributes और method overrides तय करते हैं कि resource कैसा दिखे, कैसे behave करे, और data कैसे handle करे।

इस section का हर example निम्नलिखित SQLAlchemy setup उपयोग करता है:

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Basic usage

`Post` model expose करने के लिए `ModelView` subclass करें और उसके attributes configure करें।

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

View class कुछ नहीं करती जब तक आप उसे `Admin` instance के साथ register न करें:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

उसी तरह, `Post` model पर बना runnable admin देखने के लिए [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) देखें।

View register करने पर records को list, view, create, edit, delete करने के paginated, sortable, searchable interfaces generate हो जाते हैं। आप न routes लिखते हैं और न templates.

!!! note
    `ModelView` को अपने backend के contrib package — जैसे `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel`, या `.tortoise` — से import करते हैं। **नीचे वर्णित हर attribute सभी backends में identical है**, इसलिए आप बाद में SQLAlchemy model को MongoEngine document से बदल सकते हैं बिना view logic छुए।

### Core configuration

#### Naming and routing

डिफ़ॉल्ट रूप से admin URL routing और UI labels model के class name से derive करता है। `Post` model के लिए:

* **Key:** `post` (URL: `/admin/post/list`)
* **Menu label:** `Posts` (sidebar entry)
* **Display name:** `Post` (**New Post** जैसे UI buttons)

Derived values ग़लत होने पर registration या constructor में उन्हें override करें।

| Attribute | Description | Example override | Resulting UI or URL |
| --- | --- | --- | --- |
| **`key`** | The internal slug and base URL route. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | The plural noun used in the sidebar. | `menu_label="Blog Posts"` | **Sidebar:** Blog Posts |
| **`display_name`** | The singular noun used in actions and forms. | `display_name="Article"` | **Buttons:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Field selection and customization

`fields` list तय करती है कि कौन से model attributes list view, detail page, और forms पर दिखें। Omit करने पर हर model attribute expose होता है।

Widgets, validation, labels नियंत्रित करने के लिए string names और explicit `BaseField` instances mix करें:

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    Primary key admin detect कर लेता है। `pk_attr` तभी define करें जब detection fail हो — जैसे single-field primary key विहीन custom backend पर।

#### Contextual field visibility

Fields अक्सर list या detail page पर होने चाहिए पर create form पर नहीं — timestamps और system-managed statuses जैसे। Specific surfaces से field छिपाने के लिए `exclude_fields_from_*` attributes उपयोग करें:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

उपलब्ध exclusion attributes `_create`, `_edit`, `_list`, `_detail`, `_export`, और `_import` पर ख़त्म होते हैं।

!!! important
    Record create करते समय users को primary key सेट करने देने के लिए — जो default रूप से बंद है — `show_pk_in_forms = True` सेट करें।

#### Form layout

डिफ़ॉल्ट रूप से `fields` create/edit forms को flat, vertical list के रूप में render करता है। Data definitions छुए interface reorganize करने के लिए `form_layout` attribute उपयोग करें।

**The tuple shorthand**

Basic grid के लिए widget classes import करने की ज़रूरत नहीं। Field names को tuple में group करें ताकि वे एक row में side by side render हों।

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Advanced layout widgets**

Forms बढ़ने पर उन्हें layout widgets से structure करें। Tuple shorthand उनके अंदर काम करता है:

* **`PanelWidget` या `FieldsetWidget`:** Related fields को heading के अंतर्गत group करें, या section collapsible बनाएँ।
* **`TabsWidget`:** Data की distinct categories — जैसे shipping details और SEO metadata — जिन्हें simultaneously visible होने की ज़रूरत नहीं, अलग करें।

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

Explicit widths वाली multi-column rows, tabs, static content, और access-control behavior के लिए [Form Layouts](../advanced/form-layout.md) देखें।

### Data table features

#### Search and sort

`searchable_fields` और `sortable_fields` से नियंत्रित करें कि users data कैसे ढूँढें और order करें।

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**: Filter builder और global search box चालू करता है। Global search इन fields पर full-text query चलाता है।
* **`sortable_fields`**: सीमित करता है कि users किन column headers से sort कर सकते हैं। URL parameters से आया दूसरे field का sort query ignore हो जाता है।
* **`fields_default_sort`**: Initial table state सेट करता है। Ascending sort के लिए bare string pass करें; descending के लिए `True` वाला tuple; explicit ascending के लिए `False` वाला tuple। Multi-column sort के लिए कई items chain करें।

#### Pagination and UI controls

इन attributes से list page layout fine-tune करें:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` and `page_size_options`**: Default pagination limit और dropdown choices.
* **`show_goto_page`**: Large datasets के लिए "go to page" input जोड़ता है।
* **`search_auto_submit`**: User के type करते ही filter करता है।
* **`show_detail_search`**: Detail page पर search box जोड़ता है जो inline relationship tables को filter करता है।
* **`row_click_navigate`**: Table row पर कहीं भी select करने पर detail page खोलता है। Default रूप से चालू। Rows inert रखने के लिए `False` सेट करें — तब users row actions से navigate करते हैं। जिन users की `can_view_detail` check fail हो, उनके लिए rows कभी clickable नहीं।

#### Inline editing

आप users को list view से ही specific fields change करने दे सकते हैं, पूरा edit form खोले बिना।

`inline_editable_fields` attribute से declare करें कि कौन से columns support करते हैं। Enabled cell select करने पर quick update के लिए popover खुलता है।

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "सुरक्षा और access"
    Inline editing default रूप से बंद रहता है। चालू करने पर भी view की existing `can_edit` permission gate बनी रहती है।

Configuration details, validation behavior, और supported field types का पूरा matrix देखने के लिए [Inline Edit](inline-edit.md) guide देखें।

### Relational data

Admin data relationships आपके लिए handle करता है। `Post` और `Author` के many-to-one setup के लिए relationship attribute को अपनी `fields` list में जोड़ें। जब तक दोनों models के views registered हैं, UI सही widgets render करता है।

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Manual relationship declaration

`HasOne` या `HasMany` fields स्वयं तभी declare करें जब target view custom `key` के अंतर्गत registered हो।

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Object representation

जब admin record को single value के रूप में दिखाना चाहे, वह primary key पर fallback करता है। `Author #3` से linked `Post` relationship columns में "3" की तरह render होता है, जो user को लगभग कुछ नहीं बताता। दो optional methods — **model** पर defined, view पर नहीं — default को meaningful चीज़ से बदल देती हैं। दोनों current `Request` accept करती हैं और synchronous या asynchronous हो सकती हैं।

#### `__admin_repr__`

Plain string return करती है; record text के रूप में जहाँ-तहाँ दिखे वहीं उपयोग होती है: list/detail pages के relationship columns, breadcrumbs, action confirmation messages.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

यह method होने पर post का author "3" के बजाय "Gabriel Garcia Marquez" render होता है।

#### `__admin_select2_repr__`

ऐसा HTML snippet return करती है जो relationship form fields द्वारा उपयोग किए गए `select2` dropdowns में options render करता है, इसलिए choices को images, badges, secondary text से enrich कर सकते हैं। Method न होने पर admin `__admin_repr__` के escaped output पर fallback करता है। दोनों methods न होने पर record के non-relation fields का generated summary दिखाता है।

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    Returned value valid HTML होनी चाहिए।

!!! warning
    Cross-site scripting (XSS) attacks रोकने के लिए database values escape करें। Snippet को ऊपर दिखाए अनुसार Jinja2 और `autoescape=True` से render करें, या हर value स्वयं `html.escape` से escape करें। अधिक जानकारी के लिए [OWASP documentation](https://owasp.org/www-community/attacks/xss/) देखें।

### Security and authorization

अपने `ModelView` पर permission methods override करके access restrict करें। प्रत्येक boolean return करता है, और base implementations सभी `True` return करती हैं।

यह pattern सीधे आपके `AuthProvider` से जुड़ता है। नीचे के example में हर check session के `admin_user` से `roles` list पढ़ता है:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

`AuthProvider` configure करने और `admin_user` object populate करने के बारे में अधिक जानकारी के लिए [Authentication](auth.md) देखें।

!!! note
    केवल वही methods override करें जिन्हें restrict करना है। बाकी access allow करती रहेंगी।

### Lifecycle hooks

Database transaction के ठीक पहले या बाद side effects चलाने या data mutate करने के लिए lifecycle hooks उपयोग करें।

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

उपलब्ध hooks: `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete`, और `after_delete_committed`.

#### Committed hooks

`after_create_committed`, `after_edit_committed`, और `after_delete_committed` केवल database transaction commit होने के बाद चलते हैं। ऐसे side effects के लिए उन्हें उपयोग करें जो write rollback होने पर होने ही नहीं चाहिए — email भेजना या background jobs queue करना:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    इन hooks के चलने तक request session committed और closed हो चुका होता है। इनके अंदर `request.state.session` से database में न लिखें। External I/O उपयोग करें, या नया database session खोलें।

!!! important
    `after_delete_committed` में `obj` किसी session से detached होता है। Delete से पहले load हुए attributes readable रहते हैं, पर जो कभी load नहीं हुआ था उसे पढ़ना fail होगा, क्योंकि row गई चुकी है।

!!! note "बैकएंड सपोर्ट"
    केवल वही backends ये hooks emit करते हैं जो commit को request के अंत तक टालते हैं। आज में वह SQLAlchemy backend है।

!!! tip
    कई views में फैले logic — जैसे audit log — के लिए [Events](../advanced/events.md) उपयोग करें।

### UI customization

#### साइडबार organization {#sidebar-organization}

Related views को `DropDown` से collapsible folder में group करें। Folder `ModelView`, `CustomView`, और `Link` entries mix कर सकता है।

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Exporters and importers

`exporters` और `importers` attributes तय करते हैं कि data transfer के लिए कौन से formats उपलब्ध हों। Built-in options और अपने options लिखने के लिए [Export & Import](export-import.md) guide देखें।

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Actions, inline forms, and templates

जटिल cases के लिए `ModelView` में तीन और feature sets हैं, प्रत्येक की अपनी guide:

* **Actions and row actions:** `actions` और `row_actions` attributes CRUD से आगे custom batch और per-row operations जोड़ते हैं। [Actions](actions.md) देखें।
* **Inline forms:** `inlines` attribute related model के create/edit forms को parent view के भीतर nest करता है। [Inline Forms](inline-forms.md) देखें।
* **Templates and assets:** Default pages को अपने Jinja templates से `list_template`, `detail_template`, `create_template`, या `edit_template` के माध्यम से replace करें। [Templates](../advanced/templates.md) देखें।

## CustomView

हर admin page database model से map नहीं होता। `CustomView` widgets, custom templates, या custom routes से बना standalone sidebar page बनाता है।

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

पूरा widget catalog, dashboard instructions, और custom routes के लिए [Custom Views](custom-views.md) देखें।

## Link

`Link` sidebar में hyperlink जोड़ता है, users को live site, external documentation, या किसी और internal tool की ओर point करते हुए।

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** and **`icon`**: The sidebar entry text and icon.
* **`url`** and **`target`**: The destination and the anchor target attribute.

`admin.add_link(link)` `admin.add_view(link)` के चारों ओर thin wrapper है। Codebase में जो बेहतर पढ़े, वह उपयोग करें। `Link` को `DropDown` के अंदर भी nest कर सकते हैं, जैसा [Sidebar organization](#sidebar-organization) में दिखाया गया है।

---

## What's next

* **[Fields](fields.md)**: The complete field type catalog.
* **[Form Layouts](../advanced/form-layout.md)**: Arrange create and edit forms with rows, panels, fieldsets, and tabs.
* **[Custom Views](custom-views.md)**: Build dashboards and standalone pages with widgets, templates, and custom routes.
* **[Actions & Row Actions](actions.md)**: Add batch and per-row operations beyond CRUD.
* **[Inline Edit](inline-edit.md)**: Let users edit a single field of a row from the list page.
* **[Inline Forms](inline-forms.md)**: Nest a related model's create and edit forms inside a parent view.
* **[Templates](../advanced/templates.md)**: Swap in your own Jinja templates and inject custom assets.
