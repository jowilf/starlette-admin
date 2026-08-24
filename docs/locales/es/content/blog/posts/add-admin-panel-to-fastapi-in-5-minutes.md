---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Añadir un panel de administración a FastAPI en 5 minutos con starlette-admin

_2026-07-13_

Usted ya publicó su API. Ahora, alguien de su equipo necesita editar los datos que hay detrás de ella: corregir un error tipográfico en un registro, despublicar una publicación o comprobar qué envió realmente un usuario. Las opciones habituales suelen ser costosas:

| Opción                   | La desventaja                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Frontend CRUD personalizado** | Requiere semanas de tiempo de desarrollo para construirlo y mantenerlo.                                    |
| **Acceso directo a la base de datos**  | Genera un enorme riesgo para la seguridad y la integridad de los datos.                                    |
| **Django Admin / Flask Admin**         | Obliga a reescribir el framework o depende de WSGI síncrono, lo que bloquea su aplicación ASGI asíncrona. |
| **starlette-admin**      | **Se monta en su aplicación al instante y sin código frontend.**                                           |

`starlette-admin` funciona con cualquier aplicación basada en Starlette, que es exactamente lo que es FastAPI.

Esta guía lo lleva desde un archivo vacío hasta una oficina virtual funcional en cinco minutos. Usted creará listas paginadas, funcionalidad de búsqueda, columnas ordenables, formularios de creación y edición validados por sus esquemas Pydantic existentes, confirmaciones de eliminación y exportaciones CSV, todo generado directamente a partir de un modelo SQLAlchemy.

