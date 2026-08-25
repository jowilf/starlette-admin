---
title: 自定义后端集成
description: 了解如何为 starlette-admin 构建自定义后端适配器，把你自己的 ORM 或 API 数据存储接入管理界面。
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# 自定义后端

`starlette-admin` 为 SQLAlchemy、SQLModel、Beanie、MongoEngine 和 Tortoise ORM 提供了内置后端，但管理面板本身完全与存储无关。每个后端都只是 `BaseModelView` 的一个子类。该类将标准 CRUD 操作转换为目标数据源能够理解的命令。无论你使用的是 REST API、Redis、没有 ORM 的遗留数据库，还是 TinyDB 这类轻量级文档存储，实现过程都是相同的。

## 必须实现的方法

`BaseModelView` 要求你实现六个抽象方法。提供这六个方法后，你即可自动获得管理界面的全部功能：列表、搜索、排序、过滤、分页、创建、编辑、导入、导出和删除。

```python
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.filters import FilterGroup
from starlette_admin.views import BaseModelView


class MyBackendView(BaseModelView):
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        ...

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        ...

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        ...

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        ...

    async def create(self, request: Request, data: dict) -> Any:
        ...

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        ...

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ...

```

| 方法 | 调用场景 | 返回值 |
| --- | --- | --- |
| **`find_all`** | 列表页、导出 | 匹配 `q`、`sorts` 和 `filters` 的一页记录 |
| **`count`** | 列表页分页、导出上限检查 | 匹配 `q` 和 `filters` 的记录总数 |
| **`find_by_pk`** | 详情、编辑、单条删除、行动作 | 单条记录，未找到时为 `None` |
| **`find_by_pks`** | 批量动作、批量删除、导出选中项 | 与给定主键匹配的一组记录 |
| **`create`** | 创建表单提交、导入 | 新创建的记录 |
| **`edit`** | 编辑表单提交 | 更新后的记录 |
| **`delete`** | 批量删除、行删除 | 已删除的记录数，或 `None` |

管理后台会在内部解析请求的查询字符串（例如 `?page=2&sort=views__desc&q=fire`）。你无需解析原始请求参数。等到调用 `find_all` 或 `count` 时，管理后台已经处理好了各项输入：

* **分页**被转换为 `skip` 和 `limit`（`skip = (page - 1) * page_size`）。
* **搜索**以纯字符串 `q` 的形式提供。
* **排序**被格式化为按优先级排列的 `(field_name, direction)` 元组列表。
* **过滤器**被解析为结构化的 `FilterGroup` 树。

你唯一的任务，是将这些结构化参数转换为你所用后端的原生查询语言。

## 视图 key、显示名称与字段

在渲染之前，`ModelView` 需要四个核心属性来理解数据结构和路由：

| 属性 | 用途 |
| --- | --- |
| **`key`** | 唯一的 URL slug（例如 `/admin/post/list`），同时也是事件订阅所用的内部键。 |
| **`display_name`** / **`menu_label`** | UI 显示名称。`display_name` 为单数形式，用于表单标题；`menu_label` 为复数形式，用于导航和列表页。 |
| **`pk_attr`** | 唯一标识一条记录的字段名。 |
| **`fields`** | `BaseField` 实例列表，定义要显示和编辑的列。 |

内置后端通过内省你的模型自动填充这些属性。例如，SQLAlchemy 的 `ModelView` 会读取 mapper 的列和主键。这一内省过程由 `BaseModelConverter` 的子类完成。这些转换器使用 `@converts(...)` 装饰器将原生列类型映射到对应的 `BaseField`。

构建没有可内省模型的后端（例如 REST API 或纯字典存储）时，必须将这四个属性显式设置为类属性：

```python
class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
    ]

```

对于一次性视图，显式列出字段是最简单的方式。但如果你要构建一个可复用的 `ModelView` 基类，以支持自定义后端上的多个模型，则应改为编写自定义的 `BaseModelConverter`：实现 `convert()` 和 `convert_fields_list()` 方法，用 `@converts(...)` 装饰类型处理器，并在初始化时调用转换器。这样具体视图即可自动继承字段定义，与内置后端的行为保持一致。

## 处理过滤树

过滤器以 `FilterGroup` 的形式传入你的方法。该结构是一棵由逻辑 AND/OR 节点组成的树，其中包含作为叶节点的 `FilterRule` 对象：

