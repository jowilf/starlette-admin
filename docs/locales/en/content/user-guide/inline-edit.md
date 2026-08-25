---
title: Inline Edit
description: Enable users to edit field values directly within the list view table for faster data entry.
---

# Inline Edit

Inline editing lets users change a single field straight from the list page. Selecting a cell opens a small popover, so nobody has to open the full edit form. Use it for quick, single-field updates: fixing a title, toggling a status, or adjusting a date. The interaction follows the familiar [x-editable](https://vitalets.github.io/x-editable/) pattern.

The feature is opt-in and off by default. Turning it on doesn't change the standard edit page, which stays the main interface for complex, multi-field edits.

> For a runnable example with inline editing, see [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Basic usage

Declare the editable field names in the `inline_editable_fields` list:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Editable cells then show a dashed underline on the list page. Selecting a cell opens a popover with the field's standard form control, prefilled with the current value.

The underline isn't painted on the whole cell. Each list template puts the `inline-edit-value` CSS class on the exact element to underline, and the style applies only inside an editable cell. All built-in list templates already carry the class. If you write a custom `list_template` and want the same affordance, add the class yourself:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Without the class, the cell still opens the popover, but it renders no underline.

- **Save:** Select the check button or press <kbd>Enter</kbd> in a single-line input. The admin validates the field, saves the change, and refreshes the row without reloading the page.
- **Cancel:** Select the <kbd>x</kbd> button or press <kbd>Esc</kbd> to discard the change.

## Configuration rules

The application validates `inline_editable_fields` at startup so misconfigurations fail fast. A listed name raises a `ValueError` when it meets any of these conditions:

- It isn't declared in `fields`.
- It's the primary key field.
- It's excluded from the list page (`exclude_from_list`) or the edit form (`exclude_from_edit`).
- It's a container or read-only field: `CollectionField`, `ListField`, `ComputedField`, `FileField`, or `ImageField`.

## Field support

Every editable field renders the same form widget it uses on the edit page. A field's JavaScript and CSS assets, such as select2, flatpickr, JSONEditor, or TinyMCE, load on the list page only when that field is inline-editable. Views without inline edit keep their current lightweight page footprint.

| Field type                                                                           | Supported | Popover widget                      |
| ------------------------------------------------------------------------------------ | --------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Yes       | Plain input                         |
| `SlugField`                                                                          | Yes       | Plain input (source field excluded) |
| `TextAreaField`                                                                      | Yes       | Textarea                            |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Yes       | Number input                        |
| `BooleanField`                                                                       | Yes       | Toggle                              |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Yes       | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Yes       | select2 or native select            |
| `TagsField`                                                                          | Yes       | select2 tags                        |
| `JSONField`                                                                          | Yes       | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | Yes       | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | Yes       | select2 with async lookup           |
| `FileField`, `ImageField`                                                            | No        | None (requires edit page)           |
| `CollectionField`, `ListField`, `ComputedField`                                      | No        | None (read-only containers)         |

---

## Permissions

Inline editing reuses the existing permission model. The popover appears, and the admin accepts the request, only when both `is_accessible(request)` and `can_edit(request)` return `True`. Overriding `can_edit` therefore secures inline edits too:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Also disables inline edit when False
        return "edit:post" in request.state.admin_user.roles
```

---

## Validation

An inline save validates and writes only the edited field.

- The field's `required` check and `validators` chain run exactly as they do on the edit page.
- Other fields are skipped. A save from the list page can't overwrite a concurrent edit to a different field, and invalid data in another field doesn't block the save.

The view's cross-field `validate` hook still runs, but the `data` dictionary holds only the edited field. A hook that expects a full form submission raises a `KeyError` if it indexes missing keys directly, so check that a key is present first:

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

When validation fails, the popover stays open with the submitted value intact. The edited field's message renders under the control, exactly as on the edit page. A message keyed to another field is prefixed with that field's label.

To detect an inline save inside a hook, check `request.state.action == RequestAction.INLINE_EDIT`. Use it to skip flash messages meant for full page renders.

!!! warning
    A validation rule keyed to a field the user didn't edit doesn't run during an inline save. If a field's invariants depend on values the user can't see or change from the list page, leave that field out of `inline_editable_fields`.

---

## Lifecycle hooks and events

Inline saves go through the view's standard `edit()` path. The `before_edit`, `after_edit`, and `after_edit_committed` hooks fire as usual, and the matching [events](../advanced/events.md) use the standard context types. The `data` and `old_data` payloads contain only the edited field, so they reflect exactly what the save touched.

To tell an inline save apart inside an event listener, check `ctx.extra["inline"]`, which is `True` for inline edits:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Custom fields

Custom fields support inline editing automatically when they follow the standard `BaseField` contract. Because `RequestAction.INLINE_EDIT` is a form action, `action.is_form()` returns `True`. If your custom field checks `action == RequestAction.EDIT` to build a form-value representation, change it to use `action.is_form()` so the popover receives the right representation. For the complete field contract, see [Custom Fields](../advanced/custom-fields.md).
