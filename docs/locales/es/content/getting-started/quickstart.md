---
title: Inicio rápido
description: Cree una interfaz de administración CRUD completamente funcional para
  FastAPI y Starlette en minutos con nuestra guía de inicio rápido completa.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# Inicio rápido

Cree una interfaz de administración CRUD completamente funcional para un blog en minutos, con formularios, listas, búsqueda, importación y exportación generados automáticamente directamente a partir de sus modelos de datos.

## Instalación

Instale los paquetes necesarios utilizando su gestor de paquetes preferido:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    El paquete `fastapi[standard]` incluye la CLI de FastAPI, que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

## El ejemplo completo

Cree un archivo llamado `main.py` y añada el siguiente código:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## Ejecutar la aplicación

Inicie el servidor de desarrollo:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Abra un navegador y vaya a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

En la barra lateral, seleccione **Posts** y, a continuación, seleccione **Create**. Ahora puede acceder a las páginas de lista paginada, detalle, creación, edición y eliminación. El sistema genera automáticamente todas estas interfaces a partir de la definición de su modelo.

## Cómo funciona

Las siguientes secciones explican los componentes principales de la aplicación.

### El modelo

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

Este código utiliza SQLAlchemy 2.0 estándar. El paquete starlette-admin lee los metadatos de columna mapeados a estos atributos para determinar el campo HTML exacto que debe generar. Por ejemplo, crea un campo de texto para `str`, una casilla de verificación para `bool` y un selector de fecha y hora para `datetime`.

### La vista

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` actúa como el objeto central de este recurso. El atributo `fields` controla qué columnas aparecen en la lista y en el formulario, mientras que `searchable_fields` habilita la barra de búsqueda. Toda la configuración sobre cómo se ve y se comporta `Post` en el panel de administración reside en esta única clase.

!!! note
    El ejemplo importa `ModelView` desde `starlette_admin.contrib.sqla` porque depende de SQLAlchemy. Si utiliza otro backend, como Beanie, MongoEngine o Tortoise ORM, debe importar `ModelView` desde el paquete contrib correspondiente. La API de configuración se mantiene consistente en todos los backends admitidos.

### El admin

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

La clase `Admin` conecta el motor de base de datos con la interfaz de usuario.

* `add_view` registra su vista en la barra lateral. El parámetro opcional `icon` acepta cualquier clase válida de [Font Awesome](https://fontawesome.com/icons).
* `mount_to` adjunta la aplicación de administración a su aplicación FastAPI o Starlette en la ruta `/admin`.

!!! warning
    El parámetro `secret_key` firma las cookies para los datos de sesión, incluidos los mensajes flash y la protección CSRF. En entornos de producción, debe reemplazar el valor del ejemplo por una cadena larga, aleatoria y generada de forma segura. Nunca utilice un valor de marcador de posición en un despliegue real.

## Añadir un segundo modelo

Puede registrar un número ilimitado de modelos. Por ejemplo, para añadir un modelo `Tag` y su vista correspondiente, defina las clases y llame a `add_view` nuevamente:

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

Actualice la ventana del navegador para ver tanto **Posts** como **Tags** en la barra lateral. Cada recurso cuenta ahora con sus propias páginas de lista, creación, edición y eliminación completamente funcionales.

---

## Próximos pasos

* **[Conceptos](concepts.md):** Aprenda la terminología de los conceptos presentados aquí para navegar mejor por la Guía de usuario.
* **[Admin](../user-guide/admin.md):** Descubra todas las opciones de `Admin(...)`, incluyendo marca, temas, autenticación, seguridad e internacionalización.
* **[Views](../user-guide/views.md):** Explore todas las opciones de configuración de `ModelView` disponibles para personalizar la presentación de sus datos.
