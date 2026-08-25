---
title: Custom Filters
description: Extend the built-in query builder by creating custom database filters and operators in starlette-admin.
---

# Custom filters

Subclass `BaseFilter` when you need an operator the built-in set doesn't cover: a domain-specific check like "_is divisible by_", a computed condition like "_created this month_", or support for a field type the default registry skips. This page explains how a filter works internally and shows the two ways to register one, either by subclassing your backend's `FilterRegistry` to cover every matching field type, or by passing the filter to a single field's `filters=` list. For the day-to-day details, including the default filters per field type, manual overrides, and the URL format, see the [Filters guide](../user-guide/filters.md).

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

* **`parse_value(raw)`** converts the raw URL string into the type `apply()` expects, such as a `Decimal`, a `date`, or a list. The default passes the string through unchanged, which suits `STRING` and `ENUM` filters but not numeric or temporal data. It's also your validation hook: raise `FilterValidationError` for values that parse but are still unacceptable, such as out-of-range or malformed input.
* **`apply(ctx)`** is the only abstract method. It receives a `FilterApplyContext` holding the `query`, `field_name`, `value`, `value2`, `request`, and `view`, and returns a query fragment for your backend.

## How raw URL values get parsed

Every URL parameter is a string, so `price__gt=50` and `created_at__eq=2026-01-01` both arrive as raw text. Before `apply()` runs, `parse_value()` converts that string into a Python object matching the filter's `data_type`:

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

So `?filter=price__gt=50` and `?filter=price__gt=50.5` reach `GreaterThanFilter.apply()` as Python numbers (`50` as an `int`, `50.5` as a `float`) rather than the strings `"50"` and `"50.5"`. `apply()` passes that parsed value straight to the query object, and the database driver handles the final coercion against the column's actual type, such as `Decimal` or `Numeric`.

| `data_type` | Example raw URL value | Parsed Python value | Parsed by |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (tries `int()`, falls back to `float()`) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal` using `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal` using `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal` using `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (splits on unquoted commas) |
| `string`, `enum` | `admin` | `"admin"` | `BaseFilter.parse_value` default (passed through unchanged) |
| `none` | *(no value in the URL at all)* | *(never called)* | N/A |

When a value fails to parse, such as `price__gt=abc` or `created_at__eq=not-a-date`, `parse_value()` raises a `FilterValidationError`. The request handler catches it and returns `HTTP 400` before running any database query:

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

Value-less filters, the ones with `data_type=none` such as `is_null`, `is_true`, or `in_past`, skip this step. `parse_value` never runs for them, which is why `field__is_null` needs no `=value` in the URL: there's no input string to convert.

## Making a custom filter available

You can register a custom filter with a view in two ways. Pick the one that matches the scope you want.

### Per field instance (narrow scope)

Pass the filter into the target field's `filters=` list, either alongside the defaults or in place of them. See [Overriding filters for a specific field](../user-guide/filters.md#overriding-filters-for-a-specific-field) for the same pattern with built-in filters. Use this when the filter only makes sense for one field.

### Registry-wide (every matching field type)

Each backend ships a `FilterRegistry` subclass: `SqlaFilterRegistry` for SQLAlchemy, `BeanieFilterRegistry` for Beanie, `MongoEngineFilterRegistry` for MongoEngine, and `TortoiseFilterRegistry` for Tortoise ORM. Each one defines the default filters for a supported field type in a method decorated with `@filters(FieldType, ...)`:

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

To change the filters available for a field type across a whole view, subclass the backend's registry, override or add a `@filters` method, and return an instance of your subclass from `get_filter_registry()`:

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

Declare these methods one of two ways, depending on whether you want to replace the existing filters or extend them:

* **Override:** Re-declare `@filters(StringField)` on your subclass and return exactly the classes you want. This replaces the parent's list, so include any built-in filters you want to keep.
* **Extend:** Declare `@filters(IntegerField)` when the parent registry only registers the broader `NumberField`. Because `IntegerField` subclasses `NumberField`, the method resolution order (MRO) resolves `IntegerField` to your new method, while `DecimalField`, another `NumberField` subclass with no registration of its own, keeps inheriting the parent's `numeric_filters` unchanged.

This is a plain Python subclass, so it mutates no global state. Every call to `ProductFilterRegistry()` builds an independent registry, and your changes stay scoped to the views that return it. All other views keep the backend defaults.

## Full SQLAlchemy example

The `DivisibleByFilter` below takes a value, the divisor to check the column against. A `SqlaFilterRegistry` subclass applies it to every `IntegerField` on `ProductView`, rather than attaching it to individual fields:

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

    Overriding `integer_filters` gives every IntegerField the divisibility filter
    on top of the standard numeric defaults. Other numeric fields, such as
    DecimalField, are unaffected.
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

The `lot_size__divisible_by` option now shows up as a filter for `IntegerField("lot_size")`, with no explicit `filters=` declaration on the field. For example, `lot_size__divisible_by=6` matches products whose lot size is a multiple of 6:

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    Use a `FilterRegistry` subclass when a filter is generic enough to apply to every field of a given type in a view. Use the per-field `filters=` list when the logic belongs to one field only. The [Filters guide](../user-guide/filters.md#overriding-filters-for-a-specific-field) has examples of the per-field pattern.

## Dynamic choices with `get_choices`

By default, a filter's value input follows its `data_type`: a plain text box for `STRING`, a number box for `NUMBER`, and so on. Override `get_choices(request)` when the value should come from a dropdown seeded with a per-request list of `(value, label)` pairs instead. An "is one of" filter over a relation field is the typical case: the value posted back is a foreign key, but the picker should show a readable name.

`get_choices` receives the current `Request` and returns a sequence of `(value, label)` pairs, or `None` (the default) to leave the plain input in place. A non-empty result wins over both the plain input and any choices the field itself supplies, as `EnumField` does.

The example below, from [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr), adds an "is one of" and "is not one of" pair to the `department` field on the `Employee` list. `department` is a `RelationField`, so the default registry gives it null checks only: there's no generic way to compare a related row to a raw string. `get_choices` lists every `Department` by name for the dropdown, and `parse_value` converts the posted-back values to integers so `apply` can match on the `Department.id` foreign key directly instead of joining through the relationship and comparing names:

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

* **The mixin sits before the base filter class in the MRO.** `_DepartmentChoicesMixin` comes first in `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)`, so its `get_choices` and `parse_value` override the ones each filter would otherwise inherit. `super().parse_value(raw)` still reaches `InFilter.parse_value`, which splits the raw value into a list before the mixin converts it to integers.
* **`get_choices` runs on every request**, not once at import time, so the dropdown always reflects the current rows. A newly added `Department` shows up in the filter builder immediately, with no server restart and no cache to invalidate.
* **The `(value, label)` pairs and `parse_value`'s output type have to agree.** The dropdown posts back whichever `value` the user picked, so `parse_value` converts it into what `apply` expects. `Department.id` is already an `int` here, so the mixin's `parse_value` reasserts that and raises a validation error on anything else.
* **`InFilter` and `NotInFilter` already default to `data_type = FilterDataType.ENUM`**, a multi-select, so neither subclass needs a `data_type` override. Overriding `get_choices` is enough to seed that multi-select with departments instead of leaving it empty.

---

## What's next

* **[Filters](../user-guide/filters.md):** Learn about default filters per field type, the URL format, and the `filters=` override.
* **[SQLAlchemy](../integrations/sqlalchemy.md):** Explore the SQLAlchemy backend used in this page's example.
* **[Extension points](extension-points.md):** View the complete list of methods you can override on `ModelView`.
