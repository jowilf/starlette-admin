# Custom filters

Subclassing `BaseFilter` allows you to introduce custom operators beyond the built-in set. You can implement domain-specific checks like "_is divisible by_", create computed conditions like "_created this month_", or add support for field types the default registry omits. This guide explains the internal mechanics of custom filters and details the two methods for registering them: subclassing your backend's `FilterRegistry` to apply a filter across all matching field types, or passing the filter directly to a specific field's `filters=` list. For standard implementation details, including default filters per field type, manual overrides, and URL formatting, refer to the [Filters guide](../user-guide/filters.md).

## The `BaseFilter` interface

Every filter, whether built-in or custom, implements two methods:

```python
from typing import Any
from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


class MyFilter(BaseFilter):
    name = "my_filter"
    label = "My filter"
    data_type = FilterDataType.STRING

    def parse_value(self, raw: str) -> Any:
        """Convert the raw string from the URL into the value apply() expects.

        Raise FilterValidationError if the value isn't acceptable.
        """
        return raw

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Return a query fragment for this filter's condition."""
        raise NotImplementedError()
```

* **`parse_value(raw)`** converts the raw URL string into the data type required by `apply()`, such as a `Decimal`, a `date`, or a list. The default implementation passes the string through unchanged. This behavior is suitable for `STRING` or `ENUM` filters but must be overridden for numeric or temporal data. This method also serves as a validation hook. You should raise `FilterValidationError` for values that parse correctly but are otherwise unacceptable (such as out-of-range or malformed inputs).
* **`apply(ctx)`** is the only abstract method. It receives a `FilterApplyContext` object containing the `query`, `field_name`, `value`, `value2`, `request`, and `view`. The method must return a query fragment specific to your backend.

## How raw URL values get parsed

All URL parameters are strings. For example, `price__gt=50` and `created_at__eq=2026-01-01` both arrive at the server as raw text. Before a filter's `apply()` method executes, its `parse_value()` method converts that raw string into a Python object matching its defined `data_type`:

```python
def _parse_number(raw: Any) -> int | float:
    text = str(raw).strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise FilterValidationError(f"{raw!r} is not a valid number") from None


class GreaterThanFilter(BaseFilter):
    name = "gt"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)
```

As a result, parameters like `?filter=price__gt=50` and `?filter=price__gt=50.5` reach `GreaterThanFilter.apply()` as converted Python numbers (`50` as an `int`, and `50.5` as a `float`) instead of the literal strings `"50"` and `"50.5"`. The `apply()` method passes this parsed value directly to the query object. The database driver handles the final coercion against the column's actual database type (such as `Decimal` or `Numeric`).

| `data_type` | Example raw URL value | Parsed Python value | Parsed by |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (tries `int()`, falls back to `float()`) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal` using `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal` using `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal` using `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (splits on unquoted commas) |
| `string`, `enum` | `admin` | `"admin"` | `BaseFilter.parse_value` default (passed through unchanged) |
| `none` | *(no value in the URL at all)* | *(never called)* | N/A |

If a value fails to parse (for example, `price__gt=abc` or `created_at__eq=not-a-date`), `parse_value()` raises a `FilterValidationError`. The request handler catches this exception and returns an `HTTP 400` error before executing any database queries:

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

Value-less filters (where `data_type=none`, such as `is_null`, `is_true`, or `in_past`) skip this step entirely. The `parse_value` method never runs for these filters. This explains why `field__is_null` requires no `=value` in the URL, as there is no input string to convert.

## Making a custom filter available

There are two ways to register a custom filter with a view. Choose the method that best matches your intended scope.

### Per field instance (narrow scope)

Pass the custom filter into the target field's `filters=` list. You can provide it alongside or instead of the defaults. See [Overriding filters for a specific field](../user-guide/filters.md#overriding-filters-for-a-specific-field) for the base pattern using built-in filters. Use this approach when the filter is highly specific and only applies to a single field.

### Registry-wide (every matching field type)

