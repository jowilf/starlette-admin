---
title: Integración con SQLModel
description: Cree un panel de administración completo para sus aplicaciones FastAPI
  SQLModel utilizando starlette-admin.
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# Integración con SQLModel

[SQLModel](https://sqlmodel.tiangolo.com/) combina tablas de SQLAlchemy con la validación de Pydantic en una única clase de modelo. Dado que los modelos de SQLModel son modelos de SQLAlchemy internamente, el módulo `starlette_admin.contrib.sqlmodel` actúa como una capa ligera sobre el [backend de SQLAlchemy](sqlalchemy.md) existente.

En lugar de implementar un sistema independiente, esta integración hereda directamente del backend central de SQLAlchemy toda la detección automática de campos, la gestión de claves primarias, el manejo de relaciones, los filtros y el middleware de sesiones. Añade una capa de validación robusta que procesa los datos enviados en los formularios a través de los validadores nativos de Pydantic de su modelo (como `Field(min_length=...)` o métodos personalizados `@field_validator`) antes de que se realice cualquier escritura en la base de datos. Las excepciones `ValidationError` resultantes se traducen automáticamente en errores de formulario por campo en la interfaz.

!!! note
    Todo lo documentado en la [página de SQLAlchemy](sqlalchemy.md) se aplica sin cambios. Esto incluye los motores síncronos y asíncronos, los proveedores `sessionmaker`, el ciclo de vida de sesión de un commit por solicitud, los campos de relación y el registro de filtros.

## Instalación

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## Ejemplo mínimo

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

La clase `ModelView` acepta directamente la clase de tabla de SQLModel y deriva automáticamente la lista de campos, los formularios y los filtros del esquema del modelo.

## Clases principales

### `sqlmodel.Admin`

La clase `sqlmodel.Admin` es la clase `sqla.Admin` reexportada. Utiliza el mismo constructor y acepta un `Engine`, `AsyncEngine`, `sessionmaker` o `async_sessionmaker` como argumento obligatorio `session_provider`. Además, inserta el mismo middleware de sesión que popula `request.state.session` en cada solicitud.

### `sqlmodel.ModelView`

La clase `sqlmodel.ModelView` hereda todo de `sqla.ModelView` y añade una capa de validación. Su método `validate()` llama a `self.model.model_validate(data)` antes de escribir el registro, lo que garantiza que los envíos de formularios se verifiquen mediante los validadores de Pydantic del modelo en lugar de depender estrictamente de las restricciones de columna de SQLAlchemy. Los campos de archivos y los campos de relación se excluyen intencionalmente de esta llamada de validación porque quedan fuera de la superficie de validación de Pydantic del modelo.

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

Las vistas en línea permiten al usuario editar filas relacionadas dentro del formulario padre. La clase hereda la detección de claves externas y el manejo de sesiones de la clase `InlineModelView` de SQLAlchemy, y aplica la misma validación de Pydantic a cada fila en línea.

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Validación de Pydantic

Las restricciones declaradas en el modelo se aplican automáticamente a los formularios de creación y edición:

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

Una entrada como un `full_name` de menos de dos caracteres o una dirección de correo electrónico no válida fallará la validación. Estos fallos se devuelven como errores de formulario por campo antes de que cualquier operación `INSERT` o `UPDATE` llegue a la base de datos.

!!! note
    El tipo `EmailStr` requiere el paquete `email-validator`, que se puede instalar mediante `pip install "pydantic[email]"`.

## Ejemplo completo funcional

Esta sección proporciona una integración completa y ejecutable de SQLModel con `starlette-admin`.

### 1. Instalar las dependencias

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la CLI de FastAPI, que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Crear la aplicación

Guarde el siguiente código en un archivo llamado `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Si envía un `title` de menos de tres caracteres o un `name` de menos de dos caracteres, el formulario se vuelve a renderizar con el error adjunto al campo correspondiente.

### 3. Ejecutar el servidor

Inicie el servidor de desarrollo de FastAPI:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Abra [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver e interactuar con el panel de administración.

> **Ejemplo avanzado:** [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) en el repositorio contiene un ejemplo de CMS completamente funcional que incluye relaciones, vistas en línea, acciones, filtros, eventos y exportaciones.

## Lecturas recomendadas

* **[SQLAlchemy](sqlalchemy.md):** El backend sobre el que se construye esta integración; cubre motores, sesiones, transacciones y el registro de filtros.
* **[Vistas](../user-guide/views.md):** Explore las opciones de configuración de `BaseModelView`, independientes del backend.
* **[Filtros](../user-guide/filters.md):** Conozca el constructor de filtros y cómo se integran los filtros específicos del ORM.
