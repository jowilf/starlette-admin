---
title: 过滤器
description: 使用类型感知的查询构建器，为你的管理视图添加复杂的嵌套 AND/OR 过滤能力。
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# 过滤器

列表页上的每个字段都可以拥有一组自己的过滤器操作符，例如 `contains`、`between` 和 `is null`。用户可以将这些操作符组合成嵌套的 `AND`/`OR` 树，而你自己无需编写复杂的数据库查询。

管理界面会根据字段的底层类型推导出可用的过滤器。对于任何字段，你都可以收窄、扩展或完全替换这套过滤器。


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

可运行示例见 [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters)，其中涵盖默认过滤器、按字段覆盖以及自定义 `BaseFilter` 子类。

你在 `searchable_fields` 中列出的每个字段，都会在列表工具栏中获得一个**过滤器**下拉菜单。用户可以从这里组合任意数量的过滤器，找到所需的行。

## 过滤器构建器的工作原理

点击**过滤器**按钮会打开一个下拉表单，用户可以在其中构建查询：

* **添加过滤器**：添加一行条件。用户选择一个字段，从该字段的可用过滤器中选定一个操作符，并提供一个值。输入控件会随操作符变化：`contains` 对应一个普通文本框，`between` 对应两个文本框，而 `is null` 则完全不需要输入。
* **添加分组**：嵌套一个带有独立 `AND`/`OR` 选择器的子表单。可以用它构建形如 `A AND (B OR C)` 的条件。
* **匹配以下所有/任一条件**：设置当前层级采用 `AND` 还是 `OR` 逻辑。
* **应用过滤器**：以 `GET` 请求提交表单。管理界面会将整个过滤器树序列化为一个 `filter` 查询参数，具体说明见[过滤器 URL 格式](#the-filter-url-format)。
* **活动过滤器**：每个生效的过滤器都会以可移除标签的形式显示在表格上方。点击 `×` 会重新提交列表并移除对应规则。嵌套分组会折叠为单个标签，用户可以将其作为一个整体移除。

!!! tip
    由于完整的过滤状态都保存在 URL 中，过滤后的列表是可以分享的。用户可以把页面加入书签，再把链接发给同事。

## 为特定字段覆盖过滤器 {#overriding-filters-for-a-specific-field}

当默认过滤器过于宽泛，或者你需要更具体的过滤条件时，可以为字段传入 `filters=` 参数来替换其默认过滤器集。

你可以把列表收窄到真正需要的操作符，用自定义过滤器扩展它，也可以为默认仅有基本空值检查的字段添加操作符，例如 `TagsField`：

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

!!! important "从你的后端导入过滤器"
    传递给 `filters=` 的过滤器类必须是与你数据库后端相对应的具体实现：`starlette_admin.contrib.sqla.filters`、`.beanie.filters`、`.mongoengine.filters` 或 `.tortoise.filters`。请从你所用后端的 `filters` 模块导入，而不是从 `starlette_admin.filters` 导入。

## 过滤器 URL 格式 {#the-filter-url-format}

过滤器构建器会将其状态序列化为一个紧凑字符串，放入 `filter` 查询参数。

其格式为：不带值的过滤器写作 `field__operator`，单一值写作 `field__operator=value`，双值过滤器（例如 `between`）写作 `field__operator=value..value2`。各规则之间用 `AND` 或 `OR` 连接，圆括号用于嵌套分组：

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

当值中包含空格或圆括号时，请用引号将其包裹：`name__eq="quoted value"`。对于 `is one of` 这类多选过滤器，其列表值以逗号分隔，无需引号：`status__in=ACTIVE,OUT_OF_STOCK`。

当 URL 中含有无效的 `filter` 字符串（例如未知字段、不可用的操作符或无法解析的值）时，应用程序会返回 `HTTP 400` 错误，而不是静默丢弃部分条件。

!!! important
    只有你在 `searchable_fields` 中列出的字段才会获得过滤器。如果不设置 `searchable_fields`，则所有字段都会获得过滤器。


## 内置过滤器参考

下表列出了开箱即用的所有过滤器、书签链接中出现的 URL slug，以及每种过滤器期望的值类型。标记为“双值”的过滤器需要在 URL 中同时提供 `value` 和 `value2`，例如 `between=2026-01-01..2026-01-31`。

| 过滤器 | Slug | 值类型 | 双值？ |
| --- | --- | --- | --- |
| 包含 | `contains` | 文本 |  |
| 不包含 | `not_contains` | 文本 |  |
| 以…开头 | `startswith` | 文本 |  |
| 以…结尾 | `endswith` | 文本 |  |
| 等于 | `eq` | 文本、数字、日期、日期时间或时间 |  |
| 不等于 | `neq` | 文本或数字 |  |
| 为空 | `is_null` | *（无）* |  |
| 不为空 | `is_not_null` | *（无）* |  |
| 大于 | `gt` | 数字 |  |
| 小于 | `lt` | 数字 |  |
| 大于等于 | `gte` | 数字 |  |
| 小于等于 | `lte` | 数字 |  |
| 介于两者之间 | `between` | 数字、日期、日期时间或时间 | ✓ |
| 在过去 | `in_past` | *（无）* |  |
| 在未来 | `in_future` | *（无）* |  |
| 为真 | `is_true` | *（无）* |  |
| 为假 | `is_false` | *（无）* |  |
| 属于其中之一 | `in` | 逗号分隔的列表 |  |
| 不属于其中任何一项 | `not_in` | 逗号分隔的列表 |  |

如果内置过滤器未覆盖你所需要的数据类型，例如 JSON 字段或地理坐标点，请参阅[自定义过滤器](../advanced/custom-filters.md)，了解如何编写 `BaseFilter` 子类并将其注册为全局过滤器或特定字段实例的过滤器。

---

**后续内容**

* **[自定义过滤器](../advanced/custom-filters.md)：** 编写并注册 `BaseFilter` 子类。
* **[动作](actions.md)：** 为列表页添加批量动作和行级动作。
* **[视图](views.md)：** 进一步了解 `searchable_fields` 及列表页的其他配置。
