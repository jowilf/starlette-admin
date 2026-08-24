---
title: 自定义过滤器
description: 通过在 starlette-admin 中创建自定义数据库过滤器和操作符，扩展内置的查询构建器。
source_hash: ac118a53b1d95372b17388cb1ce13241e53cd4b2983158208affa0fedb2e2446
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)
<!-- translation-notice:end -->

# 自定义过滤器

当你需要内置操作符集合未涵盖的操作符时，请继承 `BaseFilter`：例如 "_能被整除_" 这类领域特定的检查、"_本月创建_" 这类计算得到的条件，或为默认注册表忽略的字段类型提供支持。本页说明过滤器内部的工作原理，并展示注册过滤器的两种方式：继承后端的 `FilterRegistry` 以覆盖所有匹配的字段类型，或将过滤器传入单个字段的 `filters=` 列表。有关日常使用的详细信息（包括每种字段类型的默认过滤器、手动覆盖方式和 URL 格式），请参阅[过滤器指南](../user-guide/filters.md)。

## `BaseFilter` 接口

无论是内置还是自定义过滤器，都实现两个方法：

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

* **`parse_value(raw)`** 将原始 URL 字符串转换为 `apply()` 期望的类型，例如 `Decimal`、`date` 或列表。默认实现原样传递字符串，这适用于 `STRING` 和 `ENUM` 过滤器，但不适用于数值或时间数据。它也是你的校验钩子：对于能够解析但仍不可接受的值（例如超出范围或格式错误的输入），抛出 `FilterValidationError`。
* **`apply(ctx)`** 是唯一的抽象方法。它接收一个包含 `query`、`field_name`、`value`、`value2`、`request` 和 `view` 的 `FilterApplyContext`，并返回一个适用于你后端的查询片段。

## 原始 URL 值的解析方式

每个 URL 参数都是字符串，因此 `price__gt=50` 和 `created_at__eq=2026-01-01` 都以原始文本的形式传入。在 `apply()` 运行之前，`parse_value()` 会将该字符串转换为与过滤器 `data_type` 匹配的 Python 对象：

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

因此，`?filter=price__gt=50` 和 `?filter=price__gt=50.5` 到达 `GreaterThanFilter.apply()` 时已经是 Python 数字（`50` 为 `int`，`50.5` 为 `float`），而不是字符串 `"50"` 和 `"50.5"`。`apply()` 将解析后的值直接传递给查询对象，数据库驱动会根据列的实际类型（例如 `Decimal` 或 `Numeric`）完成最终转换。

| `data_type` | 原始 URL 值示例 | 解析后的 Python 值 | 解析方式 |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number`（先尝试 `int()`，再回退到 `float()`） |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal`，使用 `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal`，使用 `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal`，使用 `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array`（按不带引号的逗号拆分） |
| `string`, `enum` | `admin` | `"admin"` | `BaseFilter.parse_value` 默认实现（原样传递） |
| `none` | *（URL 中完全没有值）* | *（从不调用）* | N/A |

当某个值无法解析时（例如 `price__gt=abc` 或 `created_at__eq=not-a-date`），`parse_value()` 会抛出 `FilterValidationError`。请求处理器会捕获该异常，并在执行任何数据库查询之前返回 `HTTP 400`：

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

无值过滤器（即 `data_type=none` 的过滤器，如 `is_null`、`is_true` 或 `in_past`）会跳过这一步。`parse_value` 从不为它们运行，这正是 `field__is_null` 在 URL 中不需要 `=value` 的原因：没有需要转换的输入字符串。

## 使自定义过滤器可用

可以通过两种方式向视图注册自定义过滤器。请选择符合所需作用范围的方式。

### 单个字段实例（窄范围）