Each backend includes a `FilterRegistry` subclass. Examples include `SqlaFilterRegistry` for SQLAlchemy, `BeanieFilterRegistry` for Beanie, and `MongoEngineFilterRegistry` for MongoEngine. These classes contain methods decorated with `@filters(FieldType, ...)` to define default filters for each supported field type:

```python
# starlette_admin/contrib/sqla/filters.py
class SqlaFilterRegistry(FilterRegistry):
    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            EqualFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(NumberField, FloatField)
    def numeric_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            NumericEqualFilter,
            GreaterThanFilter,
            LessThanFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    # ... one method per field type
```

To modify the available filters for a field type across an entire view, create a subclass of the backend's registry. Override or add a `@filters` method, and then return an instance of your custom subclass from `get_filter_registry()`:

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

You can declare these methods in two ways, depending on whether you want to replace or extend the existing filters:

* **Override:** Re-declare `@filters(StringField)` on your subclass and return the exact classes you want to use. This entirely replaces the parent's default list. Be sure to include any built-in filters you want to retain.
* **Extend:** Declare `@filters(IntegerField)` when the parent registry only provides a broader `NumberField` registration. Because `IntegerField` is a subclass of `NumberField`, the Method Resolution Order (MRO) will resolve `IntegerField` to your new method. Meanwhile, `DecimalField` (another `NumberField` subclass without its own explicit registration) will continue inheriting the parent's `numeric_filters` method unchanged.

Since this is a standard Python subclass, no global state is mutated. Each call to `ProductFilterRegistry()` instantiates an independent registry. Your modifications remain scoped to the views that explicitly return this custom registry, leaving the backend defaults intact for all other views.

## Full SQLAlchemy example

The `DivisibleByFilter` in the example below takes a value: the divisor to check the column against. It is applied to every `IntegerField` on the `ProductView` via a `SqlaFilterRegistry` subclass, rather than being attached directly to individual fields:

```python
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from sqlalchemy import Integer, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.requests import Request
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.contrib.sqla.filters import SqlaFilterRegistry
from starlette_admin.fields import BaseField
from starlette_admin.filters import (
    BaseFilter,
    FilterApplyContext,
    FilterDataType,
    FilterRegistry,
    FilterValidationError,
    filters,
)

engine = create_engine(
    "sqlite:///product.db", connect_args={"check_same_thread": False}, echo=True
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    lot_size: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class DivisibleByFilter(BaseFilter):
    """
    Filters database rows where the column value is an exact multiple of a given divisor.
    """

    name = "divisible_by"
    label = "Is divisible by"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: str) -> int:
        """Validates and converts the raw admin UI input into an integer divisor."""
        try:
            divisor = int(raw)
        except ValueError:
            raise FilterValidationError(f"{raw!r} is not a valid integer") from None

        if divisor == 0:
            raise FilterValidationError("divisor must not be 0")

        return divisor

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Applies the modulus condition to the underlying SQLAlchemy query context."""
        column = getattr(ctx.view.model, ctx.field_name)
        return column % ctx.value == 0


class ProductFilterRegistry(SqlaFilterRegistry):
    """
    Custom filter registry that injects `DivisibleByFilter` into integer fields.

    By overriding `integer_filters`, this registry ensures that any IntegerField
    receives our custom divisibility filter in addition to the standard numeric defaults.
    Other numeric fields (like DecimalField) remain unaffected.
    """

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        "price",
        # Note: Passing just the string "lot_size" would also work, as SQLAlchemy's
        # default converter automatically maps integer columns to IntegerField.
        IntegerField("lot_size"),
    ]

    def get_filter_registry(self) -> FilterRegistry:
        """Binds the custom filter registry to this specific view."""
        return ProductFilterRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-product"))
admin.mount_to(app)
```

See [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) for a runnable app with a custom `BaseFilter` subclass registered the same way.

The `lot_size__divisible_by` option now appears as a filter for `IntegerField("lot_size")`. This happens automatically without needing an explicit `filters=` declaration on the field itself. For example, `lot_size__divisible_by=6` matches products whose lot size is a multiple of 6:

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

