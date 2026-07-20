# Fields: details, validators, and custom field types

Fields are plain Python dataclasses; every constructor argument is a dataclass field. See the quick map in SKILL.md for the full catalog. This file covers the details that the map omits, server-side validators, and how to build custom fields.

## Attribute notes

- `default` accepts a static value, a zero-argument callable, or a request-aware callable: `StringField("locale", default=lambda request: request.state.admin_user.locale)`.
- `getter` is a sync or async `(request, obj) -> value` callable that overrides `parse_obj`'s default `getattr(obj, self.name, None)` lookup, on any field, with no subclassing needed.
- `formatter` is a `dict[RequestAction, (request, value) -> value]` (sync or async callables). When the current action has an entry, its callable replaces `serialize_value`/`serialize_none_value` entirely; its return value (`None` included) is used as the final output as-is.
- `parser` is a `dict[RequestAction, (request, raw) -> value]` (sync or async callables). When the current action has an entry, its callable replaces the field's default parsing entirely: `raw` is the submitted form value (a list when `multiple`) for CREATE/EDIT/INLINE_EDIT, or the unprocessed cell value for IMPORT. The result still goes through `required`/`validators`.
- `extra` is a free `dict` the framework never reads or writes; attach integration metadata without subclassing.
- Visibility flags per field: `exclude_from_list`, `exclude_from_detail`, `exclude_from_create`, `exclude_from_edit`, `exclude_from_export`, `exclude_from_import` (all default `False`). The view-level `exclude_fields_from_*` lists do the same by name.
- `FloatField` renders a plain text input coerced to float; it does not support `min`/`max`/`step` (use `IntegerField` or `DecimalField` for those).
- `SlugField(populate_from=...)` auto-fills client-side from another field on the same form; manual edits stop the auto-fill. `populate_from` is required.
- `ComputedField` is virtual and read-only: pass `getter=lambda request, obj: ...` or subclass and override `parse_obj(request, obj)`. Automatically excluded from create forms, non-editable, non-searchable, non-orderable.
- `EnumField(multiple=True)` renders a select2 multi-select and stores a list. `TimeZoneField`, `CountryField`, `CurrencyField` are `EnumField` subclasses backed by Babel data (i18n extra).
- `JSONField` renders a tree/code editor storing a `dict`; pass a JSON Schema to `validation_schema` for client-side feedback.
- `DateTimeField(output_format=...)` accepts Babel formats (`"short"`, `"medium"`, `"long"`, `"full"`, or custom) and converts timezones automatically when timezone support is enabled.
- `TinyMCEEditorField` (tinymce extra): `height`, `menubar`, `statusbar`, `toolbar`, plus any native TinyMCE config via `extra_options`.

## Validators

Every field accepts `validators=[...]`: sync or async callables `(request, field, value, form_values)` that raise `ValueError` to reject the value. They run on form submission after the built-in `required` check, in order, stopping at the first error; that error renders under the input, and errors across fields are aggregated into one response. Empty values (`None`, `""`, empty collections) are checked only against `required`, so validators never see missing input.

`form_values` is the full submitted data keyed by field name, parsed before validation started (relation fields hold primary keys, multi-value fields hold lists). Read it when a field's rule depends on another field's value. On EDIT it holds the submitted form; during inline saves it holds only the edited row's fields; on import it holds the parsed row.

Built-in factories in `starlette_admin.validators` (every factory accepts `message=` to override the error text):

| Factory | Rule |
| --- | --- |
| `length(min=, max=)` | `min <= len(value) <= max`; unset bounds are not checked |
| `number_range(min=, max=)` | numeric bounds; unset bounds are not checked |
| `regexp(pattern, flags=)` | value matches the pattern via `re.match` |
| `email(**options)` | valid email address via the email-validator package (`pip install starlette-admin[email]`); DNS/MX deliverability checks are off by default, pass `check_deliverability=True` to enable |
| `url(schemes=, max_length=)` | absolute URL with valid scheme and host; default schemes http/https/ftp/ftps, `schemes=None` accepts any |
| `uuid(version=)` | valid UUID, optionally of a specific version (1, 3, 4, or 5) |
| `ip_address(ipv4=True, ipv6=False)` | valid IP address in the enabled families |
| `any_of(values)` / `none_of(values)` | membership allow list / deny list |
| `file_size(max_size)` | upload no larger than `max_size` bytes |
| `file_type(accept)` | upload matches an HTML-file-input accept string (`".pdf"`, `"image/*"`, `"image/png,.svg"`) |
| `valid_image()` | upload passes Pillow image verification |

