---
title: Inline Forms
description: Manage related models inline directly within a parent model's create and edit forms using InlineModelView.
---

# Inline Forms

Inline forms let users manage related records directly from a parent model's create or edit page. They suit child models that only make sense next to their parent, such as comments on an article or tasks in a project, and they save you from building a separate admin view for the child model.

See [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) for a runnable app that covers all three patterns on this page: auto-detected foreign key, explicit foreign key, and composite foreign key.

## A minimal inline

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

Setting this up takes two steps: define an `InlineModelView` subclass for the child model, then add it to the `inlines` list on the parent's `ModelView`.

The `ArticleView` create and edit pages now render a `Comments` formset below the article's own fields. The formset starts with one empty row (`extra = 1`) and includes the add and delete controls that the SQLAlchemy backend wires up for you.

Note that `CommentInline` never sets `fk_attr`. The SQLAlchemy backend inspects `Article.comments` and infers `Comment.article_id` as the foreign key, because it's the only relationship that points to `Comment`. Set `fk_attr` yourself only when that inference is ambiguous, or when the relationship isn't declared on the ORM model. See [Explicit and composite foreign keys](#explicit-and-composite-foreign-keys).

## `InlineModelView` reference

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | ORM model class | `None` | The related model this inline manages. Required. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Name of the foreign-key field on the inline model that points to the parent. A tuple declares a composite foreign key. Optional on the SQLAlchemy backend, which auto-detects it from the parent's relationship when you omit it. |
| `extra` | `int` | `0` | Number of empty rows shown on create and edit forms, in addition to existing rows. |
| `allow_delete` | `bool` | `True` | Show a delete checkbox or button on each existing row. |
| `inline_template` | `str` | `"inline.html"` | Template used to render the formset. |
| `collapsible` | `bool` | `True` | Whether users can expand and collapse the formset. |
| `collapsed` | `bool` | `False` | Initial collapsed state. Applies only when `collapsible=True`. |


The constructor raises a `ValueError` when you leave `fk_attr` empty and the backend can't resolve the relationship unambiguously.

## Collapsible formsets

By default (`collapsible = True`), every `InlineModelView` renders its formset with a header that users can select to collapse child records they don't need. Set `collapsed = True` to start the formset closed instead of open:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Set `collapsible = False` to opt a formset out entirely, so it always renders expanded with no toggle:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Explicit and composite foreign keys

Set `fk_attr` yourself when the parent has more than one relationship to the same child model, when the relationship isn't declared on the ORM model, or when the foreign key is composite:

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

Note that `OrderLineInline` needs no `fk_attr`, even though the primary key for `OrderLine` is composite (`order_store_id`, `order_seq`, `line_no`). The SQLAlchemy backend resolves the composite foreign key from the `ForeignKeyConstraint` between `Order` and `OrderLine` and populates both columns on new rows. Pass a `tuple[str, ...]` to `fk_attr` only when constraint introspection finds no match.

## Validation

Each submitted row validates on its own, through the same `create` and `edit` paths a standalone `ModelView` uses. The admin saves the parent first, then processes each inline row in turn. A typo in one comment's `author` field doesn't stop the other comments from being processed. When a row fails validation, its errors attach to that row, and the form re-renders the row in place with the submitted values so users can correct and resubmit that entry.

!!! important
    On the SQLAlchemy backend, the whole request is all-or-nothing. The parent and every inline row share the same request-scoped session, and that session commits only when the entire request succeeds. If any row fails validation, the response returns an error and the session rolls back, so the parent and all inline rows revert together, including rows that passed validation. Treat the per-row errors in the UI as a list of what to fix, not as a record of what was saved.

---

## What's next

* **[SQLAlchemy](../integrations/sqlalchemy.md):** How relationship introspection enables automatic foreign key detection.
* **[Custom Views](custom-views.md):** Build pages beyond the standard create, edit, and list workflow.
* **[Events](../advanced/events.md):** React to inline changes after records are saved.
