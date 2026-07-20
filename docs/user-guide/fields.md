# Fields

Fields are the core building blocks of your models. Under the hood, they are plain Python dataclasses. Every attribute you pass to a field constructor becomes a dataclass field, and every field type is a subclass of `BaseField` that you can inspect, subclass, or instantiate directly.

## Common Attributes

All field types inherit a standard set of configuration attributes from `BaseField`.

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | **Required** | The attribute name on your model. |
| `label` | `str | None` | Title-cased `name` | The column header and form label. |
| `help_text` | `str | None` | `None` | Hint text displayed below the form input. |
| `required` | `bool` | `False` | Enforces presence in forms (client- and server-side). |
| `validators` | `list[Validator]` | `[]` | Server-side validators run against the submitted value. See [Validation](#validation). |
| `disabled` | `bool` | `False` | Greys out and locks the input in forms. |
| `read_only` | `bool` | `False` | Displays the field but prevents edits. |
| `default` | `Any | Callable` | `None` | The prefill value on the create form. |
| `getter` | `Callable | None` | `None` | Replaces the model attribute lookup when reading the value. See [Computing, Formatting, and Parsing Values](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Per-action display formatting, replacing serialization for that action. See [Computing, Formatting, and Parsing Values](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Per-action input parsing, replacing the field's default parsing. See [Computing, Formatting, and Parsing Values](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Included when the `q` search parameter matches. |
| `orderable` | `bool` | `True` | Enables a sort link in the list header. |
| `copy_to_clipboard` | `bool` | `False` | Adds a copy button next to the value on the detail page. |
| `filters` | `list | None` | `None` | Explicit override for list page filters. |
| `extra` | `dict[str, Any]` | `{}` | A dictionary for storing custom metadata. |

### Visibility Controls

You can fine-tune where a field is displayed using the following boolean flags (all default to `False`):

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Defining Defaults

The `default` attribute is highly flexible and accepts static values, zero-argument callables, or request-aware functions:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Computing, Formatting, and Parsing Values

Every field accepts three callable hooks (`getter`, `formatter`, and `parser`) to intercept and transform data as it flows between your model and the UI. These hooks accept both synchronous and asynchronous functions.

#### `getter`: Reading Custom Values

The `getter` hook replaces the default `getattr()` lookup when reading a model instance. The field calls `getter(request, obj)` and displays the return value.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Because `getter` values rarely map to physical database columns, they pair best with a read-only display. The [`ComputedField`](#computedfield) is a built-in shortcut for this exact combination.

#### `formatter`: Transforming Display Output

The `formatter` hook dictates how a stored value renders on specific pages. It maps a `RequestAction` (`LIST`, `DETAIL`, `EXPORT`, etc.) to a `(request, value) -> value` callable.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Formatting behavior to note:**

* **Handles nulls:** Unlike default serialization, formatters receive `None` values, allowing you to provide fallback text (like `"unset"` in the example above).
* **Bypasses serialization:** A matched formatter completely replaces the field's default `serialize_value` and `serialize_none_value` methods. The return value is used exactly as-is, making the formatter fully responsible for producing the final displayable output.
* **JSON requirement:** Values returned for `LIST` and `RELATION_LOOKUP` actions must remain JSON serializable.

#### `parser`: Processing Incoming Data

The `parser` hook overrides the field's default logic for parsing submitted or imported data. It maps a `RequestAction` to a `(request, raw) -> value` callable.

* **Forms (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` is the submitted form input (a list if `multiple=True`).
* **Imports (`IMPORT`):** `raw` is the unprocessed cell value from the file.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

After parsing, the returned value proceeds through the standard validation chain (`required`, then `validators`) exactly as if the field had parsed the data itself.

!!! tip "Hooks vs. Subclassing"
    For a one-off customization on a single field, you rarely need a subclass. Instead, pass these hooks directly as constructor arguments to handle reading, display formatting, and input parsing.
    **When to subclass:** [Subclass the field](../advanced/custom-fields.md) only if you need to reuse the logic across multiple views or if you need to modify the HTML rendering templates.

### Validation

Server-side validation runs on every field during form submission (create or edit actions). This ensures data integrity before interacting with the database.

The validation lifecycle follows a strict sequence:

1. **Empty Values:** If a submitted value is empty (like `None`, `""`, or an empty collection), the system checks only the `required` flag. Standard validators are bypassed entirely.
2. **Populated Values:** If data is present, the system executes each callable defined in the `validators` list sequentially against the parsed value.

#### Validator Signature

Validators receive four arguments: `(request, field, value, form_values)`.

* **`request`:** The current Starlette request object.
* **`field`:** The field instance currently being validated.
* **`value`:** The parsed value submitted for this field.
* **`form_values`:** A dictionary containing all parsed form data keyed by field name. This allows you to inspect other fields during validation.

To reject an invalid value, raise a `ValueError`. The system catches the first error raised, skips any remaining validators for that specific field, and aggregates all errors to display them next to their respective inputs in the UI.

#### Built-in Validators

The [`starlette_admin.validators`](../api/validators.md) module provides standard validation rules:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Custom and Asynchronous Validation

You can write custom validators as synchronous or asynchronous functions. Because they receive the `request` object, they can easily perform database queries to check complex constraints.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

By leveraging the `form_values` argument, a field-level validator can also enforce rules that depend on other submitted fields.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Context-Specific Validation Rules

* **Relation Fields:** Fields like `HasOne` and `HasMany` receive the primary keys of the related records during validation.
* **File Fields:** Validation runs independently for every `UploadFile` in the payload. See [File & Media Fields](#file-media-fields) for more details.
* **Cross-Field Validation:** While you can use `form_values` for simple dependencies, complex rules spanning the entire form state should be handled differently. Override the `validate()` method on your view instead. This view-level validation runs only after every individual field successfully clears its own validation chain.

### Storing Custom Metadata

`extra` is a plain `dict` that starlette-admin never reads from or writes to. Use it to attach your own data to a field instance (for a custom template, a hook in your [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) subclass, or any other integration point) without subclassing the field:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Text Fields

### StringField & TextAreaField

`StringField` renders a standard single-line text input for brief content, while `TextAreaField` extends it to support multi-line long text via a `<textarea>` element.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Extra Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `maxlength` / `minlength` | `int | None` | `None` | HTML length constraints. |
| `placeholder` | `str | None` | `None` | Input placeholder text. |
| `rows` *(TextArea only)* | `int` | `6` | Number of visible text lines. |

### TinyMCEEditorField

Extends `TextAreaField` by integrating a WYSIWYG editor from the TinyMCE library. Requires the `tinymce` extra package.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    The `height`, `menubar`, `statusbar`, and `toolbar` attributes control the editor's UI. You can pass any native TinyMCE configuration via `extra_options`.

### Formatted Text Fields

Specialized `StringField` variants that render matching HTML input types and provide customized display formatting when viewing records.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField`, and `IPAddressField` each default to a matching validator (`email`, `url`, `uuid`, `ip_address` from [`starlette_admin.validators`](../api/validators.md)) when `validators` is left empty. Pass your own `validators` to override it.

    `UUIDField` sets `copy_to_clipboard=True` by default. `IPAddressField` accepts `ipv4` (default `True`) and `ipv6` (default `False`) to control which address families its default validator accepts.

### PasswordField

Renders an `<input type="password">` element on forms to obscure user input.

!!! danger
    `PasswordField` only masks the input on create/edit forms. It does not override the display templates, meaning values render as **plain text** in lists and detail pages. It also logs raw submitted values at the `DEBUG` level.
    > **Best Practice:** Set `exclude_from_list = True` and `exclude_from_detail = True` on password fields, and disable `DEBUG` logging in production.

## Numeric Fields

Numeric fields handle integers, floats, and decimals.

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| Extra Attribute | Applicable To | Description |
| --- | --- | --- |
| `min` / `max` | Integer, Decimal | Minimum and maximum allowed values. |
| `step` | Integer, Decimal | The increment step constraint. |

!!! note
    `FloatField` operates uniquely. It renders as a plain text input coerced to a `float` upon submission and does not support `min`, `max`, or `step`.

## Date & Time Fields

These fields utilize native browser date and time pickers, backed by their respective standard library types (`datetime.date`, `datetime.datetime`, `datetime.time`).

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| Extra Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel display format (`"short"`, `"medium"`, `"long"`, `"full"`, or custom). |
| `search_format` | `str | None` | ORM-specific | Format utilized for building database search queries. |

!!!note
    `DateTimeField` automatically handles conversions between configured display timezones and database timezones when timezone support is enabled.

### ArrowField

A variant of `DateTimeField` backed by an `Arrow` object. It displays as a humanized relative time (e.g., "3 hours ago") outside of edit forms. Requires the `arrow` package.

## Selection & Collection Fields

### EnumField

The universal select field. It renders a `<select>` dropdown (or a `select2` multi-select when `multiple=True`). It can be backed by a Python `Enum` subclass, a list of tuples, or dynamically loaded choices.

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| Extra Attribute | Type | Description |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Build choices from a Python `Enum` class. |
| `choices` | `Sequence | None` | Static `(value, label)` pairs or bare values. |
| `choices_loader` | `Callable | None` | Dynamically compute choices per request. |
| `multiple` | `bool` | Enables multi-select, storing values as a list. |

!!! important
    You must provide exactly one of: `enum`, `choices`, or `choices_loader`.

`TimeZoneField`, `CountryField`, and `CurrencyField` are specialized `EnumField` subclasses backed by Babel locale data (requires the `i18n` extra). They automatically localize the displayed labels based on the current request context.

### TagsField

A free-text tagging input using `select2`. It stores a list of strings (`list[str]`) without requiring a pre-defined set of choices.

### ListField

Wraps another field to store an ordered list of values of that specific type. It renders as repeatable rows with add/remove controls. The wrapped field's name dictates the `ListField`'s name.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Groups multiple sub-fields into a single nested object. Ideal for embedded or struct-like data (e.g., MongoDB embedded documents).

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## Specialized Fields

### JSONField

Renders a JSON tree/code editor and stores a Python `dict`. You can provide a standard JSON Schema dictionary to `validation_schema` to enable client-side feedback.

### SlugField

A variant of `StringField` that auto-populates client-side based on the input of another field. Manual edits stop the auto-fill behavior.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! note
    The `populate_from` attribute is strictly required and must point to another field on the same form. The generated slug is submitted and stored in the database like any standard string.

### ComputedField

A read-only, virtual field derived dynamically from the model instance at display time. It requires no underlying database column. It builds on the [`getter` hook](#computing-formatting-and-parsing-values) available on every field, adding the defaults a virtual column needs: excluded from create forms, read-only, non-searchable, and non-orderable.

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

For complex or reusable logic, you can subclass `ComputedField` and override `parse_obj()` instead of passing an inline `getter`:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` and `parse_obj` accomplish the same task: use `getter` for brief expressions, or subclass `ComputedField` when the logic spans multiple lines or is reused across views. On edit forms the field still appears as a plain-text display, so the user sees the current computed value.

Any subclass of `ComputedField` keeps `StringField` rendering. To compute a value that should render as another type (a date, a badge, an image), set `getter=` on that field type directly along with the relevant `read_only` and `exclude_from_*` flags.

## File & Media Fields

`FileField` renders a standard file upload input; `ImageField` adds an image preview and validity check. Attach a `storage=` backend to automatically save uploads and store a JSON `FileInfo` dictionary in the database, with full configuration details available in the [File Storage guide](file-storage.md).

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| Extra Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` |
| `multiple` | `bool` | `False` | Allows batch uploading of multiple files. |
| `storage` | `BaseStorage | None` | `None` |
| `upload_folder` | `str` | `""` | The storage-relative folder for saved files. |
| `max_size` | `int | None` | `None` |
| `validators` | `list[Validator]` | `[]` | Custom validators, each called as `(request, field, upload)` once per uploaded file, after the `accept` and `max_size` checks. Raise `ValueError` to reject. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | `ImageField` only. When set, a bounded thumbnail is generated with Pillow at save time and used on the list page in place of the full image. |

!!! note
`ImageField` automatically prepends a Pillow-based image validity check to the `validators` list. If Pillow is installed and storage is configured, it will also record the `width` and `height` in the resulting `FileInfo`.

With `thumbnail_size` set, a thumbnail is generated alongside the full image (aspect ratio preserved, never upscaled) and stored under its own key, e.g. `covers/cat.jpg` gets a `covers/cat.thumb.jpg` sibling. The list page uses the thumbnail automatically; rows without one (pre-existing data, or `thumbnail_size` left unset) fall back to the full image. A thumbnail generation failure is logged and never fails the upload itself.

The detail page opens every `ImageField` image in a lightbox, so visitors can click through to a full-resolution, navigable view. Images that belong to the same field (`multiple=True`) are grouped into a single gallery.

See [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) for a complete runnable app, including a custom MIME-type validator.

### Without a storage

When no `storage=` is attached, the field hands uploads to your backend raw instead of saving them itself:

* **In create and edit forms**, the parsed value is a tuple `(UploadFile | list[UploadFile] | None, bool)`. The first element is the raw Starlette `UploadFile` (a list when `multiple=True`, or `None` when the user selected nothing). The second element is `True` when the user checks the delete box on the edit form, meaning they want the existing file removed without uploading a replacement. Your backend's `edit()` / `create()` logic is responsible for storing the upload and honoring the delete flag.
* **On list and detail pages**, the field expects the value to expose three keys (as a `dict`) or attributes (as an object): `url` (required, the link target), `filename` (the display label), and `content_type` (selects the file-type icon).

This contract is how the ORM integrations below plug their own file handling into the same field.

### ORM-native file columns

**MongoEngine** supports `mongoengine.FileField` and `mongoengine.ImageField` out of the box, using **GridFS** as the storage. The admin uploads to, serves from, and deletes files in GridFS automatically. No `storage=` configuration is needed; just list the field by name.

**SQLAlchemy** gets the same treatment through [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/): declare its `FileField` / `ImageField` column types on your models and starlette-admin detects them, renders the matching admin field, and registers a route to serve the stored files. Storage is configured through sqlalchemy-file's own `StorageManager` (backed by Apache Libcloud containers), and uploads participate in the session transaction. A rolled-back session discards the stored file.

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

See [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) for a full app with multiple storages, content-type validation, and `multiple=True` fields.

### HasOne & HasMany

Relational fields that render as `select2` inputs, seamlessly backed by the related view's search endpoint.

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

The `key` parameter links to the corresponding `ModelView`. Both views must be registered on the same `Admin` instance to resolve correctly.

---

### What's Next

* [Filters](filters.md): Learn how to customize the filter builder on your list pages.
* [File Storage](file-storage.md): Configure storage backends for `FileField` and `ImageField`.
* [Custom Fields](../advanced/custom-fields.md): build a custom field
