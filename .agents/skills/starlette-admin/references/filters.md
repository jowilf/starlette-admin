# Filters

Every field listed in `searchable_fields` (or every field when unset) gets a Filters dropdown on the list page. Users combine operators into nested AND/OR trees; the whole state serializes into the `filter` query parameter, so filtered lists are shareable URLs. Defaults derive from the field type (text fields get contains/startswith/eq/is_null, numbers get gt/lt/between, and so on).

## Overriding filters per field

Pass `filters=` on the field with concrete classes from YOUR backend's module (`starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`):

```python
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter, DateInPastFilter, DateTimeBetweenFilter,
    GreaterThanFilter, NumericEqualFilter,
)


class ProductView(ModelView):
    fields = [
        "id",
        "name",  # keeps default filter set
        DecimalField("price", filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter]),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

## Filter URL format

`field__operator` (no value), `field__operator=value`, `field__operator=value..value2` (two-value filters like between). Combine with `AND`/`OR` and parentheses:

```text
?filter=price__gt=50+AND+status__eq=ACTIVE
?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)
```

Quote values containing spaces or parentheses (`name__eq="quoted value"`). Multi-select lists are comma-separated without quotes (`status__in=ACTIVE,OUT_OF_STOCK`). Invalid filter strings return HTTP 400, never a silently narrowed query.

Built-in operator slugs: `contains`, `not_contains`, `startswith`, `endswith`, `eq`, `neq`, `is_null`, `is_not_null`, `gt`, `lt`, `gte`, `lte`, `between` (two values), `in_past`, `in_future`, `is_true`, `is_false`, `in`, `not_in`.

SQLAlchemy notes: `is_null` on a relationship evaluates `~column.has()` or `~column.any()`, not `IS NULL`. The sqla backend has no `ArrayInFilter`/`ArrayNotInFilter` for list-valued columns (Beanie and MongoEngine do); write a custom filter for that.

## Custom filters

Subclass `BaseFilter` and implement `apply()`; override `parse_value()` for anything non-string:

```python
from starlette_admin.filters import (
    BaseFilter, FilterApplyContext, FilterDataType, FilterValidationError, filters,
)


class DivisibleByFilter(BaseFilter):
    name = "divisible_by"
    label = "Is divisible by"
    data_type = FilterDataType.NUMBER   # NUMBER, STRING, ENUM, DATE, DATETIME, TIME, ARRAY, NONE

    def parse_value(self, raw: str) -> int:
        # Converts the raw URL string; raise FilterValidationError -> HTTP 400
        try:
            divisor = int(raw)
        except ValueError:
            raise FilterValidationError(f"{raw!r} is not a valid integer") from None
        if divisor == 0:
            raise FilterValidationError("divisor must not be 0")
        return divisor

    def apply(self, ctx: FilterApplyContext) -> Any:
        # ctx: query, field_name, value, value2, request, view
        column = getattr(ctx.view.model, ctx.field_name)
        return column % ctx.value == 0   # return a backend-native query fragment
```

`data_type=NONE` filters (like `is_null`) take no value and never call `parse_value`.

### Registering the filter

Narrow scope: add the class to a field's `filters=` list.

Registry-wide (every field of a type in a view): subclass the backend registry and return it from `get_filter_registry()`:

```python
from starlette_admin.contrib.sqla.filters import SqlaFilterRegistry


class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self):
        return ProductFilterRegistry()
```

Re-declaring an existing `@filters(...)` method replaces the parent's list entirely (include the built-ins you keep). Declaring a more specific type (`IntegerField` when the parent registers `NumberField`) extends via MRO without touching sibling types. No global state is mutated.

### Dropdown values with `get_choices`

Override `get_choices(request) -> list[tuple[value, label]] | None` when the filter input should be a dropdown seeded per request (for example an "is one of" filter over a relation, listing rows by name but posting back ids). A non-empty result overrides both the plain input and field-supplied choices. `InFilter`/`NotInFilter` already use `FilterDataType.ENUM` (multi-select), so subclassing them plus `get_choices` is enough. Keep `get_choices` output and `parse_value` output types in agreement. See `examples/advanced/07-hr/filters.py` for the full relation-filter pattern.

Runnable example: `examples/02-filters`.
