---
title: Integración con Beanie
description: Integre Beanie ODM con starlette-admin para crear una interfaz de administración
  extensible para sus colecciones de MongoDB en FastAPI.
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Integración con Beanie

Beanie modela los documentos de MongoDB como modelos Pydantic asíncronos. El módulo `starlette_admin.contrib.beanie` proporciona clases especializadas `Admin` y `ModelView` configuradas para interactuar directamente con estos documentos.

**Características principales:**

- Soporte nativo para los operadores de consulta y el filtrado de MongoDB.
- Traducción automática de los errores de validación de Pydantic en errores específicos por campo en la interfaz del formulario.
- Integración integrada para la búsqueda de texto completo de MongoDB.

## Instalación

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## Ejemplo mínimo

Debe inicializar Beanie antes de que cualquier solicitud llegue a la interfaz de administración. Envolver la lógica de conexión dentro del context manager `lifespan` de su aplicación principal es la mejor manera de garantizar que se cumpla este requisito previo.

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

La clase `ModelView` acepta directamente la clase `Document` de Beanie. Deriva automáticamente la lista de campos, los formularios y los filtros a partir de los campos del documento.

## Clases principales

### La clase `beanie.Admin`

La clase `beanie.Admin` hereda de `BaseAdmin` y no requiere ninguna configuración específica de la base de datos durante la inicialización. La configuración de la conexión se realiza completamente dentro del lifespan de la aplicación. Importe siempre `Admin` desde `starlette_admin.contrib.beanie` para garantizar la compatibilidad con futuras mejoras específicas del backend.

### La clase `beanie.ModelView`

La clase `beanie.ModelView` proporciona la capa de integración entre su base de datos y la interfaz de usuario. Gestiona automáticamente varias operaciones:

- **Población de campos:** genera automáticamente los campos a partir de la definición del documento si usted no los especifica explícitamente.
- **Filtrado de campos internos:** excluye el campo interno `revision_id` de Beanie de las listas y los formularios de forma predeterminada.
- **Resolución de relaciones:** ejecuta las lecturas de la base de datos con `fetch_links=True` y `nesting_depth=1`, lo que garantiza que las referencias `Link` se resuelvan en sus objetos relacionados en lugar de devolver referencias sin procesar de la base de datos.
- **Gestión de errores:** traduce los errores de validación de Pydantic en errores específicos por campo en el formulario, señalando directamente al usuario la entrada incorrecta.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## El campo `BeanieObjectIdField`

Beanie utiliza `PydanticObjectId` para las claves primarias. El panel de administración representa automáticamente estas claves, así como cualquier referencia ObjectId sin procesar, mediante un campo dedicado llamado `BeanieObjectIdField`.

Aunque se renderiza y valida exactamente igual que un campo `StringField` estándar, mantiene su propio espacio en el registro de filtros. Esta separación garantiza que los filtros específicos de ObjectId se apliquen únicamente a los campos ObjectId, y no a todos los campos de texto estándar de su aplicación. Estos filtros especializados convierten de forma segura las cadenas en objetos `PydanticObjectId` válidos antes de consultar la base de datos.

## Registro de filtros

Cada tipo de campo recibe un conjunto predeterminado de filtros del `BeanieFilterRegistry`.

- **Coincidencia de cadenas:** el filtro de igualdad utiliza expresiones regulares que no distinguen mayúsculas de minúsculas para mantener la coherencia con otras búsquedas de texto como «Contains» o «Starts with».
- **Operaciones con arrays:** el registro proporciona soporte integrado para el filtrado basado en arrays, lo que permite que las operaciones «Is one of» sobre campos con valores de lista (como `TagsField`) funcionen desde el primer momento.
- **Claves primarias:** el campo `id` se reasigna automáticamente al `_id` nativo de MongoDB al construir los fragmentos de consulta.

## Búsqueda de texto completo

Cuando los usuarios interactúan con el cuadro de búsqueda en una página de lista, el panel de administración comprueba si la colección de MongoDB tiene un índice de texto existente y ajusta su estrategia de consulta en consecuencia:

- **Índice de texto presente:** la consulta utiliza el operador `$text` nativo de MongoDB. Esto proporciona capacidades reales de búsqueda de texto completo, incluida la tokenización, la derivación léxica (stemming) y la clasificación por relevancia.
- **Sin índice de texto:** el sistema recurre a una búsqueda mediante expresiones regulares que no distingue mayúsculas de minúsculas en todos los campos marcados como `searchable`. Aunque esto no requiere configuración alguna, no puede clasificar los resultados por relevancia ni utilizar índices estándar.

El panel de administración detecta los índices de texto existentes, pero no los crea. Debe definir el índice en su documento de Beanie para habilitar la búsqueda de texto nativa. Por ejemplo, puede lograrlo añadiendo `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` a su modelo.

!!! note
Si habilita un índice de texto, puede establecer `full_text_override_order_by = True` en su subclase de `ModelView` para ordenar los resultados de búsqueda según la puntuación de relevancia de MongoDB en lugar del ordenamiento predeterminado por columna.

## Ejemplo completo funcional

Esta sección proporciona una integración completa y ejecutable de Beanie con `starlette-admin`.

### 1. Instale las dependencias

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la CLI de FastAPI, lo que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Cree la aplicación

Guarde el siguiente código en un archivo llamado `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

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

Navegue a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver e interactuar con el panel de control de administración.

> **Ejemplo avanzado:** [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) en el repositorio contiene un ejemplo completamente funcional que incluye vistas en línea, eventos y acciones por lotes personalizadas.

## Qué leer a continuación

- **[Vistas](../user-guide/views.md)**: explore las opciones de configuración de `BaseModelView`, independientes del backend.
- **[Filtros](../user-guide/filters.md):** el constructor de filtros y cómo se integran los filtros específicos de cada ORM.
- **[MongoEngine](mongoengine.md):** otro backend de MongoDB integrado en starlette-admin.
- **[SQLAlchemy](sqlalchemy.md):** el backend relacional integrado en starlette-admin.