```python
@dataclass
class FilterRule:
    field: str
    filter: str         # The slug of the BaseFilter to apply (e.g., "contains", "gte")
    value: Any = None
    value2: Any = None  # Only populated for filters with has_value2 (e.g., "between")

@dataclass
class FilterGroup:
    logic: str = "and"  # Accepts "and" or "or"
    rules: list["FilterGroup | FilterRule"] = field(default_factory=list)

```

要把这棵树转换为数据库查询，必须递归遍历它。对每个 `FilterRule`，从你的 `FilterRegistry` 中取出匹配的具体过滤器类并调用其 `apply()` 方法；对嵌套的 `FilterGroup` 节点则递归处理，并用相应的逻辑运算符组合得到的片段。

下面是 TinyDB 参考示例所使用的 `build_query` 模式：

```python
def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (combined | fragment) if group.logic == "or" else (combined & fragment)
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)

```

每个具体过滤器的 `apply(ctx)` 方法都会接收一个包含 `query`、`field name` 和 `values` 的 `FilterApplyContext` 对象，并返回一段特定于你所用的后端查询语言的查询片段。由于这一过程不会修改共享状态，因此无论底层数据库架构如何，都能干净地组合出最终的规则。

## TinyDB 参考示例

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) 包含一个基于 [TinyDB](https://github.com/msiemens/tinydb) 的完整可运行管理面板。TinyDB 是一种把数据保存到本地 JSON 文件的文档存储。它没有 ORM，每个方法都直接与数据存储交互，因此是一个极佳的参考范例。

### 模型定义（`models.py`）

数据模型是一个标准的 Python dataclass，不含任何专用于管理功能的逻辑：

```python
@dataclass
class Post:
    title: str
    body: str
    tags: list[str]
    views: int = 0
    comments: list[Comment] = field(default_factory=list)
    cover: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags))
        )

```

`search_query` 方法通过在相关字段上生成全文搜索来处理 `q` 参数。

### 视图实现（`view.py`）

`PostView` 实现使用 `_build_query` 把搜索查询与过滤树合并在一起。`find_all` 和 `count` 在执行 TinyDB 搜索之前都依赖这个辅助方法：

```python
async def _build_query(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> QueryInstance | None:
    query = None
    if q is not None:
        query = Post.search_query(q)
    if filters is not None and not filters.is_empty():
        fields_by_name = {field.name: field for field in self.get_fields_list(request)}
        filter_query = build_query(filters, fields_by_name, self.get_filter_registry())
        if filter_query is not None:
            query = filter_query if query is None else (query & filter_query)
    return query

async def find_all(
    self,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sorts: list[tuple[str, str]] | None = None,
    filters: FilterGroup | None = None,
) -> Sequence[Any]:
    query = await self._build_query(request, q, filters)
    docs = self.db.search(query) if query is not None else self.db.all()
    values = [Post.from_document(doc) for doc in docs]
    for sort_by, sort_dir in reversed(sorts or []):
        values.sort(
            key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
            reverse=(sort_dir == "desc"),
        )
    if limit > 0:
        return values[skip : skip + limit]
    return values[skip:]

async def count(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> int:
    query = await self._build_query(request, q, filters)
    return len(self.db.search(query)) if query is not None else len(self.db.all())

```

由于 TinyDB 缺少原生排序能力，排序逻辑在 Python 中执行。按相反顺序依次应用各项排序即可得到可靠的多键排序。

写操作（`create`、`edit`、`delete`）直接修改数据库。关键在于，它们还会触发视图的事件钩子，从而确保生命周期事件正确触发：

```python
async def create(self, request: Request, data: dict) -> Any:
    await self.validate_data(data)
    obj = Post(**data)
    await self._emit_before_create(request, data, obj)
    new_id = self.db.insert(obj.to_dict())
    obj = await self.find_by_pk(request, new_id)
    await self._emit_after_create(request, obj)
    return obj

async def delete(self, request: Request, pks: list[Any]) -> int | None:
    ids = list(map(int, pks))
    objs = [Post.from_document(self.db.get(doc_id=i)) for i in ids if self.db.contains(doc_id=i)]
    for obj in objs:
        await self._emit_before_delete(request, await self.get_pk_value(request, obj), obj)
    removed = self.db.remove(doc_ids=ids)
    for obj in objs:
        await self._emit_after_delete(request, await self.get_pk_value(request, obj), obj)
    return len(removed)

```

### 应用组装（`app.py`）

你不需要专门的 `Admin` 子类。基础的 `Admin` 即可通用，因为 `BaseModelView` 抽象掉了所有后端细节：

```python
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB
from view import PostView

db = TinyDB(Path(__file__).parent / "db.json")

app = Starlette()
admin = Admin(debug=True, secret_key="123456")
admin.add_view(PostView(db))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

要测试此实现，请在示例目录中运行 `uv run app.py`，然后访问 `http://localhost:8000/admin/`。

## 自定义字段过滤器

过滤器与你所用后端的具体语法紧密相关。"contains" 操作在 TinyDB、SQL 和 MongoDB 中需要截然不同的代码。每个自定义后端都必须在 `FilterRegistry` 中注册自己的 `BaseFilter` 子类，并通过 `get_filter_registry()` 返回它们。

要创建过滤器，请子类化 `EqualFilter` 或 `ContainsFilter` 等基础类型，并实现 `apply` 方法：

```python
import re

from starlette_admin.filters import FilterApplyContext
from starlette_admin.filters.string import ContainsFilter
from tinydb import Query
from tinydb.queries import QueryInstance


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return Query()[ctx.field_name].search(re.escape(ctx.value), flags=re.IGNORECASE)

```

构建注册表的最佳实践是继承 `FilterRegistry`，并用 `@filters(...)` 装饰针对特定字段类型的方法。这正是随库发布的各后端所采用的模式：

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterRegistry, filters
from starlette_admin.filters.generic import IsNotNullFilter, IsNullFilter
from starlette_admin.filters.numeric import EqualFilter, GreaterThanFilter, LessThanFilter


class TinyDBFilterRegistry(FilterRegistry):
    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type]:
        # Ensures every field is filterable by null-ness, even without specific registrations.
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type]:
        return [TinyDBContainsFilter, EqualFilter, IsNullFilter, IsNotNullFilter]

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type]:
        return [EqualFilter, GreaterThanFilter, LessThanFilter, IsNullFilter, IsNotNullFilter]


