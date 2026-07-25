# Filters

Every field on a list page can have its own set of filter operators, like `contains`, `between`, `is null`, and more. Your users can combine these into a nested `AND`/`OR` tree without you having to write a single complex database query.

The set of available filters is automatically derived from the field's underlying type. You can easily narrow, extend, or fully replace that set for any specific field.

![Filters example](../../assets/images/filters.png)

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

See [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) for a runnable app covering default filters, per-field overrides, and a custom `BaseFilter` subclass.

Every field listed in `searchable_fields` automatically gets a **Filters** dropdown in the list toolbar. From there, the user can combine any number of filters to find exactly what they need.

## How the filter builder works

Clicking the **Filters** button opens a dropdown form where users can build their queries:

* **Add filter**: Adds a new condition row. You select a field, choose an operator (populated based on that field's available filters), and provide the value. The input adapts automatically. For example, it shows a plain text box for `contains`, two boxes for `between`, or no input at all for `is null`.
* **Add group**: Nests a sub-form with its own `AND`/`OR` selector. This is perfect for building complex conditions like `A AND (B OR C)`.
* **Match all/any of the following**: This selector at the top sets whether the current level uses `AND` or `OR` logic.
* **Apply filters**: Submits the form as a `GET` request. The entire filter tree is serialized into a single `filter` query parameter. You can read more about this in the [The filter URL format](#the-filter-url-format) section below.
* **Active filters**: Each active filter appears as a removable pill above the table. Clicking the `×` re-submits the list with just that specific rule dropped. A nested group collapses into a single pill that can be removed as a whole.

!!! tip
    Because the entire filter state lives in the URL, a filtered list is completely shareable. Your users can bookmark the page and share the link.

## Overriding filters for a specific field

Sometimes the default filters are too broad, or you need something highly specific. You can pass the `filters=` argument to any field to completely replace its default set.

You can narrow the list to only the operators that matter, extend it with a custom filter, or add extra operators to a field that defaults to basic null-checks, like `TagsField`:

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

!!! info "Backend-Specific Imports"
    The filter classes passed to `filters=` must be the concrete implementations for your specific database backend (`starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`, or `.tortoise.filters`). Make sure you import from your backend's `filters` module, not from `starlette_admin.filters` directly.

## The filter URL format

The filter builder serializes its state into the `filter` query parameter as a compact string.

It uses the format `field__operator` for a filter without values, `field__operator=value` for a single value, and `field__operator=value..value2` for a two-value filter like `between`. Multiple rules are joined with `AND` or `OR`, and parentheses are used to nest a group:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

If a value contains a space or a parenthesis, it must be wrapped in quotes: `name__eq="quoted value"`. A list value for a multi-select filter like `is one of` is simply comma-separated and does not need quotes: `status__in=ACTIVE,OUT_OF_STOCK`.

If the URL contains an invalid `filter` string, such as an unknown field, an unavailable operator, or an unparseable value, the application returns an `HTTP 400` error rather than silently dropping part of your condition.

!!! warning
    Only fields explicitly listed in `searchable_fields` (or every field, if left unset) will receive filters.


## Built-in filter reference

Here is every filter available out of the box. The table outlines the URL slug you will see in a bookmarked link and the kind of value it expects. Filters marked "two values" require both a `value` and a `value2` in the URL (for example, `between=2026-01-01..2026-01-31`).

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

If you need a filter for a data type the built-ins do not cover, like a JSON field, or a geo-point, check out [Custom Filters](../advanced/custom-filters.md) to learn how to write a `BaseFilter` subclass and register it globally or per field instance.

---

**What's next**

* [Custom Filters](../advanced/custom-filters.md): Write and register a `BaseFilter` subclass.
* [Actions](actions.md): Add bulk and row actions to your list pages.
* [Views](views.md): Learn more about `searchable_fields` and the rest of the list-page configuration.
