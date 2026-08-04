---
title: Custom Fields
description: Learn how to create custom field types in starlette-admin to handle specialized data types and custom UI widgets.
---

# Custom Fields

The built-in fields cover most columns you'll meet, but when none of them fit, you can build your own by subclassing [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). A field is three methods that move data between your model and the browser, plus a set of template paths that render it. Subclass `BaseField` directly, or extend the built-in field closest to what you need (such as `StringField` or `EnumField`) and override only the parts that differ.

## Minimal example

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

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

Point your `Admin` instance at the templates directory, then use the field in your view:

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

Because `StatusBadgeField` subclasses `EnumField` rather than `BaseField`, it inherits `choices`, form validation against those choices, and the default `fields/form/enum.html` template for the create and edit forms. None of that needs to change, so the class only overrides the list and detail rendering attributes.

The rest of this page covers what to override when a field needs more than a template swap. For the full working code, along with a second field (`AvatarNameField`) that does override the data methods, see [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## The three data methods

| Method | Called when | Signature |
| --- | --- | --- |
| `parse_form_data` | A create/edit form is submitted | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Reading a value off a model instance for display | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Formatting a value for the frontend (list, detail, API, export) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` overrides none of them, because `EnumField` already parses the submitted value against `choices` and reads the raw string from `obj.status`. The badge is presentation on top of that string. Override these three methods when the value itself has to be computed or reshaped rather than re-rendered.

!!! tip "Hooks or subclassing"
    For a one-off change to a single field, you rarely need a subclass. Pass the [`getter`, `formatter`, and `parser` hooks](../user-guide/fields.md#computing-formatting-and-parsing-values) as constructor arguments instead, to handle reading, display formatting, and input parsing.
    **When to subclass:** only when you need the same logic in more than one view, or when you need to change the templates.

`parse_form_data` receives the raw `FormData` (from `starlette.datastructures`) from the request and returns the data that `view.create()` or `view.edit()` should receive for this field. The default implementation reads `form_data.get(self.id)` and returns it unchanged. Most fields only need to add type coercion:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` receives the model instance and returns the value to display. The default returns `getattr(obj, self.name, None)`. Override it for fields that don't map to a single model attribute, such as one that combines two columns. `AvatarNameField`, for example, combines a `name` string with the row's uploaded avatar:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` receives whatever `parse_obj` (or the ORM layer) produced and formats it for the current request. It's called separately for the list page, the detail page, the JSON API, and data exports, so branch on `request.state.action` when the shape has to differ by context. `AvatarNameField` needs the avatar image only on the list page and falls back to plain text everywhere else:

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    Whatever `serialize_value` returns for `RequestAction.LIST` and `RequestAction.RELATION_LOOKUP` goes straight into a JSON response, so it must be JSON-serializable.

## Template paths

Every field carries the template attributes below. Each one is a path the admin's Jinja2 loader resolves: it checks your `templates_dir` first, if you set one, then falls back to the built-in `starlette_admin/templates/` directory. See [Templates](templates.md) for the details.

| Attribute | Default | Rendered for |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Each row's column value on the list page |
| `detail_template` | `"fields/detail/text.html"` | The read-only detail page |
| `form_template` | `"fields/form/input.html"` | The create/edit form input |
| `null_template` | `"fields/detail/_null.html"` | List and detail pages when the value is `None` |
| `empty_template` | `"fields/detail/_empty.html"` | List and detail pages when the value is an empty list or tuple |

All five templates receive the `field` instance and the current `data` value. For `list_template` and `detail_template`, `data` is never `None` or empty, because those cases route to `null_template` or `empty_template` before the type-specific template is included. The `form_template` also receives `error` (the message from a `FormValidationError`, if one occurred) and `action` (`RequestAction.CREATE`, `RequestAction.EDIT`, or `RequestAction.INLINE_EDIT` when rendered inside the list page's [inline edit](../user-guide/inline-edit.md) popover). All three are form actions, so `action.is_form()` returns `True`. Field code that needs the form-value representation should branch on that rather than on `action == RequestAction.EDIT`.

Override `null_template` and `empty_template` when a missing value should look different from the default muted `-null-` and `-empty-` labels, for example an empty-state icon or a "Not provided" badge that matches the field's own styling:

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

Because `null_template` and `empty_template` are plain field attributes like `list_template`, they're shared across list, detail, and any other view that renders this field, such as the inline table of a related view.

`StatusBadgeField` assigns the same template to both `list_template` and `detail_template`, because the same badge works in both contexts:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` overrides only `list_template`. The `data` variable in this template is the dictionary that `parse_obj` built and `serialize_value` reshaped, rather than a plain string:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

The `inline-edit-value` class is the opt-in marker for the [inline edit](../user-guide/inline-edit.md) underline. It's inert unless the field is inline-editable, so putting it on the name and not the avatar costs nothing here, while keeping the affordance correctly scoped if the field ever becomes editable.

Overriding `list_template` and `detail_template` while keeping the default `form_template` is exactly what `StatusBadgeField` does by extending `EnumField`. The default `fields/form/enum.html` renders a `<select>` dropdown populated from `field.choices`, so editing a status works with no further change.

## Registering with the converter registry

The `fields = [...]` list on a view accepts plain attribute names as well as field objects. Any item that isn't already a `BaseField` passes through a **converter registry** that maps the column type to a field class. Each ORM backend ships its own registry (`starlette_admin.contrib.sqla.converters.ModelConverter` and the equivalents for `beanie`, `mongoengine`, and `tortoise`), all built on the same base:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

The `@converts(*types)` decorator marks a method as the converter for one or more type keys. `BaseModelConverter.__init__` scans the instance for these decorated methods and builds its `converters` dictionary from them. For the SQLAlchemy backend, the type keys are the column type **names** (`"String"`, `"Integer"`, `"Enum"`, and so on), because SQLAlchemy has no single common base class across dialects.

Subclass the backend's converter to add your own mappings. This example routes every `Enum` column to `StatusBadgeField` instead of the default `EnumField`:

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

Pass the subclass to `ModelView(converter=...)` so the string field names in `fields = [...]` resolve through your converter instead of the default one:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

If you always construct fields explicitly, as in the minimal example above, you can skip the converter registry. You need it only when you want an entry like `fields = ["status"]` to produce a `StatusBadgeField` from the underlying column type.

---

## What's next

* **[Fields](../user-guide/fields.md):** The full built-in field reference and the `BaseField` attribute table.
* **[Templates](templates.md):** How the template loader resolves `list_template`, `detail_template`, `form_template`, `null_template`, and `empty_template`.
* **[Extension Points](extension-points.md):** Every other pluggable surface in `starlette-admin`.
