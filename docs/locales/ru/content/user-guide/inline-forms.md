---
title: Инлайн-формы
description: Управляйте связанными моделями инлайн прямо в формах создания и редактирования
  родительской модели с помощью InlineModelView.
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# Инлайн-формы

Инлайн-формы позволяют управлять связанными записями прямо со страницы создания или редактирования родительской модели. Они подходят для дочерних моделей, которые имеют смысл только рядом со своей родительской моделью, — например, комментарии к статье или задачи в проекте, — и избавляют вас от необходимости создавать отдельное представление администрирования для дочерней модели.

См. [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) — там находится работающее приложение, охватывающее все три шаблона с этой страницы: автоматически определяемый внешний ключ, явный внешний ключ и составной внешний ключ.

## Минимальный пример

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

Настройка состоит из двух шагов: определите подкласс `InlineModelView` для дочерней модели, затем добавьте его в список `inlines` в `ModelView` родительской модели.

На страницах создания и редактирования `ArticleView` теперь отображается набор форм `Comments` под собственными полями статьи. Набор форм начинается с одной пустой строки (`extra = 1`) и включает элементы управления добавлением и удалением, которые бэкенд SQLAlchemy настраивает за вас.

Обратите внимание: `CommentInline` никогда не задаёт `fk_attr`. Бэкенд SQLAlchemy проверяет связь `Article.comments` и выводит `Comment.article_id` как внешний ключ, потому что это единственная связь, указывающая на `Comment`. Задавайте `fk_attr` самостоятельно только тогда, когда такой вывод неоднозначен или когда связь не объявлена в ORM-модели. См. [Явные и составные внешние ключи](#explicit-and-composite-foreign-keys).

## Справочник по `InlineModelView`

| Атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `model` | класс ORM-модели | `None` | Связанная модель, которой управляет этот инлайн. Обязательный. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Имя поля внешнего ключа в инлайн-модели, которое указывает на родителя. Кортеж объявляет составной внешний ключ. Необязательно на бэкенде SQLAlchemy, который автоматически определяет его по связи родителя, если вы его опустите. |
| `extra` | `int` | `0` | Количество пустых строк, отображаемых на формах создания и редактирования в дополнение к существующим строкам. |
| `allow_delete` | `bool` | `True` | Показывать флажок или кнопку удаления на каждой существующей строке. |
| `inline_template` | `str` | `"inline.html"` | Шаблон, используемый для отображения набора форм. |
| `collapsible` | `bool` | `True` | Может ли пользователь сворачивать и разворачивать набор форм. |
| `collapsed` | `bool` | `False` | Начальное состояние свёрнутости. Применяется только при `collapsible=True`. |


Конструктор вызывает исключение `ValueError`, если вы оставляете `fk_attr` пустым, а бэкенд не может однозначно определить связь.

## Сворачиваемые наборы форм

По умолчанию (`collapsible = True`) каждый `InlineModelView` отображает свой набор форм с заголовком, который пользователь может выбрать, чтобы свернуть ненужные дочерние записи. Установите `collapsed = True`, чтобы набор форм изначально был закрыт, а не открыт:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Установите `collapsible = False`, чтобы полностью отключить сворачивание набора форм: он всегда будет отображаться развёрнутым, без переключателя:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Явные и составные внешние ключи {#explicit-and-composite-foreign-keys}

Задайте `fk_attr` самостоятельно, если у родителя есть более одной связи с одной и той же дочерней моделью, если связь не объявлена в ORM-модели или если внешний ключ составной:

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

Обратите внимание: `OrderLineInline` не требует `fk_attr`, даже несмотря на то что первичный ключ `OrderLine` составной (`order_store_id`, `order_seq`, `line_no`). Бэкенд SQLAlchemy определяет составной внешний ключ по ограничению `ForeignKeyConstraint` между `Order` и `OrderLine` и заполняет оба столбца в новых строках. Передавайте кортеж `tuple[str, ...]` в `fk_attr` только тогда, когда интроспекция ограничений не находит совпадения.

## Валидация

Каждая отправленная строка проходит валидацию независимо — через те же пути `create` и `edit`, которые использует отдельный `ModelView`. Панель администрирования сначала сохраняет родителя, а затем обрабатывает каждую инлайн-строку по очереди. Опечатка в поле `author` одного комментария не мешает обработке остальных комментариев. Когда строка не проходит валидацию, её ошибки привязываются к этой строке, а форма повторно отображает её на месте с отправленными значениями, чтобы пользователь мог исправить запись и отправить её снова.

!!! important
    На бэкенде SQLAlchemy весь запрос выполняется по принципу «всё или ничего». Родитель и все инлайн-строки используют одну сессию, привязанную к запросу, и эта сессия фиксируется только при успешном выполнении всего запроса. Если хотя бы одна строка не проходит валидацию, ответ возвращает ошибку, а сессия откатывается, поэтому родитель и все инлайн-строки возвращаются к исходному состоянию вместе — включая строки, прошедшие валидацию. Считайте ошибки отдельных строк в интерфейсе списком того, что нужно исправить, а не отчётом о том, что было сохранено.

---

## Что дальше

* **[SQLAlchemy](../integrations/sqlalchemy.md):** как интроспекция связей обеспечивает автоматическое определение внешних ключей.
* **[Пользовательские представления](custom-views.md):** создавайте страницы за пределами стандартного рабочего процесса создания, редактирования и списка.
* **[События](../advanced/events.md):** реагируйте на инлайн-изменения после сохранения записей.
