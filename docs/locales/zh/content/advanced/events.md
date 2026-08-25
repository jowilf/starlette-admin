---
title: 事件
description: 订阅 AFTER_CREATE 等全局生命周期事件，构建审计日志、Webhook 和异步工作流。
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# 事件

像 `before_create` 这样的方法钩子只在定义它的视图中运行。事件系统让该视图之外的代码对其内部发生的事情作出反应，这意味着审计日志、Webhook 或缓存失效逻辑可以集中放在一处，而无需复制粘贴到你编写的每个 `ModelView` 中。

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

在 `admin` 实例旁边注册一次，每个视图的创建端点都会调用它，包括你之后添加的视图。

## 视图级别与 admin 级别

每个视图都有一个可以直接订阅的 `events` 属性，其作用范围仅限该视图本身。`Admin` 实例同样有一个，它作用于注册在其上的所有视图；传入 `keys=` 时则限定为其子集。

* **`view.events.on(...)`**：仅对该视图触发。
* **`admin.events.on(...)`**：对当前及未来的每个视图触发，除非你用 `keys=` 加以限制。

你可以在调用 `admin.add_view(...)` 之前或之后在 `admin.events` 上注册。顺序无关紧要：先注册的处理器在你添加视图后仍会附加到该视图。

## 方法钩子与事件订阅

两者都在请求生命周期的同一时点触发。它们的区别在于代码所在的位置以及覆盖的视图数量。

| 特性 | 方法钩子（`before_create` 等） | 事件订阅（`view.events` / `admin.events`） |
| --- | --- | --- |
| **代码位置** | 视图类内部 | 任意位置，例如模块级函数或订阅者类 |
| **作用范围** | 该特定视图 | 单个视图（`view.events`）或所有视图（`admin.events`） |
| **适用场景** | 特定于该资源的逻辑（为标题生成 slug、加盖时间戳） | 横切关注点（审计日志、通知、插件） |
| **是否允许多个？** | 不允许，每个视图一个方法 | 允许，每个事件可有任意数量的处理器，按优先级排序 |

当逻辑内在于模型本身时，使用方法钩子。当逻辑不属于任何单个视图，或者你要将其作为可复用组件用于多个 admin 实例时，使用事件订阅。

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## AdminEvent 取值

`AdminEvent` 是一个字符串枚举。以下是视图生命周期主动发出的成员：

| 事件 | 触发时机 | 上下文类 |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | 记录创建 | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | 创建事务提交 | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | 记录更新 | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | 编辑事务提交 | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | 记录删除 | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | 删除事务提交 | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | 批量或行动作执行 | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | 导出触发 | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | 导入触发 | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | 登录成功 | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`、`AFTER_EDIT_COMMITTED` 和 `AFTER_DELETE_COMMITTED` 只在将提交延迟到请求结束的后端上触发，目前即指 SQLAlchemy 后端。发出这些事件的 `after_create_committed`、`after_edit_committed` 和 `after_delete_committed` 钩子方法请参见[视图](../user-guide/views.md#lifecycle-hooks)。

对于 `AFTER_DELETE_COMMITTED`，`ctx.obj` 是一个分离实例：其已加载的属性仍然可读，但读取删除前未加载的属性会抛出异常，因为它对应的数据库行已不存在。

每个上下文都是继承自 `EventContext` 的数据类，后者携带所有事件共有的字段：

| 属性 | 类型 | 描述 |
| --- | --- | --- |
| `event` | `AdminEvent` 或 `str` | 触发的事件 |
| `request` | `Request` | 当前正在处理的请求 |
| `view_key` | `str` | 该视图的 `key` |
| `extra` | `dict` | 默认为空，供你在自定义处理器链中自由存放数据 |

每个子类都会添加与相应事件相关的字段。

从列表页面通过[行内编辑](../user-guide/inline-edit.md)触发的编辑事件会携带 `extra["inline"] = True`，且其 `data` / `old_data` 载荷只包含被编辑的字段。其余方面与常规编辑完全一致，因此现有处理器无需改动。

## 使用装饰器订阅

`view.events.on()` 既可用作装饰器，也可直接作为函数调用：

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

以这种方式注册后，`log_deletion` 仅对 `order_view` 触发，对 admin 上的其他视图不触发。`on()` 方法也可以直接接收处理器，无需装饰器形式：

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber：分组处理器

当同一个关注点需要对多个事件作出反应时，`AdminEventSubscriber` 将它们保存在一个类中，而不是分散为模块级函数。用 `@on(AdminEvent.X)` 装饰方法——这里的 `on` 是 `starlette_admin.events` 中的模块级函数而非总线方法——然后调用一次 `subscribe()`：

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` 在 `view.events` 和 `admin.events` 上都可用。若要将订阅者的作用范围限定到单个视图，请在 `view.events` 上调用。

一个方法可以处理多个事件：`@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` 会为这两个事件注册同一个方法。

## admin.events：委托给视图

`admin.events.on()` 接受与 `view.events.on()` 相同的参数，外加 `keys=`，即用于限制订阅范围的视图键列表。保持未设置（默认为 `None`）时，当前及未来的每个模型视图都会获得该处理器：

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

只有以 `key="order"` 注册的视图，或其默认键解析为 `"order"` 的视图才会调用此处理器。任何其他视图上的 `AFTER_CREATE` 都不会触发它。

`admin.events.subscribe()` 同样接受 `keys=`，因此你可以用相同的方式将 `AdminEventSubscriber` 限定到一个视图子集：

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` 只影响上表中的视图生命周期事件：创建、编辑、删除、动作、导出和导入。这正是 `admin.events` 决定处理器适用于哪些视图的方式。`AFTER_LOGIN` 是管理员级别的，不绑定任何视图，因此 `keys=` 对它无效。

## 优先级

`on()` 接受 `priority` 关键字参数，一个默认为 `0` 的整数。同一事件的处理器按优先级降序运行，因此数值越大越先触发：

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

优先级相同的处理器按注册顺序运行。`AdminEventSubscriber` 的方法通过 `@on(AdminEvent.X, priority=10)` 指定优先级，并以相同方式转发。

!!! warning
    抛出异常的 `BEFORE_DELETE` 处理器（或任何 `BEFORE_*` 处理器）会中止操作，该事件的后续处理器不会运行。抛出异常的 `AFTER_*` 处理器会将已提交的更改变成失败的请求。如果失败不应显示为管理员错误，请在处理器内部将网络调用或第三方 API 等有风险的逻辑包在自己的 `try`/`except` 块中。

## 扩展示例

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) 将本页介绍的所有模式整合在一起：`PostView` 上的钩子重写、注册到 `admin.events` 并对所有视图生效的 `AuditSubscriber`、针对删除以及导出和导入警告的直接处理器注册、限定作用域到 `post_view.events` 的处理器，以及限定作用域到 `comment_view.events` 的 `CommentModerationSubscriber`。运行它即可在一个应用中观察优先级与作用范围的交互。

---

## 下一步

* **[视图](../user-guide/views.md)**：本页所依赖的 `before_*` 和 `after_*` 方法钩子。
* **[动作](../user-guide/actions.md)**：批量动作和行动作，它们会发出 `BEFORE_ACTION` / `AFTER_ACTION`。
* **[行内表单](../user-guide/inline-forms.md)**：随父记录一起创建的嵌套记录。
