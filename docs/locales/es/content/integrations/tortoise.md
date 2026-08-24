---
title: Integración con Tortoise ORM
description: Cree fácilmente una interfaz de administración para sus modelos de Tortoise
  ORM en FastAPI usando starlette-admin.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Integración con Tortoise ORM

Tortoise ORM es un mapeador objeto-relacional nativo de asyncio inspirado en Django. El módulo `starlette_admin.contrib.tortoise` proporciona clases especializadas de `Admin`, `ModelView` e `InlineModelView` que vienen preconfiguradas para integrarse directamente con sus modelos de Tortoise.

**Características principales:**

* **Conversión automática de campos:** Mapea los campos de los modelos de Tortoise directamente a componentes de la interfaz. Esto incluye soporte completo para enums, JSON, fechas y marcas de tiempo automáticas.
* **Mapeo de relaciones:** Convierte las claves externas y las relaciones uno a uno en campos `HasOne`, y las relaciones muchos a muchos en campos `HasMany`. Las relaciones inversas se muestran automáticamente como de solo lectura.
* **Filtrado avanzado:** Utiliza expresiones `Q` de Tortoise para el creador de filtros y permite la búsqueda de texto completo sin distinguir mayúsculas de minúsculas en los campos de texto.
* **Traducción de errores:** Mapea los errores de validación de Tortoise directamente a errores específicos de cada campo en el formulario de la interfaz.

## Instalación

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Ejemplo mínimo

Tortoise se conecta a la base de datos dentro del context manager `lifespan` de su aplicación. Dado que las vistas de administración normalmente se instancian en el momento de la importación (antes de que se ejecute `Tortoise.init()`), debe resolver las relaciones de forma anticipada.

Llame a `Tortoise.init_models()` inmediatamente después de definir sus modelos para garantizar que las relaciones estén disponibles cuando se construyan las vistas de administración.

