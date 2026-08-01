---
title: Custom Fields
description: Learn how to create custom field types in starlette-admin to handle specialized data types and custom UI widgets.
---

# Custom Fields

While the built-in fields cover most columns you will encounter, you can create custom fields by subclassing [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). A field type primarily consists of three methods that transfer data between your model and the browser, alongside three template paths that handle rendering. You can subclass `BaseField` directly or extend an existing field that closely matches your requirements (such as `StringField` or `EnumField`), overriding only the necessary components.

## Minimal Example

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

Configure the templates directory in your `Admin` instance and apply the field within your view:

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

Because `StatusBadgeField` subclasses `EnumField` rather than `BaseField` directly, it inherits several features automatically. It retains `choices`, form validation against those choices, and the default `fields/form/enum.html` template for the create and edit forms. Since none of these require modification, the class only updates the list and detail rendering attributes.

The remainder of this guide explains how to override methods when a field requires more than a simple template swap. You can view the full working version of this code, along with a second field (`AvatarNameField`) that requires data-method overrides, in the [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields) directory.

## The Three Data Methods

| Method | Called when | Signature |
| --- | --- | --- |
| `parse_form_data` | A create/edit form is submitted | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Reading a value off a model instance for display | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Formatting a value for the frontend (list, detail, API, export) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` does not require these overrides because `EnumField` already parses the submitted value against `choices` and reads the raw string from `obj.status`. The badge acts purely as a presentation layer on top of that string. You should override these three methods when the value itself must be computed or reshaped instead of just being re-rendered.

!!! tip "Hooks vs. Subclassing"
    For a one-off customization on a single field, you rarely need a subclass. Instead, you can pass the [`getter`, `formatter`, and `parser` hooks](../user-guide/fields.md#computing-formatting-and-parsing-values) directly as constructor arguments to handle reading, display formatting, and input parsing.
    **When to subclass:** Create a subclass only if you need to reuse the logic across multiple views or modify the rendering templates.

`parse_form_data` receives the raw `FormData` (from `starlette.datastructures`) from the request and returns the data that `view.create()` or `view.edit()` should receive for this field. The default implementation reads `form_data.get(self.id)` and returns it unchanged. Most fields only need to add type coercion:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` receives the model instance and returns the value to display. The default behavior is to return `getattr(obj, self.name, None)`. Override this method for fields that do not map to a single model attribute, such as a field that combines two columns. For example, `AvatarNameField` combines a `name` string with the row's uploaded avatar:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` receives whatever data `parse_obj` (or the ORM layer) produced and formats it for the current request. It is called separately for the list page, the detail page, the JSON API, and data exports. You can branch your logic based on `request.state.action` when the data shape needs to differ across contexts. `AvatarNameField` only requires the avatar image on the list page; everywhere else it falls back to plain text:

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
    Whatever `serialize_value` returns for `RequestAction.LIST` and `RequestAction.RELATION_LOOKUP` is injected directly into a JSON response. You must return a JSON-serializable value.

## Template Paths

Every field contains three template attributes. Each attribute is a path resolved against the Jinja2 loader of the admin interface. This loader checks your custom `templates_dir` if provided, and otherwise falls back to the built-in `starlette_admin/templates/` directory (see [Templates](templates.md) for more details).

| Attribute | Default | Rendered for |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Each row's column value on the list page |
| `detail_template` | `"fields/detail/text.html"` | The read-only detail page |
| `form_template` | `"fields/form/input.html"` | The create/edit form input |
| `null_template` | `"fields/detail/_null.html"` | List and detail pages when the value is `None` |
| `empty_template` | `"fields/detail/_empty.html"` | List and detail pages when the value is an empty list or tuple |

All five templates receive the `field` instance and the current `data` value. The `data` value is never `None` or empty for `list_template` and `detail_template` because those conditions are routed to `null_template` or `empty_template` before the type-specific template is included. The `form_template` additionally receives `error` (the message from a `FormValidationError`, if one occurred) and `action` (`RequestAction.CREATE`, `RequestAction.EDIT`, or `RequestAction.INLINE_EDIT` when rendered inside the list page's [inline edit](../user-guide/inline-edit.md) popover). All three are form actions: `action.is_form()` returns `True`, and field code that needs the form-value representation should branch on it rather than on `action == RequestAction.EDIT`.

Override `null_template` and `empty_template` when a field's absence should look different from the default muted `-null-` / `-empty-` labels, such as an empty-state icon or a "Not provided" badge that matches the field's own styling:

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

Because `null_template` and `empty_template` are plain field attributes like `list_template`, they are shared across list, detail, and any other view that renders this field (such as the inline table of a related view).

`StatusBadgeField` assigns the same template to both `list_template` and `detail_template` because the badge design applies perfectly to both contexts:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` only overrides `list_template`. The `data` variable in this template is the dictionary constructed by `parse_obj` and reshaped by `serialize_value`, rather than a standard string:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

The `inline-edit-value` class is the opt-in marker for the [inline edit](../user-guide/inline-edit.md) underline. It is inert unless the field is inline-editable, so placing it on the name (and not the avatar) costs nothing here while keeping the affordance correctly scoped if the field ever becomes editable.

Overriding only `list_template` and `detail_template` while retaining the default `form_template` is the exact strategy `StatusBadgeField` uses by extending `EnumField`. The default `fields/form/enum.html` template automatically renders a `<select>` dropdown populated from `field.choices`. This requires no modifications to successfully edit a status.

## Registering With the Converter Registry

The `fields = [...]` list on a view accepts plain attribute names as well as instantiated field objects. Any item that is not already a `BaseField` passes through a **converter registry** that maps the column type to a specific field class. Each ORM backend provides its own registry (such as `starlette_admin.contrib.sqla.converters.ModelConverter` or the equivalents for `beanie`, `mongoengine`, and `tortoise`), which are all built on the same foundation:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

The `@converts(*types)` decorator marks a method as the converter for one or more type keys. The `BaseModelConverter.__init__` method scans the instance for these decorated methods to construct its `converters` dictionary. For the SQLAlchemy backend, the type keys are the column type **names** (such as `"String"`, `"Integer"`, or `"Enum"`) because SQLAlchemy lacks a single common base class across dialects.

You can subclass the backend's converter to add your own mappings. The following example routes every `Enum` column to `StatusBadgeField` instead of the default `EnumField`:

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

Supply the subclass to `ModelView(converter=...)` so that string field names defined in `fields = [...]` resolve through your custom converter rather than the default configuration:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

If you consistently construct fields explicitly rather than relying on name-based conversion (as demonstrated in the minimal example above), you can skip the converter registry entirely. The registry is only necessary when you want an entry like `fields = ["status"]` to automatically produce a `StatusBadgeField` based on the underlying column type.

---

**What's Next**

* [Fields](../user-guide/fields.md): The full built-in field reference and `BaseField` attribute table.
* [Templates](templates.md): A guide on how the template loader resolves `list_template`, `detail_template`, `form_template`, `null_template`, and `empty_template` paths.
* [Extension Points](extension-points.md): An overview of every other pluggable surface in starlette-admin.
