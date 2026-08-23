---
title: Formularios en línea
description: Gestione modelos relacionados directamente dentro de los formularios
  de creación y edición de un modelo padre mediante InlineModelView.
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# Formularios en línea

Los formularios en línea permiten a los usuarios gestionar registros relacionados directamente desde la página de creación o edición de un modelo padre. Son adecuados para modelos hijos que solo tienen sentido junto a su modelo padre, como los comentarios de un artículo o las tareas de un proyecto, y le evitan tener que construir una vista de administración separada para el modelo hijo.

Consulte [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) para ver una aplicación ejecutable que cubre los tres patrones de esta página: clave externa detectada automáticamente, clave externa explícita y clave externa compuesta.

## Un inline mínimo

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

Configurar esto requiere dos pasos: definir una subclase de `InlineModelView` para el modelo hijo y luego añadirla a la lista `inlines` del `ModelView` del padre.

Las páginas de creación y edición de `ArticleView` ahora muestran un formset de `Comments` debajo de los campos propios del artículo. El formset comienza con una fila vacía (`extra = 1`) e incluye los controles de añadir y eliminar que el backend de SQLAlchemy configura por usted.

Tenga en cuenta que `CommentInline` nunca define `fk_attr`. El backend de SQLAlchemy inspecciona `Article.comments` e infiere `Comment.article_id` como la clave externa, porque es la única relación que apunta a `Comment`. Defina `fk_attr` usted mismo solo cuando esa inferencia sea ambigua o cuando la relación no esté declarada en el modelo ORM. Consulte [Claves externas explícitas y compuestas](#claves-externas-explicitas-y-compuestas).

## Referencia de `InlineModelView`

| Atributo | Tipo | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `model` | Clase de modelo ORM | `None` | El modelo relacionado que este inline gestiona. Obligatorio. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Nombre del campo de clave externa en el modelo inline que apunta al padre. Una tupla declara una clave externa compuesta. Opcional en el backend de SQLAlchemy, que la detecta automáticamente a partir de la relación del padre cuando se omite. |
| `extra` | `int` | `0` | Número de filas vacías que se muestran en los formularios de creación y edición, además de las filas existentes. |
| `allow_delete` | `bool` | `True` | Mostrar una casilla de verificación o un botón de eliminación en cada fila existente. |
| `inline_template` | `str` | `"inline.html"` | Plantilla utilizada para mostrar el formset. |
| `collapsible` | `bool` | `True` | Indica si los usuarios pueden expandir y contraer el formset. |
| `collapsed` | `bool` | `False` | Estado inicial contraído. Se aplica solo cuando `collapsible=True`. |


El constructor lanza una excepción `ValueError` cuando deja `fk_attr` vacío y el backend no puede resolver la relación de forma inequívoca.

## Formsets plegables

De forma predeterminada (`collapsible = True`), cada `InlineModelView` muestra su formset con un encabezado que los usuarios pueden seleccionar para contraer los registros hijos que no necesiten. Defina `collapsed = True` para que el formset comience cerrado en lugar de abierto:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Defina `collapsible = False` para excluir por completo el formset del comportamiento plegable, de modo que siempre se muestre expandido sin ningún control:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Claves externas explícitas y compuestas

Defina `fk_attr` usted mismo cuando el padre tenga más de una relación con el mismo modelo hijo, cuando la relación no esté declarada en el modelo ORM o cuando la clave externa sea compuesta:

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

Tenga en cuenta que `OrderLineInline` no necesita `fk_attr`, aunque la clave primaria de `OrderLine` sea compuesta (`order_store_id`, `order_seq`, `line_no`). El backend de SQLAlchemy resuelve la clave externa compuesta a partir de la restricción `ForeignKeyConstraint` entre `Order` y `OrderLine`, y rellena ambas columnas en las filas nuevas. Pase una `tuple[str, ...]` a `fk_attr` solo cuando la introspección de restricciones no encuentre ninguna coincidencia.

## Validación

Cada fila enviada se valida por sí misma, a través de las mismas rutas `create` y `edit` que utiliza un `ModelView` independiente. La administración guarda primero el padre y luego procesa cada fila inline por turnos. Un error tipográfico en el campo `author` de un comentario no impide que se procesen los demás comentarios. Cuando una fila no supera la validación, sus errores se asocian a esa fila, y el formulario vuelve a mostrarla en su lugar con los valores enviados para que los usuarios puedan corregirla y volver a enviarla.

!!! important
    En el backend de SQLAlchemy, toda la solicitud es todo-o-nada. El padre y cada fila inline comparten la misma sesión con ámbito de solicitud, y esa sesión solo confirma cuando la solicitud completa tiene éxito. Si alguna fila no supera la validación, la respuesta devuelve un error y la sesión se revierte, de modo que el padre y todas las filas inline se revierten juntas, incluidas las filas que superaron la validación. Considere los errores por fila en la interfaz como una lista de lo que hay que corregir, no como un registro de lo que se guardó.

---

## Próximos pasos

* **[SQLAlchemy](../integrations/sqlalchemy.md):** Cómo la introspección de relaciones permite la detección automática de claves externas.
* **[Vistas personalizadas](custom-views.md):** Cree páginas más allá del flujo de trabajo estándar de creación, edición y lista.
* **[Eventos](../advanced/events.md):** Reaccione a los cambios inline después de guardar los registros.