```python
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from tortoise import Tortoise, fields
from tortoise.models import Model
from starlette_admin.contrib.tortoise import Admin, ModelView


class Genre(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)


# Resuelve las relaciones en el momento de la importación, antes de construir las vistas de administración.
Tortoise.init_models(["app"], "models")


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(
        db_url="sqlite://library.sqlite3", modules={"models": ["app"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

La clase `ModelView` acepta directamente la clase `Model` de Tortoise y deriva automáticamente la lista de campos, los formularios y los filtros a partir del esquema del modelo.

## Clases principales

### `tortoise.Admin`

La clase `tortoise.Admin` hereda de `BaseAdmin` y no requiere ninguna configuración específica de la base de datos durante la inicialización. La configuración de la conexión se realiza por completo dentro del `lifespan` de la aplicación. Importe siempre `Admin` desde `starlette_admin.contrib.tortoise` para garantizar la compatibilidad con futuras mejoras específicas del backend.

### `tortoise.ModelView`

La clase `tortoise.ModelView` proporciona la capa de integración entre su base de datos y la interfaz de usuario. Gestiona automáticamente las siguientes operaciones:

* **Población de campos:** Genera los campos a partir de la definición del modelo si usted no los especifica explícitamente. Las columnas de clave sin procesar que respaldan las relaciones to-one (como `author_id` para una relación llamada `author`) y las relaciones inversas se omiten de forma predeterminada.
* **Resolución de relaciones:** Precarga todas las relaciones que muestra la vista. Esto garantiza que las páginas de lista y de detalle nunca activen cargas diferidas (lazy loads).
* **Marcas de tiempo automáticas:** Las columnas que usan `DatetimeField(auto_now=...)` o `DatetimeField(auto_now_add=...)` se muestran como de solo lectura y nunca se marcan como obligatorias.
* **Gestión de errores:** Traduce los errores de validación de Tortoise (`"<campo>: <detalle>"`) a errores específicos de cada campo en el formulario, que señalan directamente al usuario la entrada incorrecta.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Las vistas en línea permiten editar filas relacionadas dentro del formulario principal. La clave externa se detecta automáticamente cuando el modelo secundario tiene exactamente una relación que apunta al modelo principal. Si existen varias relaciones, debe establecer `fk_attr` explícitamente usando el nombre de la relación o su columna de clave sin procesar.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Gestión de relaciones

La integración mapea las relaciones de la base de datos a campos de administración según el tipo de campo. Debe registrar un `ModelView` para cada modelo relacionado para que los campos de relación puedan resolver correctamente sus vistas externas.

| Tipo de relación | Configuración de Tortoise | Comportamiento en la administración |
| --- | --- | --- |
| **Directa (to-one)** | `ForeignKeyField`, `OneToOneField` | Se convierte en `HasOne`. |
| **Directa (to-many)** | `ManyToManyField` | Se convierte en `HasMany`. |
| **Inversa** | propiedades `related_name` | Se muestra como de solo lectura. Debe añadirse explícitamente a `fields` para mostrarse. |

**Filtrado y ordenación en las relaciones:**
Las relaciones to-one ofrecen los filtros «Is null» e «Is not null», que actúan sobre la columna de clave sin procesar. Para exponer una relación en el creador de filtros, añada el nombre de la relación a `searchable_fields`. Para habilitar la ordenación por la columna de clave sin procesar, añada el nombre de la relación a `sortable_fields`.

## Búsqueda y filtrado

### Registro de filtros

Cada tipo de campo recibe un conjunto predeterminado de filtros del `TortoiseFilterRegistry`, implementado mediante expresiones `Q` de Tortoise:

* **Coincidencia de texto:** Los filtros de contiene, comienza/termina con y de igualdad usan búsquedas sin distinguir mayúsculas de minúsculas (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enums:** Los valores sin procesar de los filtros se convierten de nuevo en miembros del enum antes de realizar la consulta, tanto para las columnas `CharEnumField` como para las `IntEnumField`.
* **Columnas de hora:** Las columnas `TimeField` ofrecen únicamente comprobaciones de valores nulos. Esta limitación existe porque los parámetros de tipo hora no pueden vincularse de forma portable en todos los backends de bases de datos.

### Búsqueda de texto completo

El cuadro de búsqueda de la página de lista construye una coincidencia `contains` sin distinguir mayúsculas de minúsculas (expresiones `Q` combinadas con `OR`) sobre todos los campos de texto marcados como buscables. Puede personalizar este comportamiento sobrescribiendo el método `get_search_query()` de su vista.

## Ejemplo completo y funcional

Esta sección proporciona una integración completa y ejecutable de Tortoise ORM con `starlette-admin`.

### 1. Instale las dependencias

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la CLI de FastAPI, que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Cree la aplicación

Guarde el siguiente código en un archivo llamado `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from starlette_admin import SlugField
from starlette_admin.contrib.tortoise import Admin, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

DB_URL = "sqlite://blog.sqlite3"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __admin_repr__(self, request) -> str:
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts")

    def __admin_repr__(self, request) -> str:
        return self.title


# Resuelve las relaciones en el momento de la importación, antes de construir las vistas de administración.
Tortoise.init_models(["main"], "models")


class AuthorView(ModelView):
    fields = ["id", "name"]


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
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["main"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Dado que `created_at` usa `auto_now_add`, la interfaz de administración lo muestra automáticamente como de solo lectura. No es necesario configurar `exclude_fields_from_create` ni `exclude_fields_from_edit`.

### 3. Ejecute el servidor

Inicie el servidor de desarrollo de FastAPI:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Navegue a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver el panel de control de administración e interactuar con él.

> **Ejemplo avanzado:** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) en el repositorio contiene un ejemplo completo que incluye relaciones, vistas en línea, enums y campos JSON respaldados por SQLite.

## Lecturas recomendadas

* **[Vistas](../user-guide/views.md):** Explore las opciones de configuración de `BaseModelView` independientes del backend.
* **[Filtros](../user-guide/filters.md):** Aprenda sobre el creador de filtros y cómo se integran los filtros específicos de cada ORM.
* **[SQLAlchemy](sqlalchemy.md):** Documentación del otro backend relacional integrado en starlette-admin.
