---
title: Filters
description: Add complex nested AND/OR filtering capabilities to your admin views using type-aware query builders.
---

# Filters

Every field on a list page can have its own set of filter operators, such as `contains`, `between`, and `is null`. Your users combine these operators into a nested `AND`/`OR` tree, and you never write a complex database query.

The admin derives the available filters from the field's underlying type. You can narrow, extend, or fully replace that set for any field.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

See [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) for a runnable app that covers default filters, per-field overrides, and a custom `BaseFilter` subclass.

Every field you list in `searchable_fields` gets a **Filters** dropdown in the list toolbar. From there, users combine any number of filters to find the rows they need.

## How the filter builder works

Selecting the **Filters** button opens a dropdown form where users build their queries:

* **Add filter**: Adds a condition row. The user picks a field, chooses an operator from that field's available filters, and provides a value. The input adapts to the operator: a plain text box for `contains`, two boxes for `between`, and no input at all for `is null`.
* **Add group**: Nests a subform with its own `AND`/`OR` selector. Use it to build conditions like `A AND (B OR C)`.
* **Match all/any of the following**: Sets whether the current level uses `AND` or `OR` logic.
* **Apply filters**: Submits the form as a `GET` request. The admin serializes the whole filter tree into a single `filter` query parameter, described in [The filter URL format](#the-filter-url-format).
* **Active filters**: Each active filter appears as a removable pill above the table. Selecting the `×` resubmits the list with that rule dropped. A nested group collapses into a single pill that users remove as a whole.

!!! tip
    Because the whole filter state lives in the URL, a filtered list is shareable. Your users can bookmark the page and send the link to a colleague.

## Overriding filters for a specific field

When the default filters are too broad, or you need something more specific, pass the `filters=` argument to a field to replace its default set.

You can narrow the list to the operators that matter, extend it with a custom filter, or add operators to a field that defaults to basic null checks, such as `TagsField`:

```python
from enum import Enum

from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import ModelView

# Import the concrete filter implementations for your specific backend
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    NumericEqualFilter,
)


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductView(ModelView):
    fields = [
        "id",
        StringField("name"),  # Uses the default filter set, no override needed
        EnumField("status", enum=ProductStatus),  # Uses the default filter set
        DecimalField(
            "price",
            # Narrowed down to just 3 of the 9 default numeric filters
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Import filters from your backend"
    The filter classes you pass to `filters=` must be the concrete implementations for your database backend: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`, or `.tortoise.filters`. Import from your backend's `filters` module, not from `starlette_admin.filters`.

## The filter URL format

The filter builder serializes its state into the `filter` query parameter as a compact string.

The format is `field__operator` for a filter without values, `field__operator=value` for a single value, and `field__operator=value..value2` for a two-value filter such as `between`. Rules are joined with `AND` or `OR`, and parentheses nest a group:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Wrap a value in quotes when it contains a space or a parenthesis: `name__eq="quoted value"`. A list value for a multi-select filter such as `is one of` is comma-separated and needs no quotes: `status__in=ACTIVE,OUT_OF_STOCK`.

When the URL contains an invalid `filter` string, such as an unknown field, an unavailable operator, or an unparseable value, the application returns an `HTTP 400` error instead of silently dropping part of the condition.

!!! important
    Only the fields you list in `searchable_fields` receive filters. If you leave `searchable_fields` unset, every field receives them.


## Built-in filter reference

The following table lists every filter available out of the box, the URL slug you see in a bookmarked link, and the kind of value each one expects. Filters marked "two values" need both a `value` and a `value2` in the URL, for example `between=2026-01-01..2026-01-31`.

| Filter | Slug | Value type | Two values? |
| --- | --- | --- | --- |
| Contains | `contains` | text |  |
| Does not contain | `not_contains` | text |  |
| Starts with | `startswith` | text |  |
| Ends with | `endswith` | text |  |
| Equal | `eq` | text, number, date, datetime, or time |  |
| Not equal | `neq` | text or number |  |
| Is null | `is_null` | *(none)* |  |
| Is not null | `is_not_null` | *(none)* |  |
| Greater than | `gt` | number |  |
| Less than | `lt` | number |  |
| Greater than or equal | `gte` | number |  |
| Less than or equal | `lte` | number |  |
| Between | `between` | number, date, datetime, or time | ✓ |
| Is in the past | `in_past` | *(none)* |  |
| Is in the future | `in_future` | *(none)* |  |
| Is true | `is_true` | *(none)* |  |
| Is false | `is_false` | *(none)* |  |
| Is one of | `in` | comma-separated list |  |
| Is not one of | `not_in` | comma-separated list |  |

If you need a filter for a data type the built-ins don't cover, such as a JSON field or a geo-point, see [Custom Filters](../advanced/custom-filters.md) to write a `BaseFilter` subclass and register it globally or per field instance.

---

**What's next**

* **[Custom Filters](../advanced/custom-filters.md):** Write and register a `BaseFilter` subclass.
* **[Actions](actions.md):** Add bulk and row actions to your list pages.
* **[Views](views.md):** Learn more about `searchable_fields` and the rest of the list-page configuration.
