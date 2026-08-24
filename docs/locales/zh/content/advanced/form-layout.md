---
title: 表单布局
description: 使用 TabsWidget、FieldsetWidget 和网格列，在 starlette-admin 中设计复杂的响应式表单布局。
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# 表单布局

默认情况下，新建和编辑表单会将 `fields` 中的所有内容渲染为一个扁平列表。借助 `form_layout` 属性，你可以使用与[仪表盘](../user-guide/custom-views.md)相同的可组合部件来排列这些输入：并排行、带标题或可折叠的面板、标签页、静态内容，以及你自己的自定义部件。

## 基本用法

最简单的布局完全不需要部件。通过字符串名称引用字段，可使其独占一行；将多个名称组成元组，可使它们在同一行中并排显示。

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

在上面的布局中：

* `("first_name", "last_name")` 创建一行，由两个输入平分宽度。
* `"email"` 在其正下方独占一行渲染。
* `("salary", "notes")` 创建第二个多列行。

一行中可以放置任意数量的字段，并且可以自由混用单列行和多列行。

容器部件会自行展开这种简写形式：`RowWidget`、`ColumnWidget`、`GridWidget`、`PanelWidget`、`FieldsetWidget`、`TabsWidget` 和 `Col` 在构造时都会将元组转换为行、将列表转换为堆叠的列。因此，这种简写形式同样适用于嵌套的 `children` 属性以及 [`CustomView.widget`](../user-guide/custom-views.md) 仪表盘。

## 字段分组

### 带标题的面板

要为一组字段添加标题，或使其可折叠，请将其包装在 `PanelWidget` 中。该部件接受与顶层相同的字符串和元组简写形式。

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` 接受以下属性：

| 属性 | 描述 |
| --- | --- |
| `title` | 显示在面板卡片头部中的标题。 |
| `children` | 按顺序渲染在面板内部的部件。接受上述简写形式或嵌套部件。添加一个 `TextWidget(card=False)` 子项，可在标题下方放置说明文字。 |
| `collapsible` | 允许用户展开和折叠面板。 |
| `collapsed` | 使面板初始处于折叠状态。仅在 `collapsible=True` 时生效。 |

对于不需要标题的分组，请改用 `ColumnWidget`。它会垂直堆叠子项，而不会将其包装在带样式的卡片中。

### 字段集

`FieldsetWidget` 对字段的分组方式与 `PanelWidget` 类似，但它渲染的是原生 HTML `<fieldset>` 和 `<legend>` 元素，而不是带样式的卡片。当你想要更简单的带边框分组时，可以使用它。

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

`legend` 属性设置 `<legend>` 元素中的标题文字。`disabled=True` 会在容器上设置 HTML `disabled` 属性，从而禁用所有嵌套的表单控件。`FieldsetWidget` 支持与 `PanelWidget` 相同的 `children` 简写形式，但不支持 `collapsible` 和 `icon` 等面板专属选项。

## 显式列宽

元组简写形式总是将一行平均分配。若要更精细地控制列宽，请使用 `RowWidget`、`Col` 和 `FieldRef` 显式构建行：

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## 隐藏字段标签

显式构造 `FieldRef` 时可以使用 `show_label` 参数，当周围布局已能清楚表明字段用途时，该参数可移除 `<label>` 元素。

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` 默认为 `True`。字符串和元组简写形式总是会渲染标签，因为它们不接受关键字参数。

## 输入组

`prepend` 和 `append` 参数用于在输入框的任一侧附加一个[输入组](https://docs.tabler.io/ui/forms/form-elements#input-group)（input group）附加组件。两者均接受纯文本或原始 HTML，例如 Font Awesome 图标。

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

附加组件适用于表单模板渲染原生 `<input>` 元素的字段：`StringField`、`EmailField`、`URLField`、`PhoneField`、`PasswordField`、`ColorField`、`SlugField`、数值字段（`IntegerField`、`DecimalField`、`FloatField`）以及日期和时间字段。其他类型（如 `EnumField`、`TextAreaField` 和 `BooleanField`）则会静默忽略它们。

!!! warning
    附加组件的值以未转义的形式渲染，以便图标标记之类的 HTML 能正常工作。只传入你自己编写的可信内容，切勿传入用户输入。

## 标签页

要将各分区拆分为标签页界面，请使用 `TabsWidget`。它接受由 `(label, widgets)` 对组成的列表。

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## 静态内容

使用 `HtmlWidget` 和 `TextWidget` 可以在布局中的任意位置渲染任意内容：说明文字、警告信息或分隔线。

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## 自定义部件

由于 `form_layout` 与仪表盘共享 `BaseWidget` 层次结构，你可以通过继承 `BaseWidget` 来构建自己的元素。对于内置部件未能涵盖的任何需求，例如只读预览、嵌入式图表或自定义宏，都可以用它来实现。

一般模式请参见[自定义视图与部件](../user-guide/custom-views.md)，子类可覆盖的方法请参见[部件 API 参考](../api/widgets.md)。无论字段可见性规则如何规定，`form_layout` 中的自定义部件始终会渲染。

## 访问控制与可见性

`form_layout` 遵循你的字段级访问规则。每个 `FieldRef` 都会经过常规的 `can_access_field` 检查，且 `exclude_from_create`、`exclude_from_edit` 以及基于角色的权限全部保持有效。

* **行扩展：**当多列行中的某个字段对某次请求隐藏时，其余可见字段会扩展以填满空间。
* **空容器：**当容器（行、面板、字段集、列、网格或标签页）中的所有字段都被隐藏时，该容器会被省略，因此不会留下空壳。
* **静态渲染：**`HtmlWidget`、`TextWidget` 以及自定义 `BaseWidget` 子类等静态组件始终会渲染，因为它们不依赖表单字段。

## 处理被省略的字段

声明在 `fields` 中但未出现在 `form_layout` 里的字段，会按声明顺序追加到表单底部，因此任何字段都不会被静默丢弃。

重复引用同一字段，或引用不在 `fields` 中的名称，都会在视图构造时引发 `ValueError`。

---

## 下一步

* **[自定义视图与部件](../user-guide/custom-views.md)：**`form_layout` 所依托的部件层次结构，以及如何编写自己的部件。
* **[模板](templates.md)：**重写 `_form_group.html` 以更改布局组渲染的标记。
* **[字段](../user-guide/fields.md)：**布局所编排的字段类型与可见性规则。