El código completo y ejecutable está disponible en [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Minuto 1: Instalación

Necesita tres paquetes: el framework de administración, el ORM y FastAPI.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic se incluye con FastAPI, lo cual será importante más adelante: el panel de administración puede reutilizar exactamente los mismos esquemas que su API utiliza para la validación.

## Minutos 2 y 3: La aplicación completa

Cree `main.py`. Esta es la aplicación completa:

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

Observe lo que falta. No hay plantillas, ni controladores de rutas para las páginas de administración, ni serializadores, ni configuraciones de campos. `starlette-admin` lee los metadatos de las columnas de SQLAlchemy y deriva toda la interfaz automáticamente: entradas de texto acotadas para las dos columnas `String`, un área de texto para el contenido `Text` y un selector de fecha y hora para `published_at`.

Las tres líneas resaltadas son sus únicos puntos de integración. `Admin` vincula el motor de base de datos, `add_view` registra el modelo en la barra lateral y `mount_to` adjunta todo a su aplicación FastAPI existente bajo la ruta `/admin`. Sus rutas de API permanecen intactas; el panel de administración simplemente funciona como una subaplicación montada.

## Minuto 4: Ejecución

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Abra [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) y haga clic en **Post** en la barra lateral. De forma predeterminada, obtiene:

- Una vista de lista paginada y ordenable de todas las publicaciones.
- Formularios de creación y edición equipados con el widget correcto según el tipo de cada columna.
- Una página de vista detallada para cada registro.
- Capacidades de eliminación por lotes con un diálogo de confirmación.
- Exportaciones CSV y Excel de la lista actual.

Su API sigue atendiendo el tráfico con normalidad. Compruebe [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para verificar que todo está intacto.

## Minuto 5: Hacer que parezca hecho a medida

La vista predeterminada proporciona una interfaz CRUD completa, pero una oficina virtual real merece personalización: su orden de campos, su diseño de formulario y su comportamiento de búsqueda. Crear una subclase de `ModelView` es donde `starlette-admin` libera todo su potencial. Reemplace la llamada a `add_view` por una vista configurada:

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

Cuatro mejoras potentes ocurren en esta única clase:

- **`SlugField(populate_from="title")`**: genera el slug automáticamente mientras el operador escribe el título, sin necesidad de JavaScript personalizado por su parte.
- **`ComputedField`**: muestra un valor que no existe en la base de datos. El recuento de palabras se calcula mediante una función Python sencilla en el momento de la visualización.
- **`form_layout`**: organiza el formulario en filas lógicas: título y slug lado a lado, contenido a ancho completo y la fecha de publicación debajo.
- **`search_auto_submit`**: filtra la lista dinámicamente mientras el operador escribe en todas las columnas definidas en `searchable_fields`.

## Rechazo de datos incorrectos: use el esquema que ya tiene

Los operadores cometen errores, lo que significa que la administración debe aplicar sus reglas del lado del servidor. La ventaja es que usted ya escribió esas reglas. Cada proyecto de FastAPI valida sus cuerpos de solicitud con modelos Pydantic, así que en algún lugar de su código existe un esquema como este:

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

En lugar de escribir la lógica de validación dos veces, entregue a la administración su modelo existente. La extensión `ext.pydantic` proporciona un `ModelView` que procesa cada envío de formulario a través de un modelo Pydantic antes de llegar a la base de datos. Apunte su importación de `ModelView` a la extensión, mantenga `Admin` tal como está y pase el esquema:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

El cuerpo de `PostView` permanece exactamente igual; solo cambia su clase base mediante la nueva importación.

La integración es perfecta. Cada restricción se aplica durante la creación y la edición: los límites de longitud, la expresión regular del slug y el `field_validator` personalizado. Cada error de Pydantic se mapea directamente al campo de formulario correspondiente y se muestra en línea, imitando a la perfección un formulario hecho a mano. Asegúrese de mantener `id` opcional en el esquema para que los formularios de creación, que carecen de un ID inicialmente, puedan seguir validándose.

Esto establece una única fuente de verdad. Cuando su esquema de API recibe una nueva regla, la administración la aplica en la siguiente solicitud sin requerir ningún cambio de código del lado de la administración.

## ¿Tiene un minuto extra? Asigne un autor a las publicaciones

Los datos reales dependen de relaciones, y la administración las maneja con el mismo enfoque de configuración cero. Añada un modelo `User` y vincúlelo a `Post`:

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

Registre el modelo de usuario usando el mismo patrón basado en esquemas. `EmailStr` y `HttpUrl` proporcionan validación de formato automáticamente, y `email-validator` ya está incluido con `fastapi[standard]`:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Como esta vez no hay nada que configurar, el `ModelView` de la extensión se utiliza directamente sin crear una subclase.

Por último, haga obligatorio el autor añadiendo dos líneas a `PostIn`:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` carece de valor predeterminado, lo que significa que una publicación sin autor se rechaza igual que cualquier otro error de validación. El tipo es la propia clase `User` de SQLAlchemy porque la administración resuelve el ID seleccionado en una instancia ORM antes de ejecutar la validación. Esta es exactamente la razón por la que se requiere `arbitrary_types_allowed` (`ConfigDict` se importa de `pydantic`).

A continuación, añada `"user"` a `PostView.fields` y `form_layout` para que el autor aparezca en el formulario de publicación. Este campo no es un menú desplegable estándar. Es un campo de selección con autocompletado del lado del servidor que busca entre sus usuarios mientras el operador escribe, y la página de detalle del usuario enlaza con cada publicación relacionada.

!!! note
`create_all` no altera las tablas existentes, por lo que deberá eliminar `blog.db` antes de reiniciar para incorporar la nueva columna `user_id`.

## Antes de realizar el despliegue

!!! warning
El parámetro `secret_key` firma la cookie de sesión utilizada para la protección CSRF y los mensajes flash. Reemplace el marcador de posición por un valor largo y aleatorio proveniente de su configuración antes del despliegue, y asegúrese de cargarlo desde sus variables de entorno en lugar de codificarlo directamente en el código fuente.

!!! note
`Base.metadata.create_all(engine)` en el lifespan es una comodidad para la guía rápida. En un proyecto de producción, sus tablas se gestionan mediante migraciones (como Alembic). Elimine esa llamada y apunte el `Admin` directamente a su motor existente. `starlette-admin` nunca modifica su esquema; solo lee y escribe filas.

## Esto escala más allá de la demostración

Todo lo anterior utiliza dos modelos, pero estas mismas mecánicas de `ModelView` pueden soportar una oficina virtual de gran tamaño. Puede implementar fácilmente cargas de archivos e imágenes, [autenticación con acceso basado en roles](../../user-guide/auth.md), [filtros personalizados](../../user-guide/filters.md), [acciones de fila y acciones por lotes](../../user-guide/actions.md) e [i18n](../../user-guide/i18n.md) completo. Siempre que el comportamiento integrado se quede corto, cada consulta y paso del ciclo de vida ofrece un hook de anulación. Esta flexibilidad es exactamente cómo se construyen patrones como [eliminaciones lógicas con una vista de papelera](soft-deletes-trash-view.md).

---

## Próximos pasos

- **[Conceptos](../../getting-started/concepts.md):** el vocabulario detrás de lo que acaba de construir, lo que garantiza que el resto de la documentación se lea con fluidez.
- **[Views](../../user-guide/views.md):** un análisis profundo de todas las opciones de `ModelView`, incluidos los hooks de permisos.
- **[Eliminaciones lógicas y una vista de papelera para FastAPI](soft-deletes-trash-view.md):** la primera receta avanzada, construida directamente sobre los hooks de anulación introducidos aquí.
