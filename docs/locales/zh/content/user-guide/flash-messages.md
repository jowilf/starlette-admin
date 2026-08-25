---
title: Flash 消息
description: 在 starlette-admin 中完成动作后向用户发送临时的成功、警告或错误提示。
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Flash 消息

Flash 消息为用户执行某个动作后提供临时的一次性反馈，例如“文章创建成功”或“文件类型无效”。消息在一次 HTTP 重定向中得以保留，并在显示后被管理后台丢弃。

`flash()` 会将消息加入当前请求的队列。管理后台在用户看到的下一个页面中渲染这条消息，随后清空队列。这一模式源自 Flask-Admin。


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash

class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Queue the message for the next page load
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")

```

## 消息类别

每条 Flash 消息都需要一个类别。类别决定了默认主题下横幅的颜色，用户可以据此一眼判断严重程度。

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

`category` 参数默认为 `"info"`。它必须恰好是 `success`、`info`、`warning` 或 `error` 之一。其他任何值都会引发 `ValueError`。

## 内置 CRUD 消息

对于标准 CRUD 操作，你无需调用 `flash()`。这些动作完成时，管理后台会自动闪现一条 `success` 消息：

| 动作 | 默认消息 |
| --- | --- |
| **新建** | `The item "<repr>" was added successfully.` |
| **编辑** | `The item "<repr>" was changed successfully.` |
| **删除（单个）** | `The item "<repr>" was successfully deleted.` |
| **删除（批量）** | `%(count)d items were successfully deleted.` |

!!! note "`<repr>` 所指代的内容"
    自动消息使用的是 `view.repr()` 定义的行表示形式，而不是模型的类名。例如，创建一篇文章时闪现的消息是 *"The item 'My First Post' was added successfully"*，而不是笼统的 *"Post was added successfully"*。

## 在自定义动作中使用 Flash 消息

自定义动作（`@action` 和 `@row_action`）的处理程序默认返回 `None`。若要向用户提供反馈，请在处理程序返回之前调用 `flash()`。

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash

class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Notify the user that the custom action succeeded
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **如果省略 `flash()`：**动作仍会执行，但页面重定向后用户得不到任何视觉确认。
* **如果动作失败：**当自定义动作抛出 `ActionFailed` 时，管理后台会拦截该异常，并将异常字符串显示为错误横幅。请不要在 `ActionFailed` 分支中调用 `flash()`，因为请求不会发生重定向。

## 在自定义模板中渲染消息

管理后台的基础模板会替你弹出并渲染 Flash 消息。只有当你构建完整的[自定义视图](custom-views.md)时，才需要自行获取它们。

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

读取 Flash 队列的操作是**破坏性的**。第一次调用 `get_flashed_messages(request)` 时会弹出并清空队列。同一请求中的后续调用将返回空列表 `[]`。

!!! important "保持消息简短"
    Flash 消息保存在名为 `admin_flash` 的签名 `httponly` cookie 中，而不是服务器会话中。浏览器将 cookie 大小限制在约 4 KB 左右，因此请仅在需要简要反馈时使用 Flash 消息，避免长字符串和大型数据载荷。这种基于 cookie 的方式也意味着，即使没有 `SessionMiddleware`，Flash 消息也能正常工作。

> 请参阅 [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions)，这是一个从钩子和自定义动作中调用 `flash()` 的可运行应用。

---

## 下一步

* **[动作](actions.md)**：通过批量动作或行级动作触发业务逻辑。
* **[安全](security.md)**：了解 `secret_key` 如何同时保护 Flash cookie 和 CSRF 令牌。
* **[模板](../advanced/templates.md)**：在你自己的布局中渲染 Flash 横幅。
