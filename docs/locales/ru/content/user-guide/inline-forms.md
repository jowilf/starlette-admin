---
title: Встроенные формы
description: Управляйте связанными моделями прямо внутри форм создания и редактирования
  родительской модели с помощью InlineModelView.
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

# Встроенные формы

Встроенные формы позволяют пользователям управлять связанными записями непосредственно со страницы создания или редактирования родительской модели. Они подходят для дочерних моделей, которые имеют смысл только рядом со своей родительской моделью — например, комментарии к статье или задачи в проекте, — и избавляют вас от необходимости создавать отдельное представление администрирования для дочерней модели.

Смотрите [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) — это работающее приложение, охватывающее все три паттерна на этой странице: автоматически определяемый внешний ключ, явный внешний ключ и составной внешний ключ.

## Минимальный пример встроенной формы

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

Настройка выполняется в два шага: определите подкласс `InlineModelView` для дочерней модели, а затем добавьте его в список `inlines` в `ModelView` родительской модели.

На страницах создания и редактирования `ArticleView` теперь отображается набор форм `Comments` под собственными полями статьи. Набор форм изначально содержит одну пустую строку (`extra = 1`) и включает элементы управления добавлением и удалением, которые backend SQLAlchemy настраивает за вас.

Обратите внимание, что `CommentInline` никогда не задаёт `fk_attr`. Backend SQLAlchemy проверяет `Article.comments` и выводит `Comment.article_id` как внешний ключ, поскольку это единственная связь, указывающая на `Comment`. Задавайте `fk_attr` самостоятельно только тогда, когда такой вывод неоднозначен или когда связь не объявлена в ORM-модели. См. раздел [Явные и составные внешние ключи](#explicit-and-composite-foreign-keys).

## Справочник по `InlineModelView`

| Атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `model` | класс ORM-модели | `None` | Связанная модель, которой управляет эта встроенная форма. Обязательный атрибут. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Имя поля внешнего ключа во встроенной модели, которое указывает на родителя. Кортеж объявляет составной внешний ключ. Необязателен для backend'а SQLAlchemy, который автоматически определяет его по связи родителя, если вы его не указали. |
| `extra` | `int` | `0` | Количество пустых строк, отображаемых на формах создания и редактирования, помимо существующих строк. |
| `allow_delete` | `bool` | `True` | Показывать чекбокс или кнопку удаления для каждой существующей строки. |
| `inline_template` | `str` | `"inline.html"` | Шаблон, используемый для отображения набора форм. |
| `collapsible` | `bool` | `True` | Может ли пользователь сворачивать и разворачивать набор форм. |
| `collapsed` | `bool` | `False` | Начальное состояние свёрнутости. Применяется только при `collapsible=True`. |


Конструктор выбрасывает исключение `ValueError`, если `fk_attr` оставлен пустым, а backend не может однозначно разрешить связь.

## Сворачиваемые наборы форм

По умолчанию (`collapsible = True`) каждый `InlineModelView` отображает свой набор форм с заголовком, по которому пользователь может свернуть ненужные дочерние записи. Установите `collapsed = True`, чтобы набор форм изначально был свёрнут, а не развёрнут:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Установите `collapsible = False`, чтобы полностью отключить сворачивание набора форм — он всегда будет отображаться развёрнутым, без переключателя:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Явные и составные внешние ключи {#explicit-and-composite-foreign-keys}

Задайте `fk_attr` самостоятельно, если у родителя есть более одной связи с одной и той же дочерней моделью, если связь не объявлена в ORM-модели или если внешний ключ является составным:

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

Обратите внимание, что `OrderLineInline` не требует `fk_attr`, даже несмотря на то, что первичный ключ `OrderLine` является составным (`order_store_id`, `order_seq`, `line_no`). Backend SQLAlchemy разрешает составной внешний ключ по ограничению `ForeignKeyConstraint` между `Order` и `OrderLine` и заполняет оба столбца в новых строках. Передавайте кортеж `tuple[str, ...]` в `fk_attr` только тогда, когда интроспекция ограничений не находит совпадения.

## Валидация

Каждая отправленная строка проходит валидацию независимо, через те же пути `create` и `edit`, которые использует отдельный `ModelView`. Административная панель сначала сохраняет родителя, а затем последовательно обрабатывает каждую встроенную строку. Опечатка в поле `author` одного комментария не мешает обработке остальных комментариев. Когда строка не проходит валидацию, её ошибки привязываются к этой строке, а форма повторно отображает её на месте с отправленными значениями, чтобы пользователь мог исправить запись и отправить её снова.

!!! important
    На backend'е SQLAlchemy весь запрос является атомарной операцией «всё или ничего». Родитель и все встроенные строки используют одну и ту же сессию в рамках запроса, и эта сессия фиксируется только при успешном выполнении всего запроса целиком. Если хотя бы одна строка не проходит валидацию, ответ возвращает ошибку, а сессия откатывается, поэтому родитель и все встроенные строки отменяются вместе — включая строки, прошедшие валидацию. Рассматривайте построчные ошибки в интерфейсе как список того, что нужно исправить, а не как отчёт о том, что было сохранено.

---

## Что дальше

* **[SQLAlchemy](../integrations/sqlalchemy.md):** Как интроспекция связей обеспечивает автоматическое определение внешних ключей.
* **[Пользовательские представления](custom-views.md):** Создание страниц за пределами стандартного рабочего процесса создания, редактирования и просмотра списка.
* **[События](../advanced/events.md):** Реагирование на изменения во встроенных формах после сохранения записей.
