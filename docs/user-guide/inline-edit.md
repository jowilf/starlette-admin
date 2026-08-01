---
title: Inline Edit
description: Enable users to edit field values directly within the list view table for faster data entry.
---

# Inline Edit

Inline editing allows users to modify a single field directly from the list page. Clicking a cell opens a small popover, eliminating the need to navigate to the full edit form. Use this feature for quick, single-field updates like fixing a title, toggling a status, or adjusting a date. The interaction mirrors the familiar [x-editable](https://vitalets.github.io/x-editable/) pattern.

This feature is opt-in and disabled by default. Enabling it does not affect the standard edit page, which remains the primary interface for complex, multi-field edits.

> For a runnable example with inline editing, see [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Basic Usage

Declare the editable field names in the `inline_editable_fields` list:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

When enabled, editable cells display a dashed underline on the list page. Clicking a cell opens a popover with the field's standard form control, pre-filled with the current value.

The underline is not painted on the whole cell. Each list template places the `inline-edit-value` CSS class on the exact element to underline, and the style only activates inside an editable cell. All built-in list templates already carry the class. A custom `list_template` that should show the affordance must add the class itself:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Omitting the class keeps the cell fully clickable but renders it without the underline.

- **Save:** Click the check button or press <kbd>Enter</kbd> (for single-line inputs). This validates the field, persists the change, and refreshes the row without a page reload.
- **Cancel:** Click the <kbd>x</kbd> button or press <kbd>Esc</kbd> to discard changes.

## Configuration Rules

The application validates `inline_editable_fields` at startup to ensure misconfigurations fail fast. A `ValueError` is raised when a listed name meets any of the following conditions:

- Is not declared in `fields`.
- Is the primary key field.
- Is excluded from the list page (`exclude_from_list`) or the edit form (`exclude_from_edit`).
- Is a container or read-only field (`CollectionField`, `ListField`, `ComputedField`, `FileField`, or `ImageField`).sa

## Field Support

Every editable field renders the exact form widget it uses on the edit page. A field's specific JavaScript and CSS assets (like select2, flatpickr, JSONEditor, or TinyMCE) load on the list page only when that field is inline-editable. Views without inline edit keep their current lightweight page footprint.

| Field Type                                                                           | Supported | Popover Widget                      |
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

Inline editing reuses the existing permission model. The popover appears and accepts requests only when both `is_accessible(request)` and `can_edit(request)` return `True`. Overriding `can_edit` automatically secures inline edits:

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
- Other fields are bypassed. A save from the list page cannot overwrite a concurrent edit to a different field, and existing invalid data in other fields will not block the save.

The view's cross-field `validate` hook still runs, but the `data` dictionary contains only the edited field. Hooks expecting full-form submissions will raise a `KeyError` if they index missing keys directly. Use conditional checks to verify key presence:

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

On validation failure, the popover stays open with the submitted value intact. The edited field's message renders under the control, exactly as on the edit page. A message keyed to another field is prefixed with that field's label.

Detect an inline save inside a hook using `request.state.action == RequestAction.INLINE_EDIT`. This is useful for skipping flash messages intended for full page renders.

> **Warning**
> A validation rule keyed to a field that was not edited will not fire during an inline save. If a field's invariants depend on values the user cannot see or change from the list page, exclude it from `inline_editable_fields`.

---

## Lifecycle Hooks and Events

Inline saves route through the view's standard `edit()` path. The `before_edit`, `after_edit`, and `after_edit_committed` hooks fire normally, and the corresponding [events](../advanced/events.md) use the standard context types. However, the `data` and `old_data` payloads contain only the edited field to accurately reflect what the save touched.

To distinguish an inline save within an event listener, check `ctx.extra["inline"]`. This value is set to `True` for inline edits:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Custom Fields

Custom fields support inline editing automatically if they follow the standard `BaseField` contract. Because `RequestAction.INLINE_EDIT` is a form action, `action.is_form()` returns `True`. If your custom field code checks `action == RequestAction.EDIT` to generate a form-value representation, update it to use `action.is_form()` instead. This ensures the popover receives the correct representation. Review [Custom Fields](../advanced/custom-fields.md) for the complete field contract.
