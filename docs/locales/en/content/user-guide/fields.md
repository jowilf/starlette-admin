---
title: Fields
description: Comprehensive reference for all built-in fields in starlette-admin to map your database columns to UI components.
---

# Fields

Fields are the building blocks of your views. Under the hood they're plain Python dataclasses: every attribute you pass to a field constructor becomes a dataclass field, and every field type subclasses `BaseField`, so you can inspect it, subclass it, or instantiate it directly.

## Common attributes

Every field type inherits this set of configuration attributes from `BaseField`.

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | **Required** | The attribute name on your model. |
| `label` | `str | None` | Title-cased `name` | The column header and form label. |
| `help_text` | `str | None` | `None` | Hint text shown below the form input. |
| `required` | `bool` | `False` | Requires a value in forms, on both the client and the server. |
| `validators` | `list[Validator]` | `[]` | Server-side validators run against the submitted value. See [Validation](#validation). |
| `disabled` | `bool` | `False` | Greys out and locks the input in forms. |
| `read_only` | `bool` | `False` | Shows the field but blocks edits. |
| `default` | `Any | Callable` | `None` | The prefill value on the create form. |
| `getter` | `Callable | None` | `None` | Replaces the model attribute lookup when reading the value. See [Computing, formatting, and parsing values](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Per-action display formatting, which replaces serialization for that action. See [Computing, formatting, and parsing values](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Per-action input parsing, which replaces the field's default parsing. See [Computing, formatting, and parsing values](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Included when the `q` search parameter matches. |
| `orderable` | `bool` | `True` | Adds a sort link in the list header. |
| `copy_to_clipboard` | `bool` | `False` | Adds a copy button next to the value on the detail page. |
| `filters` | `list | None` | `None` | Explicit override for the list page filters. |
| `extra` | `dict[str, Any]` | `{}` | A dictionary for your own metadata. |

### Visibility controls

Use these boolean flags, all `False` by default, to control where a field appears:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Defining defaults

The `default` attribute accepts a static value, a zero-argument callable, or a request-aware function:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Computing, formatting, and parsing values

Every field accepts three callable hooks, `getter`, `formatter`, and `parser`, that intercept and transform data as it moves between your model and the UI. Each accepts a synchronous or an asynchronous function.

#### `getter`: reading custom values

The `getter` hook replaces the default `getattr()` lookup when the field reads a model instance. The field calls `getter(request, obj)` and displays the return value.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Because `getter` values rarely map to a physical database column, they pair best with a read-only display. [`ComputedField`](#computedfield) is a built-in shortcut for that combination.

#### `formatter`: transforming display output

The `formatter` hook sets how a stored value renders on specific pages. It maps a `RequestAction`, such as `LIST`, `DETAIL`, or `EXPORT`, to a `(request, value) -> value` callable.

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

**Formatting behavior to keep in mind:**

* **Nulls reach the formatter:** Unlike default serialization, formatters receive `None` values, so you can supply fallback text, such as `"unset"` above.
* **Serialization is bypassed:** A matched formatter replaces the field's `serialize_value` and `serialize_none_value` methods. The return value is used as is, so the formatter is fully responsible for the final output.
* **JSON requirement:** Values returned for the `LIST` and `RELATION_LOOKUP` actions must stay JSON serializable.

#### `parser`: processing incoming data

The `parser` hook overrides the field's default parsing of submitted or imported data. It maps a `RequestAction` to a `(request, raw) -> value` callable.

* **Forms (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` is the submitted form input, or a list when `multiple=True`.
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

After parsing, the returned value goes through the standard validation chain, `required` and then `validators`, exactly as if the field had parsed the data itself.

!!! tip "Hooks or a subclass?"
    For a one-off customization on a single field, you rarely need a subclass. Pass these hooks as constructor arguments to handle reading, display formatting, and input parsing. [Subclass the field](../advanced/custom-fields.md) when you reuse the logic across views, or when you need to change the HTML rendering templates.

### Validation

Server-side validation runs on every field when a create or edit form is submitted, so bad data never reaches the database.

The lifecycle is fixed:

1. **Empty values:** When a submitted value is empty, such as `None`, `""`, or an empty collection, only the `required` flag is checked. The validators are skipped.
2. **Populated values:** When data is present, each callable in the `validators` list runs in order against the parsed value.

#### Validator signature

A validator receives four arguments: `(request, field, value, form_values)`.

* **`request`:** The current Starlette request object.
* **`field`:** The field instance being validated.
* **`value`:** The parsed value submitted for this field.
* **`form_values`:** A dictionary of all parsed form data, keyed by field name, so you can inspect other fields.

To reject a value, raise a `ValueError`. The admin catches the first error for a field, skips that field's remaining validators, and collects all errors to display next to their inputs.

#### Built-in validators

The [`starlette_admin.validators`](../api/validators.md) module provides standard rules:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Custom and asynchronous validation

Write custom validators as synchronous or asynchronous functions. They receive the `request`, so they can query the database to check complex constraints.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

With the `form_values` argument, a field-level validator can also enforce a rule that depends on another submitted field.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Context-specific validation rules

* **Relation fields:** `HasOne` and `HasMany` receive the primary keys of the related records during validation.
* **File fields:** Validation runs once per `UploadFile` in the payload. See [File & media fields](#file-media-fields).
* **Cross-field validation:** Use `form_values` for a simple dependency. For a rule that spans the whole form, override the `validate()` method on your view instead. View-level validation runs only after every field clears its own validation chain.

### Storing custom metadata

`extra` is a plain `dict` that `starlette-admin` never reads or writes. Use it to attach your own data to a field instance, for a custom template, a hook in your [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) subclass, or any other integration point, without subclassing the field:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Text fields

### StringField & TextAreaField

`StringField` renders a single-line text input for short content. `TextAreaField` extends it with a `<textarea>` element for long, multi-line text.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Extra attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `maxlength` and `minlength` | `int | None` | `None` | HTML length constraints. |
| `placeholder` | `str | None` | `None` | Input placeholder text. |
| `rows` *(TextArea only)* | `int` | `6` | Number of visible text lines. |

### TinyMCEEditorField

Extends `TextAreaField` with a WYSIWYG editor from the TinyMCE library. It requires the `tinymce` extra package.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    The `height`, `menubar`, `statusbar`, and `toolbar` attributes control the editor's UI. Pass any other native TinyMCE configuration through `extra_options`.

### Formatted text fields

These `StringField` variants render a matching HTML input type and format the value when the record is displayed.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField`, and `IPAddressField` each add a matching validator (`email`, `url`, `uuid`, and `ip_address` from [`starlette_admin.validators`](../api/validators.md)) when you leave `validators` empty. Pass your own `validators` to override it.

    `UUIDField` sets `copy_to_clipboard=True` by default. `IPAddressField` accepts `ipv4`, `True` by default, and `ipv6`, `False` by default, which control the address families its default validator accepts.

### PasswordField

Renders an `<input type="password">` element on forms to obscure what the user types.

!!! danger
    `PasswordField` masks the input on create and edit forms only. It doesn't override the display templates, so values render as **plain text** on list and detail pages, and it logs raw submitted values at `DEBUG` level.

    Set `exclude_from_list = True` and `exclude_from_detail = True` on password fields, and turn off `DEBUG` logging in production.

## Numeric fields

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

| Extra attribute | Applies to | Description |
| --- | --- | --- |
| `min` and `max` | Integer, Decimal | Minimum and maximum allowed values. |
| `step` | Integer, Decimal | The increment step constraint. |

!!! note
    `FloatField` works differently: it renders as a plain text input, coerces the submission to a `float`, and doesn't support `min`, `max`, or `step`.

## Date & time fields

These fields use the native browser date and time pickers, backed by the matching standard library types (`datetime.date`, `datetime.datetime`, and `datetime.time`).

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

| Extra attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel display format: `"short"`, `"medium"`, `"long"`, `"full"`, or a custom pattern. |
| `search_format` | `str | None` | ORM-specific | Format used to build database search queries. |

!!! note
    When timezone support is on, `DateTimeField` converts between the display timezone and the database timezone for you.

### ArrowField

A `DateTimeField` variant backed by an `Arrow` object. Outside edit forms, it displays a humanized relative time, such as "3 hours ago". It requires the `arrow` package.

## Selection & collection fields

### EnumField

The general-purpose select field. It renders a `<select>` dropdown, or a `select2` multi-select when `multiple=True`. Back it with a Python `Enum` subclass, a list of tuples, or choices loaded at request time.

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

| Extra attribute | Type | Description |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Build choices from a Python `Enum` class. |
| `choices` | `Sequence | None` | Static `(value, label)` pairs, or bare values. |
| `choices_loader` | `Callable | None` | Compute choices per request. |
| `multiple` | `bool` | Turns on multi-select and stores values as a list. |

!!! important
    Provide exactly one of `enum`, `choices`, or `choices_loader`.

`TimeZoneField`, `CountryField`, and `CurrencyField` are `EnumField` subclasses backed by Babel locale data, which needs the `i18n` extra. They localize their labels to the current request.

### TagsField

A free-text tagging input built on `select2`. It stores a `list[str]` and needs no predefined choices.

### ListField

Wraps another field to store an ordered list of values of that type. It renders as repeatable rows with add and remove controls. The wrapped field's name becomes the `ListField`'s name.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Groups several subfields into one nested object. Use it for embedded or struct-like data, such as a MongoDB embedded document.

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

## Specialized fields

### JSONField

Renders a JSON tree and code editor, and stores a Python `dict`. Pass a standard JSON Schema dictionary to `validation_schema` for client-side feedback.

### SlugField

A `StringField` variant that fills itself in on the client from another field's input. A manual edit stops the auto-fill.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` is required and must point to another field on the same form. The generated slug is submitted and stored like any other string.

### ComputedField

A read-only, virtual field derived from the model instance at display time, with no database column behind it. It builds on the [`getter` hook](#computing-formatting-and-parsing-values) that every field has, and adds the defaults a virtual column needs: excluded from create forms, read-only, non-searchable, and non-orderable.

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

For complex or reusable logic, subclass `ComputedField` and override `parse_obj()` instead of passing an inline `getter`:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` and `parse_obj` do the same job: use `getter` for short expressions, and subclass `ComputedField` when the logic spans several lines or is reused across views. On edit forms, the field still appears as plain-text display, so the user sees the current computed value.

Every `ComputedField` subclass keeps `StringField` rendering. To compute a value that should render as another type, such as a date, a badge, or an image, set `getter=` on that field type directly, along with the matching `read_only` and `exclude_from_*` flags.

## File & media fields

`FileField` renders a file upload input, and `ImageField` adds an image preview and a validity check. Attach a `storage=` backend to save uploads automatically and store a JSON `FileInfo` dictionary in the database. For the full configuration, see the [File Storage guide](file-storage.md).

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

| Extra attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Comma-separated list of accepted file extensions or MIME types, passed to the HTML `accept` attribute. |
| `multiple` | `bool` | `False` | Accepts several files in one field. |
| `storage` | `BaseStorage | None` | `None` | Storage backend that saves the uploads. Without it, the field hands raw uploads to your backend. |
| `upload_folder` | `str` | `""` | The storage-relative folder for saved files. |
| `max_size` | `int | None` | `None` | Maximum accepted upload size, in bytes. |
| `validators` | `list[Validator]` | `[]` | Custom validators, each called as `(request, field, upload)` once per uploaded file, after the `accept` and `max_size` checks. Raise `ValueError` to reject. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | `ImageField` only. When set, Pillow generates a bounded thumbnail at save time, and the list page uses it in place of the full image. |

!!! note
    `ImageField` prepends a Pillow-based image validity check to the `validators` list. When Pillow is installed and storage is configured, it also records `width` and `height` in the resulting `FileInfo`.

With `thumbnail_size` set, the admin generates a thumbnail alongside the full image, preserving the aspect ratio and never upscaling, and stores it under its own key. For example, `covers/cat.jpg` gets a `covers/cat.thumb.jpg` sibling. The list page uses the thumbnail automatically. Rows without one, from pre-existing data or because `thumbnail_size` is unset, fall back to the full image. A thumbnail generation failure is logged and never fails the upload.

The detail page opens every `ImageField` image in a lightbox, so viewers can page through full-resolution images. Images that belong to the same field (`multiple=True`) are grouped into one gallery.

See [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) for a complete runnable app, including a custom MIME-type validator.

### Without a storage

With no `storage=` attached, the field hands uploads to your backend raw instead of saving them:

* **In create and edit forms**, the parsed value is a tuple, `(UploadFile | list[UploadFile] | None, bool)`. The first element is the raw Starlette `UploadFile`, a list when `multiple=True`, or `None` when the user selected nothing. The second element is `True` when the user selects the delete box on the edit form, which means they want the existing file removed without a replacement. Your backend's `create()` and `edit()` logic stores the upload and honors the delete flag.
* **On list and detail pages**, the field expects the value to expose three keys, as a `dict`, or three attributes, as an object: `url`, required, the link target; `filename`, the display label; and `content_type`, which selects the file-type icon.

This contract is how the ORM integrations below plug their own file handling into the same field.

### ORM-native file columns

**MongoEngine** supports `mongoengine.FileField` and `mongoengine.ImageField` out of the box, with **GridFS** as the storage. The admin uploads to, serves from, and deletes files in GridFS for you. You need no `storage=` configuration: list the field by name.

**SQLAlchemy** gets the same treatment through [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Declare its `FileField` or `ImageField` column types on your models, and `starlette-admin` detects them, renders the matching admin field, and registers a route to serve the stored files. You configure storage through sqlalchemy-file's own `StorageManager`, backed by Apache Libcloud containers, and uploads join the session transaction, so a rolled-back session discards the stored file.

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

See [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) for a full app with several storages, content-type validation, and `multiple=True` fields.

## HasOne & HasMany

Relational fields that render as `select2` inputs, backed by the related view's search endpoint.

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

The `key` parameter points to the matching `ModelView`. Register both views on the same `Admin` instance so the keys resolve.

---

## What's next

* [Filters](filters.md): Customize the filter builder on your list pages.
* [File Storage](file-storage.md): Configure storage backends for `FileField` and `ImageField`.
* [Custom Fields](../advanced/custom-fields.md): Build a custom field.
