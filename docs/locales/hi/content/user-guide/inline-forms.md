---
title: Inline Forms
description: InlineModelView का उपयोग करके parent model के create/edit फ़ॉर्म के भीतर
  ही related models inline प्रबंधित करें।
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# Inline Forms

Inline forms users को parent model के create या edit page से ही related records manage करने देते हैं। ये उन child models के लिए उपयुक्त हैं जो केवल अपने parent के साथ ही meaningful होते हैं — जैसे article पर comments या project में tasks — और child model के लिए अलग admin view बनाने से आपको बचाते हैं।

इस पेज के तीनों patterns — auto-detected foreign key, explicit foreign key, और composite foreign key — cover करने वाले runnable app के लिए [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) देखें।

## एक minimal inline {#a-minimal-inline}

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

यह setup दो steps लेता है: child model के लिए `InlineModelView` subclass define करें, फिर उसे parent के `ModelView` की `inlines` list में जोड़ें।

`ArticleView` के create/edit pages अब article के अपने fields के नीचे एक `Comments` formset render करते हैं। Formset एक empty row (`extra = 1`) से शुरू होता है और add/delete controls include करता है जिन्हें SQLAlchemy backend आपके लिए wire up करता है।

ध्यान दें कि `CommentInline` ने कभी `fk_attr` सेट नहीं किया। SQLAlchemy backend `Article.comments` inspect करके `Comment.article_id` को foreign key infer कर लेता है, क्योंकि `Comment` की ओर इशारा करने वाला वही अकेला relationship है। `fk_attr` स्वयं तभी सेट करें जब inference अस्पष्ट (ambiguous) हो, या ORM model पर relationship declared न हो। [Explicit and composite foreign keys](#explicit-and-composite-foreign-keys) देखें।

## `InlineModelView` संदर्भ {#inlinemodelview-reference}

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | ORM model class | `None` | The related model this inline manages. Required. |
| `fk_attr` | `str \| tuple[str, ...]` | `""` | Name of the foreign-key field on the inline model that points to the parent. A tuple declares a composite foreign key. Optional on the SQLAlchemy backend, which auto-detects it from the parent's relationship when you omit it. |
| `extra` | `int` | `0` | Number of empty rows shown on create and edit forms, in addition to existing rows. |
| `allow_delete` | `bool` | `True` | Show a delete checkbox or button on each existing row. |
| `inline_template` | `str` | `"inline.html"` | Template used to render the formset. |
| `collapsible` | `bool` | `True` | Whether users can expand and collapse the formset. |
| `collapsed` | `bool` | `False` | Initial collapsed state. Applies only when `collapsible=True`. |


जब आप `fk_attr` खाली छोड़ें और backend relationship को unambiguously resolve न कर सके, constructor `ValueError` raise करता है।

## Collapsible formsets

डिफ़ॉल्ट रूप से (`collapsible = True`) हर `InlineModelView` अपना formset ऐसे header के साथ render करता है जिसे users select करके अनचाहे child records collapse कर सकते हैं। Formset open के बजाय closed शुरू कराने के लिए `collapsed = True` सेट करें:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Formset को entirely opt-out करने के लिए `collapsible = False` सेट करें — तब वह हमेशा expanded render होगा, toggle के बिना:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Explicit और composite foreign keys {#explicit-and-composite-foreign-keys}

जब parent का उसी child model से एक से अधिक relationships हों, जब ORM model पर relationship declared न हो, या जब foreign key composite हो, तब `fk_attr` स्वयं सेट करें:

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

ध्यान दें कि `OrderLineInline` को `fk_attr` की आवश्यकता नहीं है, भले हि `OrderLine` की primary key composite (`order_store_id`, `order_seq`, `line_no`) है। SQLAlchemy backend `Order` और `OrderLine` के बीच `ForeignKeyConstraint` से composite foreign key resolve करके नई rows पर दोनों columns populate करता है। `fk_attr` को `tuple[str, ...]` तभी पास करें जब constraint introspection कोई match न पाए।

## Validation

प्रत्येक submitted row अपने आप validate होती है — standalone `ModelView` वहीं `create`/`edit` paths से। Admin पहले parent save करता है, फिर हर inline row क्रमवार process करता है। एक comment के `author` field में typo बाकी comments को process होने से नहीं रोकता। जब किसी row की validation fail होती है, errors उस row से attach होते हैं, और form submitted values के साथ उस row को वहीं re-render करता है ताकि users उस entry को ठीक करके फिर submit कर सकें।

!!! important
    SQLAlchemy backend पर पूरा request all-or-nothing होता है। Parent और हर inline row उसी request-scoped session को share करते हैं, और वह session तभी commit होता है जब पूरा request succeed करे। यदि किसी row की validation fail होती है, response error return करता है और session rollback हो जाता है — parent और सारे inline rows (validation pass करने वाली rows सहित) एक साथ revert हो जाते हैं। UI के per-row errors को ठीक करने की list समझें, saved हुए का record नहीं।

---

## आगे क्या {#whats-next}

* **[SQLAlchemy](../integrations/sqlalchemy.md):** Relationship introspection automatic foreign key detection कैसे सक्षम करती है।
* **[Custom Views](custom-views.md):** Standard create/edit/list workflow से आगे के pages बनाएँ।
* **[इवेंट](../advanced/events.md):** Records save होने के बाद inline बदलावों पर प्रतिक्रिया दें।
