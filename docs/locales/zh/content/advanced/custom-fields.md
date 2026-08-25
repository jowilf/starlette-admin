---
title: 自定义字段
description: 了解如何在 starlette-admin 中创建自定义字段类型，以处理特殊的数据类型和自定义 UI 部件。
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# 自定义字段

内置字段已经覆盖了你会遇到的大多数列，但当它们都不适用时，你可以通过继承 [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField) 来构建自己的字段。一个字段就是三个在模型与浏览器之间传递数据的方法，外加一组负责渲染它的模板路径。你可以直接继承 `BaseField`，也可以扩展最接近需求的内置字段（例如 `StringField` 或 `EnumField`），只覆盖有差异的部分。

## 最小示例

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

将 `Admin` 实例指向模板目录，然后在视图中使用该字段：

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

由于 `StatusBadgeField` 继承自 `EnumField` 而不是 `BaseField`，它继承了 `choices`、针对这些选项的表单校验，以及用于创建和编辑表单的默认 `fields/form/enum.html` 模板。这些都无需改动，所以该类只覆盖了列表和详情的渲染属性。

本页其余部分介绍当字段需要的不仅仅是更换模板时应当覆盖哪些内容。完整的可运行代码，以及第二个确实覆盖了数据处理方法的字段（`AvatarNameField`），参见 [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields)。

## 三个数据方法

| 方法 | 调用时机 | 签名 |
| --- | --- | --- |
| `parse_form_data` | 创建/编辑表单提交时 | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | 从模型实例读取值用于显示时 | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | 为前端格式化值时（列表、详情、API、导出） | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` 没有覆盖其中任何一个，因为 `EnumField` 已经根据 `choices` 解析提交的值，并从 `obj.status` 读取原始字符串。徽章只是在该字符串之上呈现的外观。只有当值本身需要计算或重塑、而非重新渲染时，才需要覆盖这三个方法。

!!! tip "钩子还是子类"
    对单个字段做一次性修改时，很少需要子类。可以改为把 [`getter`、`formatter` 和 `parser` 钩子](../user-guide/fields.md#computing-formatting-and-parsing-values)作为构造函数参数传入，分别处理读取、显示格式化和输入解析。
    **何时使用子类：**仅当你需要在多个视图中复用相同逻辑，或者需要更改模板时。

`parse_form_data` 从请求中接收原始的 `FormData`（来自 `starlette.datastructures`），并返回该字段应交给 `view.create()` 或 `view.edit()` 的数据。默认实现读取 `form_data.get(self.id)` 并原样返回。大多数字段只需添加类型转换：

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` 接收模型实例并返回要显示的值。默认实现返回 `getattr(obj, self.name, None)`。当字段并非映射到单个模型属性（例如组合两列的字段）时，应覆盖该方法。例如，`AvatarNameField` 把 `name` 字符串与该行上传的头像组合在一起：

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` 接收 `parse_obj`（或 ORM 层）产生的结果，并为当前请求进行格式化。列表页、详情页、JSON API 和数据导出会分别调用它，因此当数据结构需要因上下文而异时，应根据 `request.state.action` 分支处理。`AvatarNameField` 只在列表页需要头像图片，其他场景则回退为纯文本：

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
    `serialize_value` 针对 `RequestAction.LIST` 和 `RequestAction.RELATION_LOOKUP` 返回的内容会直接进入 JSON 响应，因此必须是可 JSON 序列化的。

## 模板路径

每个字段都带有下列模板属性。每个属性都是一条由管理后台的 Jinja2 加载器解析的路径：它会先检查你设置的 `templates_dir`（如果设置了的话），然后回退到内置的 `starlette_admin/templates/` 目录。细节参见[模板](templates.md)。

| 属性 | 默认值 | 渲染场景 |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | 列表页上每行的列值 |
| `detail_template` | `"fields/detail/text.html"` | 只读的详情页 |
| `form_template` | `"fields/form/input.html"` | 创建/编辑表单的输入控件 |
| `null_template` | `"fields/detail/_null.html"` | 值为 `None` 时的列表页和详情页 |
| `empty_template` | `"fields/detail/_empty.html"` | 值为空列表或空元组时的列表页和详情页 |

所有五个模板都会收到 `field` 实例和当前的 `data` 值。对于 `list_template` 和 `detail_template`，`data` 永远不会是 `None` 或空值，因为这类情况会在引入类型专属模板之前被路由到 `null_template` 或 `empty_template`。`form_template` 还会收到 `error`（若发生了 `FormValidationError`，则为其中的消息）和 `action`（在列表页的[内联编辑](../user-guide/inline-edit.md)弹出框内渲染时为 `RequestAction.CREATE`、`RequestAction.EDIT` 或 `RequestAction.INLINE_EDIT`）。这三者都是表单动作，因此 `action.is_form()` 返回 `True`。需要区分表单取值表示形式的字段代码应据此分支，而不是判断 `action == RequestAction.EDIT`。

当缺失值的外观需要区别于默认的灰色 `-null-` 和 `-empty-` 标签时，可以覆盖 `null_template` 和 `empty_template`，例如使用空状态图标，或一个与字段自身样式一致的"Not provided"徽章：

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

由于 `null_template` 和 `empty_template` 与 `list_template` 一样是普通的字段属性，它们会在列表、详情以及任何其他渲染该字段的视图之间共享，例如关联视图的内联表格。

`StatusBadgeField` 给 `list_template` 和 `detail_template` 赋予了同一个模板，因为同一个徽章在两种上下文中都适用：

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` 只覆盖了 `list_template`。该模板中的 `data` 变量是由 `parse_obj` 构造、再经 `serialize_value` 重塑的字典，而不是普通字符串：

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

