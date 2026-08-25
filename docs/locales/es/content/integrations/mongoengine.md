---
title: Integración con MongoEngine
description: Aprenda a conectar modelos de MongoEngine con starlette-admin para gestionar
  sus datos de MongoDB mediante un panel de administración.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# Integración con MongoEngine

MongoEngine modela los documentos de MongoDB como clases de Python síncronas mediante una API de campos al estilo de Django. El módulo `starlette_admin.contrib.mongoengine` proporciona clases especializadas `Admin` y `ModelView` que construyen vistas administrativas directamente a partir de sus definiciones de `mongoengine.Document`.

**Características principales:**

* Conversión automática de tipos de campo, relaciones y documentos embebidos.
* Soporte listo para usar para subidas de `FileField` e `ImageField` respaldadas por GridFS.

## Instalación

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## Ejemplo mínimo

Debe establecer la conexión a MongoDB antes de que cualquier solicitud llegue a la interfaz de administración. Envolver la lógica de conexión dentro del context manager `lifespan` de su aplicación principal es la mejor manera de garantizar que se cumpla este requisito previo.

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

La clase `ModelView` acepta directamente la clase `mongoengine.Document`. Deriva automáticamente la lista de campos, los formularios y los filtros a partir de los campos del documento.

## Clases principales: Admin y ModelView

### La clase `mongoengine.Admin`

La clase `mongoengine.Admin` extiende la clase base `Admin` añadiendo una ruta especializada: `/api/file/{db}/{col}/{pk}`. Esta ruta transmite un archivo de GridFS directamente al navegador.

Dado que cada subida mediante `FileField` o `ImageField` en un modelo de MongoEngine se almacena en GridFS, esta ruta es necesaria para servir dichos archivos. Utilice siempre `mongoengine.Admin` en lugar de la clase base `Admin`.

### La clase `mongoengine.ModelView`

A diferencia de la clase base, el constructor de `mongoengine.ModelView` recibe un argumento posicional `document` en lugar de una clase de modelo declarativo:

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

Si deja sin definir el atributo `fields` en su subclase de `ModelView`, este incluirá por defecto todos los campos del documento en el orden en que fueron declarados.

Los atributos como `key`, `menu_label` y `display_name` siguen un orden estricto de valores alternativos:

1. El argumento del constructor.
2. Un atributo a nivel de clase definido en la subclase.
3. Un valor derivado del nombre de la clase del documento (`key` se convierte en el nombre slugificado, `menu_label` en el nombre pluralizado y embellecido, y `display_name` en el nombre singular embellecido).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Registro de filtros {#filter-registry}

Cada tipo de campo incluye un conjunto fijo de filtros proporcionado por el `MongoEngineFilterRegistry`. Puede sobrescribir estos valores predeterminados por campo utilizando el argumento `filters=[...]`.

| Tipo de campo | Filtros disponibles |
| --- | --- |
| `StringField` | contiene, no contiene, empieza con, termina con, igual a, distinto de, es nulo, no es nulo |
| `TextAreaField` | contiene, no contiene, empieza con, termina con, es nulo, no es nulo |
| `EnumField` | igual a, distinto de, in, not in, es nulo, no es nulo |
| `NumberField` | igual a, distinto de, mayor que, menor que, entre, es nulo, no es nulo |
| `FloatField` | igual a, distinto de, mayor que, menor que, entre, es nulo, no es nulo |
| `DateField` | igual a, entre, en el pasado, en el futuro, es nulo, no es nulo |
| `DateTimeField` | igual a, entre, en el pasado, en el futuro, es nulo, no es nulo |
| `BooleanField` | es verdadero, es falso, es nulo, no es nulo |
| `TagsField` | in, not in, es nulo, no es nulo |
| `RelationField` | es nulo, no es nulo |
| `ObjectIdField` | igual a, distinto de, in, not in, es nulo, no es nulo |

!!! note
    El `ObjectIdField` representa el `id` del documento.

Internamente, el método `apply()` de cada filtro devuelve un fragmento `Q` de MongoEngine para su condición específica. Los árboles anidados de `FilterGroup` combinan después esos fragmentos mediante operadores bit a bit (`&` u `|`) antes de ejecutar la consulta. Para más detalles, consulte la documentación de [Filtros](../user-guide/filters.md).

## Documentos embebidos

El campo `EmbeddedDocumentField` de MongoEngine se convierte en un `CollectionField`. Este proceso convierte recursivamente cada campo del documento embebido en su propio subcampo:

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

En este ejemplo:

* El campo `address` se muestra como un subformulario anidado durante la creación y la edición, y como un bloque anidado en la página de detalle.
* El campo `comments` (un `EmbeddedDocumentListField`) se convierte en un `ListField` de `CollectionField`. Se representa como un grupo repetible de subformularios, mostrando uno por cada entrada de la lista.

## Ejemplo completo funcional

Esta sección proporciona una integración completa y ejecutable de MongoEngine con `starlette-admin`.

### 1. Instale las dependencias

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la CLI de FastAPI, lo que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Cree la aplicación

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


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
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


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

Acceda a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver e interactuar con el panel de administración.

> **Ejemplo avanzado:** [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) en el repositorio contiene una aplicación completamente equipada. Incluye vistas inline, eventos, acciones personalizadas de fila y por lotes, así como subidas de imágenes y archivos mediante GridFS.

---

## Qué leer a continuación

* **[Vistas](../user-guide/views.md)**: Explore las opciones de configuración de `BaseModelView` independientes del backend.
* **[Campos](../user-guide/fields.md):** Guía detallada de cada tipo de campo y sus atributos, incluido el `CollectionField`.
* **[Filtros](../user-guide/filters.md):** Explore la interfaz del constructor de filtros y aprenda a escribir un filtro personalizado.
* **[Beanie](beanie.md):** Descubra la alternativa asíncrona basada en Pydantic para MongoDB.
