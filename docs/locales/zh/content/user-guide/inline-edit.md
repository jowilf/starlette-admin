---
title: 行内编辑
description: 让用户直接在列表视图表格内编辑字段值，加快数据录入速度。
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# 行内编辑

行内编辑让用户可以直接从列表页修改单个字段。选中一个单元格会打开一个小型弹出框，因此无需打开完整的编辑表单。它适用于快速的单字段更新：修正标题、切换状态或调整日期。这种交互遵循广为人知的 [x-editable](https://vitalets.github.io/x-editable/) 模式。

该功能为可选启用，默认关闭。启用它不会改变标准的编辑页面，后者仍是复杂多字段编辑的主要界面。

> 如需包含行内编辑的可运行示例，请参见 [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart)。

## 基本用法

在 `inline_editable_fields` 列表中声明可编辑字段的名称：

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

此后，列表页上的可编辑单元格会显示虚线下划线。选中一个单元格会打开一个弹出框，其中包含该字段的标准表单控件，并预填当前值。

下划线并不会绘制在整个单元格上。每个列表模板都会在需要加下划线的具体元素上放置 `inline-edit-value` CSS 类，且该样式只在可编辑单元格内部生效。所有内置列表模板都已带有该类。如果你编写了自定义的 `list_template` 并希望获得相同的视觉提示，请自行添加该类：

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

如果没有该类，单元格仍会打开弹出框，但不会渲染下划线。

- **保存：** 在单行输入框中选择对勾按钮或按 <kbd>Enter</kbd>。管理后台会校验该字段、保存更改并刷新该行，无需重新加载页面。
- **取消：** 选择 <kbd>x</kbd> 按钮或按 <kbd>Esc</kbd> 放弃更改。

## 配置规则

应用会在启动时校验 `inline_editable_fields`，以便配置错误能快速失败。当列出的名称满足以下任一条件时会引发 `ValueError`：

- 未在 `fields` 中声明。
- 它是主键字段。
- 它被排除在列表页（`exclude_from_list`）或编辑表单（`exclude_from_edit`）之外。
- 它是容器字段或只读字段：`CollectionField`、`ListField`、`ComputedField`、`FileField` 或 `ImageField`。

## 字段支持

每个可编辑字段都渲染与其在编辑页面上相同的表单部件。字段的 JavaScript 与 CSS 资源（如 select2、flatpickr、JSONEditor 或 TinyMCE）仅在该字段支持行内编辑时才会加载到列表页。未使用行内编辑的视图保持其现有的轻量页面体积。

| 字段类型                                                                             | 是否支持 | 弹出框部件                          |
| ------------------------------------------------------------------------------------ | -------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | 支持     | 普通输入框                          |
| `SlugField`                                                                          | 支持     | 普通输入框（源字段被排除）          |
| `TextAreaField`                                                                      | 支持     | 文本域                              |
| `IntegerField`, `DecimalField`, `FloatField`                                         | 支持     | 数字输入框                          |
| `BooleanField`                                                                       | 支持     | 开关                                |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | 支持     | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | 支持     | select2 或原生下拉选择              |
| `TagsField`                                                                          | 支持     | select2 标签                        |
| `JSONField`                                                                          | 支持     | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | 支持     | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | 支持     | 支持异步查询的 select2              |
| `FileField`, `ImageField`                                                            | 不支持   | 无（需要编辑页面）                  |
| `CollectionField`, `ListField`, `ComputedField`                                      | 不支持   | 无（只读容器）                      |

---

## 权限

行内编辑复用现有的权限模型。只有当 `is_accessible(request)` 和 `can_edit(request)` 都返回 `True` 时，弹出框才会出现，管理后台也才会接受请求。因此，重写 `can_edit` 同样能保护行内编辑：

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Also disables inline edit when False
        return "edit:post" in request.state.admin_user.roles
```

---

## 校验

行内保存只校验并写入被编辑的字段。

- 该字段的 `required` 检查和 `validators` 链的运行方式与编辑页面上完全一致。
- 其他字段会被跳过。来自列表页的保存不会覆盖对其他字段的并发编辑，另一字段中的无效数据也不会阻止保存。

视图的跨字段 `validate` 钩子仍会运行，但 `data` 字典只包含被编辑的字段。期望接收完整表单提交的钩子如果直接索引缺失的键会引发 `KeyError`，因此请先检查键是否存在：

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

校验失败时，弹出框保持打开状态，且已提交的值保持不变。被编辑字段的消息渲染在该控件下方，与编辑页面完全一致。与其他字段关联的消息则以该字段的标签作为前缀。

要在钩子内检测行内保存，请检查 `request.state.action == RequestAction.INLINE_EDIT`。可以用它来跳过面向完整页面渲染的 Flash 消息。

!!! warning
    与用户未编辑的字段关联的校验规则不会在行内保存期间运行。如果某个字段的约束依赖于用户无法从列表页查看或更改的值，请不要将该字段加入 `inline_editable_fields`。

---

## 生命周期钩子与事件

行内保存经过视图的标准 `edit()` 路径。`before_edit`、`after_edit` 和 `after_edit_committed` 钩子照常触发，相应的[事件](../advanced/events.md)使用标准的上下文类型。`data` 和 `old_data` 载荷只包含被编辑的字段，因此它们准确反映了此次保存所触及的内容。

要在事件监听器中区分行内保存，请检查 `ctx.extra["inline"]`，对于行内编辑它的值为 `True`：

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## 自定义字段

自定义字段只要遵循标准的 `BaseField` 契约，就会自动支持行内编辑。由于 `RequestAction.INLINE_EDIT` 属于表单动作，`action.is_form()` 会返回 `True`。如果你的自定义字段通过检查 `action == RequestAction.EDIT` 来构建表单值表示形式，请改为使用 `action.is_form()`，以便弹出框接收到正确的表示形式。有关完整的字段契约，请参见[自定义字段](../advanced/custom-fields.md)。