class PostView(BaseModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return TinyDBFilterRegistry()

```

如果某个字段既没有匹配的注册项，也没有显式的 `filters=[]` 覆盖，它将不可过滤。TinyDB 示例正是利用 `filters=[]` 这一覆盖技巧，有意让 `id` 字段保持不可过滤。

对于可过滤类型要到运行时才能确定的动态模式，`FilterRegistry` 还提供了命令式的 `register(field_type, *filter_classes)` 方法。

## 管理生命周期事件

自定义后端完全掌控 `create`、`edit` 和 `delete` 方法。由于 `BaseModelView` 从不直接接触你的数据源，发生写入时你必须显式通知它。否则会静默破坏两个核心系统：

1. **方法钩子：**你在 `ModelView` 上重写的 `before_create` 和 `after_create`。
2. **事件订阅者：**注册在 `view.events` 或 `admin.events` 上的处理器。

通知通过调用定义在 `BaseModelView` 上的成对辅助方法完成。每个辅助方法会先调用对应的方法钩子，再发出一个 `AdminEvent`。

| 方法 | 写入前辅助方法 | 写入后辅助方法 |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

写入前的调用接受根据提交数据构造出的内存对象。这为处理器提供了最后一次通过抛出异常拒绝写入的机会。写入后的调用则需要从数据库重新读回的已持久化对象。这也解释了为什么 TinyDB 的 `create` 方法要重新获取记录，而不是返回最初的内存对象。

另外两个辅助方法 `_emit_after_create_committed` 和 `_emit_after_edit_committed` 用于支持两阶段提交或会话语义的后端。除非你的数据库强制严格的事务边界，否则完全可以跳过这两个方法。

导出和导入操作无需手动接线事件。`BaseAdmin` 类会自动处理这些生命周期事件。

---

### 其他资源

* **[视图](../user-guide/views.md)**：探索与后端无关的 `BaseModelView` 配置选项。
* **[自定义过滤器](../advanced/custom-filters.md)**：学习如何从零开始编写并注册自定义过滤器。
* **[事件](../advanced/events.md)**：了解完整的事件订阅 API，包括方法钩子、事件总线和执行优先级。