> **Tip**
> Use a `FilterRegistry` subclass when a filter is generic enough to apply to every field of a given type within a view. Use the per-field `filters=` approach when the logic is highly specific to a single field. See the [Filters guide](../user-guide/filters.md#overriding-filters-for-a-specific-field) for examples of the per-field pattern.

## Dynamic choices with `get_choices`

By default, a filter's value input follows its `data_type`: a plain text box for `STRING`, a number box for `NUMBER`, and so on. Override `get_choices(request)` when the value should instead come from a dropdown seeded with a per-request list of `(value, label)` pairs, for example an "is one of" filter over a relation field, where the value posted back is a foreign key but the picker should show a human-readable name.

`get_choices` receives the current `Request` and returns a sequence of `(value, label)` pairs, or `None` (the default) to leave the plain input in place. A non-empty result takes precedence over both the plain input and any choices the field itself supplies (as `EnumField` does).

The example below, from [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr), adds an "is one of" / "is not one of" pair to the `Employee` list's `department` field. `department` is a `RelationField`, so the default registry only gives it null-check filters; there is no generic way to compare a related row to a raw string. `get_choices` lists every `Department` by name for the dropdown, and `parse_value` converts the posted-back values to integers so `apply` can match on the `Department.id` foreign key directly, rather than joining through the relationship and comparing on name:

```python
# examples/advanced/07-hr/filters.py
from typing import Any

from models import Department, Employee
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin.filters.base import FilterApplyContext, FilterValidationError
from starlette_admin.filters.enum import InFilter, NotInFilter


class _DepartmentChoicesMixin:
    """Shared `get_choices`/`parse_value` for the two filters below: the
    filter builder's dropdown lists every department by name, and posts back
    the department's `id` rather than its name, so `apply` can match on the
    primary key instead of an `ilike` comparison.
    """

    def get_choices(self, request: Request) -> list[tuple[int, str]]:
        session: Session = request.state.session
        return list(
            session.execute(
                select(Department.id, Department.name).order_by(Department.name)
            ).all()
        )

    def parse_value(self, raw: Any) -> list[int]:
        values = super().parse_value(raw)  # type: ignore[misc]
        try:
            return [int(v) for v in values]
        except ValueError as err:
            raise FilterValidationError("Department id must be an integer") from err


class DepartmentInFilter(_DepartmentChoicesMixin, InFilter):
    """Employees in one of the selected departments."""

    name = "department_in"
    label = "is one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Employee.department_id.in_(ctx.value)


class DepartmentNotInFilter(_DepartmentChoicesMixin, NotInFilter):
    """Employees not in any of the selected departments"""

    name = "department_not_in"
    label = "is not one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return ~Employee.department_id.in_(ctx.value)
```

A few things to note about this pattern:

* **The mixin sits before the base filter class in the MRO.** `_DepartmentChoicesMixin` is listed first in `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)`, so its `get_choices` and `parse_value` override the ones each filter would otherwise inherit, while `super().parse_value(raw)` still reaches `InFilter.parse_value` to split the raw value into a list before it is converted to integers.
* **`get_choices` runs on every request**, not once at import time, so the dropdown always reflects the current rows. Here that means a newly added `Department` shows up in the filter builder immediately, with no server restart or cache to invalidate.
* **The `(value, label)` pairs and `parse_value`'s output type must agree.** The dropdown posts back whichever `value` the user picked, so `parse_value` has to convert it into what `apply` expects. `Department.id` is already an `int` here, so the mixin's `parse_value` simply reasserts that with a validation error on anything that isn't.
* **`InFilter`/`NotInFilter` already default to `data_type = FilterDataType.ENUM`** (a multi-select), so no `data_type` override is needed on either subclass. Overriding `get_choices` alone is enough to seed that multi-select with departments instead of leaving it empty.

---

## What's next

* **[Filters](../user-guide/filters.md):** Learn about default filters per field type, the URL format, and the `filters=` override.
* **[SQLAlchemy](../integrations/sqlalchemy.md):** Explore the SQLAlchemy backend used in this page's example.
* **[Extension points](extension-points.md):** View the complete list of methods you can override on `ModelView`.