将过滤器传入目标字段的 `filters=` 列表中，既可以与默认过滤器并存，也可以取而代之。使用内置过滤器的相同模式，请参见[为特定字段覆盖过滤器](../user-guide/filters.md#overriding-filters-for-a-specific-field)。当过滤器只对某一个字段有意义时，请使用这种方式。

### 注册表级别（所有匹配的字段类型）

每个后端都附带一个 `FilterRegistry` 子类：SQLAlchemy 对应 `SqlaFilterRegistry`，Beanie 对应 `BeanieFilterRegistry`，MongoEngine 对应 `MongoEngineFilterRegistry`，Tortoise ORM 对应 `TortoiseFilterRegistry`。每个子类都在由 `@filters(FieldType, ...)` 装饰的方法中定义某种受支持字段类型的默认过滤器：

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

要在整个视图范围内更改某一字段类型可用的过滤器，请继承后端的注册表，覆盖或新增一个 `@filters` 方法，并让 `get_filter_registry()` 返回你的子类实例：

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

根据是要替换现有过滤器还是扩展它们，可以用以下两种方式之一声明这些方法：

* **覆盖：**在子类上重新声明 `@filters(StringField)`，并精确返回所需的类。这会替换父类的列表，因此请包含你想保留的所有内置过滤器。
* **扩展：**当父注册表只注册了更宽泛的 `NumberField` 时，可声明 `@filters(IntegerField)`。由于 `IntegerField` 继承自 `NumberField`，方法解析顺序（MRO）会将 `IntegerField` 解析到你的新方法；而另一个没有自身注册项的 `NumberField` 子类 `DecimalField` 则保持不变，继续继承父类的 `numeric_filters`。

这是一个普通的 Python 子类，因此不会修改任何全局状态。每次调用 `ProductFilterRegistry()` 都会构建一个独立的注册表，你的修改只作用于返回它的视图。所有其他视图保持后端默认设置。

## 完整的 SQLAlchemy 示例

下面的 `DivisibleByFilter` 接受一个值，即用于检查列的除数。一个 `SqlaFilterRegistry` 子类将它应用于 `ProductView` 上的每个 `IntegerField`，而不是附加到各个单独的字段：

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

可运行的应用示例见 [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters)，其中包含以同样方式注册的自定义 `BaseFilter` 子类。

现在，`lot_size__divisible_by` 选项会作为 `IntegerField("lot_size")` 的过滤器出现，无需在该字段上显式声明 `filters=`。例如，`lot_size__divisible_by=6` 匹配批量是 6 的倍数的产品：

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    当过滤器足够通用、可以应用于视图中某一给定类型的所有字段时，请使用 `FilterRegistry` 子类。当逻辑只属于单个字段时，请使用按字段的 `filters=` 列表。[过滤器指南](../user-guide/filters.md#overriding-filters-for-a-specific-field)提供了按字段模式的示例。

## 使用 `get_choices` 提供动态选项

默认情况下，过滤器的值输入控件遵循其 `data_type`：`STRING` 对应纯文本框，`NUMBER` 对应数字框，依此类推。当值应改为来自下拉菜单、且该下拉菜单由随每次请求提供的 `(value, label)` 对列表填充时，请覆盖 `get_choices(request)`。作用于关系字段的 "is one of" 过滤器是典型场景：回传的值是外键，但选择器应显示易于阅读的名称。

`get_choices` 接收当前的 `Request` 并返回一个由 `(value, label)` 对组成的序列，或者返回 `None`（默认行为）以保留普通输入控件。只要结果非空，它就会同时优先于普通输入控件和字段自身提供的任何选项（如 `EnumField` 提供的选项）。

下面的示例来自 [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr)，它在 `Employee` 列表的 `department` 字段上添加了一对 "is one of" 和 "is not one of" 过滤器。`department` 是一个 `RelationField`，因此默认注册表只为它提供空值检查：没有将关联行与原始字符串进行比较的通用方法。`get_choices` 按名称列出所有 `Department` 以填充下拉菜单，而 `parse_value` 将回传的值转换为整数，使 `apply` 可以直接基于 `Department.id` 外键进行匹配，而不必通过关系进行连接并比较名称：

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

关于这一模式，有几点需要注意：

* **Mixin 在 MRO 中位于基础过滤器类之前。**在 `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)` 中，`_DepartmentChoicesMixin` 排在最前，因此它的 `get_choices` 和 `parse_value` 会覆盖各过滤器原本要继承的实现。`super().parse_value(raw)` 仍会到达 `InFilter.parse_value`，它先将原始值拆分为列表，再由 mixin 将其转换为整数。
* **`get_choices` 在每次请求时运行**，而不是在导入时运行一次，因此下拉菜单始终反映当前的数据行。新增的 `Department` 会立即出现在过滤器构建器中，无需重启服务器，也没有需要失效的缓存。
* **`(value, label)` 对必须与 `parse_value` 的输出类型保持一致。**下拉菜单回传用户选择的任意 `value`，因此 `parse_value` 要将其转换为 `apply` 所期望的类型。这里的 `Department.id` 本身就是 `int`，所以 mixin 的 `parse_value` 再次确认这一点，并对其他任何类型抛出校验错误。
* **`InFilter` 和 `NotInFilter` 已默认使用 `data_type = FilterDataType.ENUM`**，即一种多选类型，因此这两个子类都不需要覆盖 `data_type`。只需覆盖 `get_choices`，即可用部门填充该多选控件，而不是让它留空。

---

## 下一步

* **[过滤器](../user-guide/filters.md)：**了解每种字段类型的默认过滤器、URL 格式以及 `filters=` 覆盖方式。
* **[SQLAlchemy](../integrations/sqlalchemy.md)：**探索本页示例所使用的 SQLAlchemy 后端。
* **[扩展点](extension-points.md)：**查看可以在 `ModelView` 上覆盖的方法完整列表。