`inline-edit-value` 类是启用[内联编辑](../user-guide/inline-edit.md)下划线的可选标记。在字段不支持内联编辑时它不起任何作用，因此把它放在名称而非头像上没有任何代价，同时若字段日后变为可编辑，这一交互提示的作用范围也能保持正确。

覆盖 `list_template` 和 `detail_template` 同时保留默认的 `form_template`，正是 `StatusBadgeField` 通过扩展 `EnumField` 所做的。默认的 `fields/form/enum.html` 会渲染一个由 `field.choices` 填充的 `<select>` 下拉框，因此编辑状态无需进一步改动即可正常工作。

## 注册到转换器注册表

视图中的 `fields = [...]` 列表既接受字段对象，也接受普通属性名。凡是不是 `BaseField` 的条目都会经过一个**转换器注册表**，由它把列类型映射到字段类。每个 ORM 后端都自带注册表（`starlette_admin.contrib.sqla.converters.ModelConverter` 以及 `beanie`、`mongoengine` 和 `tortoise` 的对应实现），它们都构建在同一个基类之上：

```python
from starlette_admin.converters import BaseModelConverter, converts
```

`@converts(*types)` 装饰器把一个方法标记为一个或多个类型键的转换器。`BaseModelConverter.__init__` 会扫描实例中被装饰的方法，并由它们构建 `converters` 字典。对于 SQLAlchemy 后端，类型键就是列类型的**名称**（如 `"String"`、`"Integer"`、`"Enum"` 等），因为 SQLAlchemy 的各个方言之间不存在统一的公共基类。

继承后端的转换器即可添加自己的映射。下例把每个 `Enum` 列都路由到 `StatusBadgeField`，而不是默认的 `EnumField`：

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

把这个子类传给 `ModelView(converter=...)`，这样 `fields = [...]` 中的字符串字段名就会通过你的转换器而非默认转换器来解析：

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

如果你总是像上面的最小示例那样显式构造字段，则可以跳过转换器注册表。只有当你希望像 `fields = ["status"]` 这样的条目能根据底层列类型生成 `StatusBadgeField` 时才需要它。

---

## 后续内容

* **[字段](../user-guide/fields.md)：**完整的内置字段参考以及 `BaseField` 属性表。
* **[模板](templates.md)：**模板加载器如何解析 `list_template`、`detail_template`、`form_template`、`null_template` 和 `empty_template`。
* **[扩展点](extension-points.md)：**`starlette-admin` 中其余所有可插拔的扩展面。
