---
title: 内联表单
description: 使用 InlineModelView 直接在父模型的创建和编辑表单中内联管理关联模型。
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# 内联表单

内联表单让用户可以直接在父模型的创建或编辑页面中管理关联记录。它们适合那些只有与父模型一起出现才有意义的子模型，例如文章的评论或项目中的任务，同时免去为子模型单独构建管理视图的工作。

可运行的示例应用参见 [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms)，它涵盖了本页的全部三种模式：自动检测的外键、显式外键和复合外键。

## 最简内联示例

```python hl_lines="40-43"
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.requests import Request
from starlette_admin.contrib.sqla import InlineModelView, ModelView


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="article", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"))
    author: Mapped[str] = mapped_column(String(100), default="Anonymous")
    body: Mapped[str] = mapped_column(Text)

    article: Mapped["Article"] = relationship("Article", back_populates="comments")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.author}: {self.body[:50]}"


class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1


class ArticleView(ModelView):
    fields = ["title", "body"]
    inlines = [CommentInline]
```

完成这项设置只需两步：为子模型定义一个 `InlineModelView` 子类，然后将它添加到父模型 `ModelView` 的 `inlines` 列表中。

`ArticleView` 的创建和编辑页面现在会在文章自身字段下方渲染一个 `Comments` 表单集。该表单集以一个空行开始（`extra = 1`），并带有由 SQLAlchemy 后端为你接好的添加和删除控件。

注意，`CommentInline` 从未设置 `fk_attr`。SQLAlchemy 后端会检查 `Article.comments` 并推断出 `Comment.article_id` 作为外键，因为这是唯一指向 `Comment` 的关联关系。只有在这种推断存在歧义，或者 ORM 模型上没有声明该关联关系时，才需要自行设置 `fk_attr`。参见[显式外键与复合外键](#explicit-and-composite-foreign-keys)。

## `InlineModelView` 参考

| 属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `model` | ORM 模型类 | `None` | 此内联所管理的关联模型。必填。 |
| `fk_attr` | `str | tuple[str, ...]` | `""` | 内联模型上指向父模型的外键字段名称。元组表示复合外键。在 SQLAlchemy 后端上可省略，省略时会从父模型的关联关系自动检测。 |
| `extra` | `int` | `0` | 除现有行之外，在创建和编辑表单中显示的空行数量。 |
| `allow_delete` | `bool` | `True` | 在每个现有行上显示删除复选框或按钮。 |
| `inline_template` | `str` | `"inline.html"` | 用于渲染表单集的模板。 |
| `collapsible` | `bool` | `True` | 用户是否可以展开和折叠表单集。 |
| `collapsed` | `bool` | `False` | 初始折叠状态。仅在 `collapsible=True` 时生效。 |


当你将 `fk_attr` 留空且后端无法明确解析关联关系时，构造函数会抛出 `ValueError`。

## 可折叠的表单集

默认情况下（`collapsible = True`），每个 `InlineModelView` 渲染的表单集都带有一个标题栏，用户可以点选它来折叠不需要的子记录。设置 `collapsed = True` 可以让表单集初始处于收起状态而不是展开状态：

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

设置 `collapsible = False` 可以完全禁用某个表单集的折叠功能，使其始终以展开方式渲染且没有切换开关：

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## 显式外键与复合外键 {#explicit-and-composite-foreign-keys}

当父模型对同一子模型有多条关联关系、ORM 模型上没有声明关联关系，或者外键是复合的时候，请自行设置 `fk_attr`：

```python hl_lines="40-44 89-92"
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.requests import Request
from starlette_admin import StringField
from starlette_admin.contrib.sqla import InlineModelView, ModelView


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class TaskInline(InlineModelView):
    model = Task
    fk_attr = "project_id"
    fields = ["title", "done"]
    extra = 2


class ProjectView(ModelView):
    fields = [StringField("name")]
    inlines = [TaskInline]


class Order(Base):
    __tablename__ = "orders"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String(100))

    lines: Mapped[list["OrderLine"]] = relationship(
        "OrderLine", back_populates="order", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Order #{self.store_id}-{self.seq} ({self.customer})"


class OrderLine(Base):
    __tablename__ = "order_lines"

    order_store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product: Mapped[str] = mapped_column(String(100))
    qty: Mapped[int] = mapped_column(Integer, default=1)

    order: Mapped["Order"] = relationship("Order", back_populates="lines")

    __table_args__ = (
        ForeignKeyConstraint(
            ["order_store_id", "order_seq"],
            ["orders.store_id", "orders.seq"],
        ),
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Line {self.line_no}: {self.product} x {self.qty}"


class OrderLineInline(InlineModelView):
    model = OrderLine
    fields = ["line_no", "product", "qty"]
    extra = 1


class OrderView(ModelView):
    fields = ["store_id", "seq", "customer"]
    inlines = [OrderLineInline]
```

注意，尽管 `OrderLine` 的主键是复合的（`order_store_id`、`order_seq`、`line_no`），`OrderLineInline` 也不需要设置 `fk_attr`。SQLAlchemy 后端会根据 `Order` 与 `OrderLine` 之间的 `ForeignKeyConstraint` 解析出复合外键，并为新行填充这两列。只有当约束自省找不到匹配时，才向 `fk_attr` 传入 `tuple[str, ...]`。

## 校验

每个提交的行都会独立校验，走的是与独立 `ModelView` 相同的 `create` 和 `edit` 路径。管理后台会先保存父模型，再依次处理每个内联行。某条评论的 `author` 字段出现笔误并不会阻止其他评论的处理。当某行校验失败时，错误会附着在该行上，表单会带着提交的值原位重新渲染该行，以便用户更正并重新提交该条目。

!!! important
    在 SQLAlchemy 后端上，整个请求是全有或全无的。父模型和每个内联行共享同一个请求作用域的 session，且该 session 只有在整个请求成功时才会提交。如果任何一行校验失败，响应会返回错误并且 session 回滚，因此父模型和所有内联行会一起恢复原状，包括已通过校验的行。请把界面中按行显示的错误当作待修复事项的清单，而不是已保存内容的记录。

---

## 接下来

* **[SQLAlchemy](../integrations/sqlalchemy.md)：** 关联关系自省如何实现自动外键检测。
* **[自定义视图](custom-views.md)：** 构建超越标准创建、编辑和列表工作流的页面。
* **[事件](../advanced/events.md)：** 在记录保存后对内联变更做出响应。
