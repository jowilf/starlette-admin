---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# 使用 FastAPI 与 starlette-admin 实现软删除和回收站视图

_2026-07-10_

标准的 `DELETE` 操作是不可挽回的。如果操作员误点了一下，或者某个自动化清理任务用错了过滤器，数据就会丢失，除非你执行一次复杂的数据库恢复。实现"软删除"可以缓解这一风险：它只是把记录标记为已删除，而不是将其从数据库中永久移除。这样一来，数据恢复就变成了一次简单的更新操作。

本指南演示如何在 FastAPI 应用中借助 `starlette-admin` 实现软删除模式。我们将构建一个完整的解决方案，其中用到：

- 单个数据库模型
- 两个彼此独立的管理视图
- 一个 `deleted_at` 时间戳
- 一个专用的回收站界面，用于恢复或永久清除记录

**查看完整的可运行代码：**[`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete)。

## 模型

在想要保护的表中添加一个可为空的时间戳列。`NULL` 值表示记录处于活跃状态，而时间戳有值则表示记录已被删除：

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

这种方式既不需要单独的回收站表，也不需要外部的软删除 mixin 库。单单一个列就能管理整个状态机。

## 在活跃视图中隐藏已删除的行

`ModelView` 类使用可覆盖的方法来构建它的列表、计数和详情查询。`get_detail_query` 默认取自 `get_list_query`，因此对列表查询的过滤也会作用于详情页面，包括直接访问的 URL。`get_count_query` 则是独立的，必须单独过滤。把这些查询都过滤为只包含 `deleted_at IS NULL` 的记录，就能有效地把软删除的行从列表页面、分页计数和直达的详情链接中隐藏掉：

```python title="app.py" hl_lines="7-8 10-11"
class PostView(ModelView):
    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at", "created_at"]
    exclude_fields_from_edit = ["deleted_at", "created_at"]
    fields_default_sort = [("created_at", True)]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(Post.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(Post.deleted_at.is_(None))
```

你还必须把 `deleted_at` 从创建和编辑表单中排除。操作员绝不应该手动设置这个字段；它只应通过 `delete()` 方法和恢复动作以编程方式进行修改。

!!! warning
缺少 `get_count_query` 会造成数据可见性泄露：分页和搜索结果的统计总数会把已删除的行计算在内，尽管它们并不会在列表中渲染。这里的 `get_detail_query` 不需要单独覆盖，因为它默认取自 `get_list_query`，会自动继承同一个过滤器。不过，如果你确实为某个视图提供了自定义的 `get_detail_query`，它就不再继承 `get_list_query`，必须自行过滤 `deleted_at`。

## 重新定义删除

内置的批量删除动作和行级删除按钮都会调用 `ModelView.delete()`。覆盖这个方法，即可在所有入口点全局重新定义删除行为，且无需任何额外配置：

```python title="app.py" hl_lines="6-7 11"
async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()
    for obj in objs:
        await self._emit_after_delete(request, obj.id, obj)
    return len(objs)
```

`_emit_before_delete` 和 `_emit_after_delete` 调用保证了[事件总线](../../advanced/events.md)的触发方式与物理删除时完全一致。因此，`AdminEvent.AFTER_DELETE` 的订阅者（例如审计日志或 webhook）无需知道这次删除其实是软删除。真正变化的是数据库行层面的影响，生命周期事件则保持一致。

### AFTER_DELETE_COMMITTED 需要单独接线

`BEFORE_DELETE` 和 `AFTER_DELETE` 事件并不代表完整的生命周期。SQLAlchemy 的基类 `ModelView.delete()` 方法还会注册一个 `on_commit` 回调。事务成功提交后，该回调便会触发 `AFTER_DELETE_COMMITTED` 事件，让订阅者可以放心地认为这一行已被永久移除。

由于 `PostView` 示例完全覆盖了 `delete()`，默认的 `on_commit` 注册便被绕开了。因此，在支持软删除的视图上监听 `AdminEvent.AFTER_DELETE_COMMITTED` 的处理器将静默地不再触发。

要找回这项功能，你必须手动注册基类实现所使用的同一个回调：

```python title="app.py" hl_lines="16-17 20 22"
from collections.abc import Callable

from starlette_admin.helpers import on_commit


async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()

    def _make_after_delete_committed(obj: Post, pk: Any) -> Callable[[], Any]:
        return lambda: self._emit_after_delete_committed(request, pk, obj)

    for obj in objs:
        pk = obj.id
        await self._emit_after_delete(request, pk, obj)
        on_commit(request, _make_after_delete_committed(obj, pk))
    return len(objs)
```

`_make_after_delete_committed` 辅助函数接受 `obj` 和 `pk` 作为普通参数传入。每一行都会用它自己那一行的值各调用一次。这个结构至关重要。如果直接在循环体内构造 lambda，它闭包引用的将是循环变量本身，而不是该次迭代时的值。结果就是，循环结束后触发的每个回调使用的都是 `obj` 和 `pk` 的最终值。把它们作为实参传给外层函数，才能在调用时刻精确捕获它们的状态。

软删除的一个优势恰好体现在这里。物理删除必须在安排 committed 回调之前先把对象分离出去（`session.expunge`）。被物理删除的行到了提交时已经不复存在，此时访问未加载的属性会抛出 `ObjectDeletedError`。而软删除从不移除行，对象始终与会话保持关联，回调内部可以安全地读取所有属性。

不过，`on_commit` 的首要规则依然适用：回调不得使用 `request.state.session` 写入数据库。那个会话已经完结。任何被 flush 到该会话的内容都会开启一个新事务，而这个事务会在会话关闭时被丢弃。

## 同一张表的第二个视图

`TrashView` 指向的还是同一个 `Post` 模型，但以一个唯一的 `key` 注册。这一配置告诉 `starlette-admin` 把它当作一项独立的资源来对待，拥有单独的 URL 和菜单入口：

```python title="app.py" hl_lines="8 11"
class TrashView(ModelView):
    menu_label = "Trash"
    icon = "fa fa-trash"
    fields_default_sort = [("deleted_at", True)]
    actions = ["restore", "delete"]

    def get_list_query(self, request: Request):
        return select(Post).where(Post.deleted_at.isnot(None))

    def get_count_query(self, request: Request):
        return select(func.count()).select_from(Post).where(Post.deleted_at.isnot(None))

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False
```

这些查询与 `PostView` 的查询恰好互为镜像，过滤条件是 `IS NOT NULL` 而不是 `IS NULL`。`get_detail_query` 同样默认取自 `get_list_query`，因此被丢进回收站的记录在其详情页面上也能正确解析，无需单独覆盖。`can_create` 和 `can_edit` 方法返回 `False`，因为操作员绝不应该直接在回收站里创建或编辑记录。记录只能经由 `PostView.delete()` 进入回收站，再通过恢复动作或永久清除离开。

## 恢复，以及保留真正删除的理由

`TrashView` 在自己的 `actions` 列表中保留了内置的 `delete` 动作，并且没有覆盖它。在回收站视图中执行 `delete` 时，运行的是标准的 SQL `DELETE`。这相当于一次永久清除。一行数据一旦从回收站中被移除，就彻底消失了。

恢复一条记录需要一个简短的[自定义动作](../../user-guide/actions.md)来清空 `deleted_at` 时间戳：

```python title="app.py" hl_lines="12"
@action(
    name="restore",
    text="Restore",
    confirmation="Restore the selected posts?",
    submit_btn_text="Yes, restore",
    submit_btn_class="btn btn-success",
)
async def restore_action(self, request: Request, pks: list[Any]) -> None:
    session: Session = request.state.session
    objs = await self.find_by_pks(request, pks)
    for obj in objs:
        obj.deleted_at = None
        session.add(obj)
    session.flush()
    count = len(objs)
    flash(request, f"{count} post{'s' if count != 1 else ''} restored.", "success")
```

执行 `deleted_at = None` 之后，这一行会在下一次请求时立即回到活跃的 `PostView` 列表中，因为主视图只查询 `NULL` 值。

## 把两个视图接到同一张表上

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

这一配置为同一张数据库表建立了两个彼此独立的管理视图。由单独一列决定每个特定的行显示在哪一个视图中。

## 这种模式的局限所在

- **唯一约束：**如果 `slug` 这类字段上存在 `UNIQUE` 约束，那么只要软删除的版本还留在回收站里，操作员就无法用相同的 slug 重新创建一篇活跃的文章。要解决这个问题，要么使用部分索引（如果你的数据库引擎支持的话）把 `deleted_at IS NOT NULL` 的行排除在唯一索引之外，要么把 `deleted_at` 列并入唯一约束本身。
- **外键：**被软删除的 `Post` 对于其他表中的外键关系来说仍然是一行有效数据。子记录会继续解析到它。虽然这通常正是期望的行为，但若要把软删除级联传播到相关行，就需要显式的自定义逻辑——数据库不会像物理删除时的 `ON DELETE CASCADE` 那样自动处理这种情况。
- **查询纪律：**今后每一条涉及 `Post` 模型的数据库查询都必须显式带上 `deleted_at IS NULL` 过滤器。无论是原生查询、导出任务还是别的管理视图，只要遗漏了这个过滤器，已删除的数据就会泄露进活跃的工作流。
- **数据库增长：**被软删除的行会持续占用表和索引空间。如果你的应用程序对大多数软删除的行都是清除而非恢复，可以考虑实现一个定时后台任务，对超过特定保留期的记录执行物理删除，以免数据库无限增长。

## 扩展到其他后端

这一模式的核心原则并非 SQLAlchemy 独有。凡是允许覆盖列表、计数、详情查询以及 `delete()` 方法的后端，都可以采用这种做法。例如，如果你使用的是 Beanie、MongoEngine 或 Tortoise ORM，对应的覆盖同样会以完全相同的方式基于 `deleted_at` 字段过滤查询。变化的只是具体的查询语法，架构模式则如出一辙。

---

## 下一步

- **[事件](../../advanced/events.md)：**了解 `_emit_before_delete` 和 `_emit_after_delete` 如何连接到视图之外的外部订阅者。
- **[动作](../../user-guide/actions.md)：**深入了解 `restore_action` 背后的装饰器，包括如何实现确认对话框和Flash 消息辅助函数。
- **[视图](../../user-guide/views.md)：**查阅 `ModelView` 内部可用的全套查询与权限钩子。