Rules and context:

- `EmailField`, `URLField`, `UUIDField`, and `IPAddressField` install their matching validator automatically when `validators` is empty; passing your own list replaces that default.
- Relation fields (`HasOne`/`HasMany`) validate primary keys; multi-value fields receive the whole list.
- `FileField`/`ImageField` run the chain once per `UploadFile`, after the field's own `max_size` and `accept` checks; `ImageField` prepends `valid_image()`.
- Validators receive the request, so they can query the database:

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")

StringField("slug", validators=[unique_slug])
```

A field validator can reach another field through `form_values`, which raises the error under its own field:

```python
def not_before_start(request, field, value, form_values):
    if form_values.get("start") and value < form_values["start"]:
        raise ValueError("End date must be after the start date")

DateField("end", validators=[not_before_start])
```

To reject across several fields at once, override the view's `validate(request, data)` and raise `FormValidationError({field_name: message})`; it runs only after every field passes its own chain. During inline saves `data` contains only the edited field, see [views.md](views.md).

## Custom fields

Subclass the closest existing field and override only what differs. Three data methods move values between model and browser; five template paths control rendering.

### Presentation-only customization (template swap)

```python
from dataclasses import dataclass
from dataclasses import field as dc_field
from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html
{# templates/employee/status_badge.html #}
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>
```

Point `Admin(templates_dir="templates/")` at the directory. Extending `EnumField` keeps `choices`, form validation, and the default select form template for free.

### Data methods

| Method | Called when | Default |
| --- | --- | --- |
| `parse_form_data(request, form_data)` | Form submitted | `form_data.get(self.id)` unchanged |
| `parse_obj(request, obj)` | Reading a value off a model instance | `getattr(obj, self.name, None)` |
| `serialize_value(request, value)` | Formatting for list, detail, API, export | passthrough |

Override them when the value must be computed or reshaped, not just re-rendered. Branch on `request.state.action` (a `RequestAction`) when the shape differs per context. Whatever `serialize_value` returns for `RequestAction.LIST` and `RequestAction.RELATION_LOOKUP` goes straight into a JSON response, so it must be JSON-serializable.

For the common cases, `getter=`, `formatter=`, and `parser=` (see Attribute notes above) cover computing, reshaping, and parsing a value without a subclass at all.

### Template attributes

| Attribute | Default | Context |
| --- | --- | --- |
| `list_template` | `fields/list/text.html` | List cell |
| `detail_template` | `fields/detail/text.html` | Detail row |
| `form_template` | `fields/form/input.html` | Create/edit input (also receives `error` and `action`) |
| `null_template` | `fields/detail/_null.html` | Value is `None` |
| `empty_template` | `fields/detail/_empty.html` | Value is an empty list/tuple |

All receive `field` and `data`. `data` is never None/empty in `list_template`/`detail_template`; those cases route to the null/empty templates first.

### Converter registry (string names to custom fields)

Needed only when `fields = ["status"]` should auto-resolve to your custom field. Subclass the backend converter and pass it to the view:

```python
from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts


class MyModelConverter(ModelConverter):
    @converts("Enum")   # sqla keys are column type NAMES: "String", "Integer", "Enum", ...
    def conv_enum(self, *args, **kwargs):
        _type = kwargs["type"]
        return StatusBadgeField(**self._field_common(*args, **kwargs), enum=_type.enum_class)


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Runnable example: `examples/advanced/05-custom-fields` (includes an `AvatarNameField` with data-method overrides).
