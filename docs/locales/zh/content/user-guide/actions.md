---
title: 动作
description: 在列表视图中直接执行批量与行级操作，支持自定义确认与表单。
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# 动作

动作提供了一种直接的方式，让你可以从管理界面中操作数据库记录，用户可以执行诸如批量删除、批量更新和发送邮件等操作。

## 理解 `ActionSelection`

`ActionSelection` 是动作 API 中的核心对象。你的处理函数接收的不是原始的主键列表，而是一个 `ActionSelection` 实例。

该对象采用惰性解析方式，无论用户是逐行勾选还是使用“全选匹配项”，其行为都保持一致。它还会将当前列表页的过滤器暴露给你的处理函数。

### `ActionSelection` API 参考

| 方法或属性                | 描述                                                                   |
| ------------------------- | ---------------------------------------------------------------------- |
| `await selection.rows()`  | 获取目标行。仅获取一次，随后缓存。                                     |
| `await selection.pks()`   | 获取目标行的主键。                                                     |
| `await selection.count()` | 返回该动作目标行的总数。                                               |
| `selection.is_select_all` | 布尔值，指示用户是否选择了“全选匹配项”。                               |
| `selection.filters`       | 当前生效的 `FilterGroup`，等同于 `ListParams.filters`。                 |
| `selection.q`             | 当前生效的全文搜索关键词，搜索未启用时为 `None`。                       |

## 批量动作

默认情况下，用户通过在列表页选中某个对象并单独编辑来更新它。若要将同一更改一次性应用到多个对象，请添加自定义**批量动作**。

!!! note
    `starlette-admin` 默认添加了一个 `delete` 批量动作。

要向你的 `ModelView` 添加自定义批量动作，请编写一个包含业务逻辑的异步函数，并用 `@action` 装饰器包装它。

!!! important
    批量动作的名称在同一个 `ModelView` 内必须唯一。

### 批量动作示例

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")
```

## 全局动作

标准批量动作需要一个有效的选择：只有当选中至少一行时，**With selected** 下拉菜单才会出现。当动作的目标是整个集合（例如完整的数据库同步）时，应将其设为全局动作。

在 `@action` 装饰器中设置 `allow_empty_selection=True`。全局动作会渲染在一个始终可见的 **Actions** 下拉菜单中，并且无需选中任何行即可运行。

**全局动作的处理函数行为：**

- **空选择：** `selection` 对象可以解析为零行。
- **附带的选择：** 如果用户在触发全局动作时已勾选了若干行，处理函数仍会接收到这些行。当你的逻辑面向整个集合时，应显式忽略 `selection`。

其他所有参数（`confirmation`、`form`、`custom_response` 和 `is_action_allowed`）的工作方式与标准批量动作完全相同。

**专用工具栏按钮：** 添加 `dedicated_button=True` 可将全局动作渲染为独立的工具栏按钮，而不是 **Actions** 下拉菜单中的一个条目。内置的导出动作就使用了此选项。将 `dedicated_button=True` 与仅限选择的动作组合使用会在启动时引发错误。

### 全局动作示例

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")
```

### “全选匹配项”功能

当用户勾选了当前页的所有行，且过滤器在其他位置还匹配更多行时，界面会提供全选匹配项选项。

该选项向动作 API 发送的是 `all=1`，而不是主键列表。使用 `selection.is_select_all` 来分支你的逻辑，或者让 `selection.rows()` 以任一方式解析数据：

```python
@action(name="archive", text="Archive")
async def archive_action(self, request: Request, selection: ActionSelection) -> None:
    if selection.is_select_all:
        await self.bulk_archive_where(request, selection.filters, selection.q)
    else:
        await self.bulk_archive_pks(request, await selection.pks())
```

!!! important "物化限制"
    在全选模式下，`selection.rows()`、`pks()` 和 `count()` 受 `action_select_all_limit` 限制，该值默认为 1000。超出限制会引发 `ActionFailed` 异常。只读取 `selection.filters` 和 `selection.q` 的处理函数不会物化任何数据，因此不受该上限约束。

## 行级动作 {#row-actions}

行级动作让用户可以直接从列表视图对单个条目进行操作。`starlette-admin` 默认包含三个行级动作：`view`、`edit` 和 `delete`。

要添加自定义行级动作，请编写你的逻辑并应用 `@row_action` 装饰器。当动作只是将用户跳转到另一个 URL 时，请改用 `@link_row_action` 装饰器。它会将该链接嵌入 HTML 的 `href` 属性中，并跳过动作 API。

!!! important
    行级动作的名称在同一个 `ModelView` 内必须唯一。

### 行级动作示例

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"
```

### 限制行级动作

有两个钩子决定一个行级动作是否可用。二者默认都允许该动作。

1. **`is_row_action_allowed(request, name)`**：每个动作名称运行一次。用于不依赖于行的限制，例如基于角色的访问控制。
2. **`is_row_action_allowed_for_obj(request, name, obj)`**：对通过了第一层检查的动作，每一行运行一次。用于依赖数据的限制，例如在已发布的文章上隐藏 **Publish** 按钮。

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)
```

!!! warning
    对于你的重写未处理的动作名称，务必调用 `super()`。否则，你会在无意间禁用内置动作的权限检查。

## 行级动作的 UI 配置

### 显示类型

`row_actions_display_type` 参数设置动作在列表页上的显示方式。详情页上的动作始终渲染为完整按钮。

| 显示类型       | 描述                                                                   |
| -------------- | ---------------------------------------------------------------------- |
| `ICON_LIST`    | 渲染一排仅含图标的水平按钮列表。                                       |
| `DROPDOWN`     | 将动作归入一个带标签的下拉菜单。                                       |
| `KEBAB`        | 将动作归入一个由 `⋮` 图标打开的下拉菜单。                              |
| `INLINE_LINKS` | 在图标下方渲染动作标签，以中间点分隔。                                 |

### 列位置

默认情况下，动作列渲染在你的数据列之前。要将它移到表格右侧，请使用 `RowActionsPosition`：

```python
from starlette_admin.types import RowActionsPosition


class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS
```

## 动态动作表单

`@action` 和 `@row_action` 装饰器上的 `form` 参数都接受可调用对象，因此你可以在请求时生成 HTML。

该可调用对象可以是同步或异步的，并且必须返回字符串。

- **`@action` 签名**：`(request) -> str`
- **`@row_action` 签名**：`(request, obj) -> str`

当你想用某行的当前值预填表单输入项时，可以使用可调用对象。

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]
```

!!! important
    列表页上的每一行都会运行一次行级动作的表单可调用对象。请保持其高效，避免在其中执行数据库查询。你所需的行数据已经可以通过 `obj` 参数获得。
