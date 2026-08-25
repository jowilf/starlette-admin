---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Añada un panel de administración a FastAPI en 5 minutos con starlette-admin

_2026-07-13_

Ya publicó su API. Ahora, alguien de su equipo necesita editar los datos que hay detrás de ella: corregir una errata en un registro, despublicar una entrada o comprobar lo que un usuario envió realmente. Las opciones habituales suelen resultar costosas:

| Opción                   | El inconveniente                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Frontend CRUD propio** | Requiere semanas de tiempo de desarrollo para construirlo y mantenerlo.                                    |
| **Acceso directo a la base de datos**  | Genera un enorme riesgo para la seguridad y la integridad de los datos.                                    |
| **Django Admin / Flask Admin**         | Obliga a reescribir el framework o se apoya en WSGI síncrono, lo que bloquea su aplicación ASGI asíncrona. |
| **starlette-admin**      | **Se monta en su aplicación al instante y sin código frontend.**                                           |

`starlette-admin` funciona con cualquier aplicación basada en Starlette, que es exactamente lo que es FastAPI.

Esta guía le lleva desde un archivo vacío hasta un back office funcional en cinco minutos. Construirá listas paginadas, funcionalidad de búsqueda, columnas ordenables, formularios de creación y edición validados por sus esquemas Pydantic existentes, confirmaciones de borrado y exportaciones CSV, todo generado directamente a partir de un modelo de SQLAlchemy.

El código completo y ejecutable está disponible en [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Minuto 1: Instalación

Necesita tres paquetes: el framework de administración, el ORM y el propio FastAPI.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic se incluye con FastAPI, algo que será importante más adelante: el panel de administración puede reutilizar exactamente los mismos esquemas que su API emplea para la validación.

## Minutos 2 y 3: La aplicación completa

Cree `main.py`. Esta es la aplicación entera:

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

Fíjese en lo que falta. No hay plantillas, ni manejadores de rutas para las páginas de administración, ni serializadores, ni configuraciones de campos. `starlette-admin` lee los metadatos de las columnas de SQLAlchemy y deriva toda la interfaz automáticamente: campos de texto acotados para las dos columnas `String`, un textarea para el contenido `Text` y un selector de fecha y hora para `published_at`.

Las tres líneas resaltadas son sus únicos puntos de integración. `Admin` vincula el motor de base de datos, `add_view` registra el modelo en la barra lateral y `mount_to` adjunta todo a su aplicación FastAPI existente bajo la ruta `/admin`. Sus rutas de API permanecen intactas; el panel de administración funciona simplemente como una subaplicación montada.

## Minuto 4: Ejecútelo

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Abra [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) y haga clic en **Post** en la barra lateral. De fábrica, obtiene:

- Una vista de lista paginada y ordenable de todas las entradas.
- Formularios de creación y edición equipados con el widget de entrada correcto según el tipo de cada columna.
- Una página de vista detallada para cada registro.
- Capacidades de borrado por lotes con un diálogo de confirmación.
- Exportaciones CSV y Excel de la lista actual.

Su API sigue atendiendo tráfico con normalidad. Compruebe [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para verificar que todo está intacto.

## Minuto 5: Hágalo parecer hecho a mano

La vista predeterminada ofrece una interfaz CRUD completa, pero un back office real merece personalización: su orden de campos, su disposición del formulario y su comportamiento de búsqueda. Heredar de `ModelView` es donde `starlette-admin` libera todo su potencial. Sustituya la llamada a `add_view` por una vista configurada:

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

- **`SlugField(populate_from="title")`**: Genera el slug automáticamente mientras el operador escribe el título, sin necesidad de JavaScript personalizado por su parte.
- **`ComputedField`**: Muestra un valor que no existe en la base de datos. El recuento de palabras se calcula mediante una función Python sencilla en el momento de renderizar.
- **`form_layout`**: Organiza el formulario en filas lógicas: título y slug lado a lado, el contenido a ancho completo y la fecha de publicación debajo.
- **`search_auto_submit`**: Filtra la lista dinámicamente mientras el operador escribe en todas las columnas definidas en `searchable_fields`.

## Rechazar datos incorrectos: use el esquema que ya tiene

Los operadores cometen errores, lo que significa que el panel de administración debe imponer sus reglas en el lado del servidor. La ventaja es que esas reglas ya las escribió usted. Todo proyecto de FastAPI valida los cuerpos de sus peticiones con modelos de Pydantic, así que en algún lugar de su código existe un esquema parecido a este:

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

En lugar de escribir la lógica de validación dos veces, entregue al panel de administración su modelo existente. La extensión `ext.pydantic` proporciona un `ModelView` que procesa cada envío de formulario a través de un modelo de Pydantic antes de que llegue a la base de datos. Apunte su importación de `ModelView` hacia la extensión, mantenga `Admin` tal cual y pase el esquema:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

El cuerpo de `PostView` permanece exactamente igual; solo cambia su clase base mediante la nueva importación.

La integración es perfecta. Cada restricción se activa durante la creación y la edición: los límites de longitud, la expresión regular del slug y el `field_validator` personalizado. Cada error de Pydantic se mapea directamente de vuelta a su campo de formulario correspondiente y se muestra en línea, reproduciendo fielmente un formulario hecho a mano. Asegúrese de mantener `id` opcional en el esquema para que los formularios de creación, que carecen de ID inicialmente, puedan seguir validándose.

Esto establece una única fuente de verdad. Cuando su esquema de API recibe una regla nueva, el panel de administración la impone en la siguiente petición sin necesidad de ningún cambio de código en el lado de la administración.

## ¿Un minuto de sobra? Dé a las entradas un autor

Los datos reales dependen de relaciones, y el panel de administración las gestiona con el mismo enfoque de configuración cero. Añada un modelo `User` y vincúlelo a `Post`:

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

Registre el modelo de usuario usando el mismo patrón guiado por esquemas. `EmailStr` y `HttpUrl` proporcionan validación de formato automáticamente, y `email-validator` ya viene incluido con `fastapi[standard]`:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Como esta vez no hay nada que configurar, se utiliza directamente el `ModelView` de la extensión sin heredar de él.

Por último, haga obligatorio el autor añadiendo dos líneas a `PostIn`:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` no tiene valor predeterminado, lo que significa que una entrada sin autor se rechaza igual que cualquier otro error de validación. El tipo es la propia clase `User` de SQLAlchemy porque el panel de administración resuelve el ID seleccionado a una instancia del ORM antes de que se ejecute la validación. Es exactamente por esto que `arbitrary_types_allowed` es necesario (`ConfigDict` se importa de `pydantic`).

A continuación, añada `"user"` a `PostView.fields` y a `form_layout` para que el autor aparezca en el formulario de entradas. Este campo no es un desplegable estándar. Es un campo de selección con autocompletado del lado del servidor que busca entre sus usuarios mientras el operador escribe, y la página de detalle del usuario enlaza de vuelta con cada entrada relacionada.

!!! note
`create_all` no modifica las tablas existentes, por lo que deberá eliminar `blog.db` antes de reiniciar para incorporar la nueva columna `user_id`.

## Antes de desplegar

!!! warning
El parámetro `secret_key` firma la cookie de sesión utilizada para la protección CSRF y los mensajes flash. Sustituya el marcador de posición por un valor largo y aleatorio procedente de su configuración antes del despliegue, y asegúrese de cargarlo desde sus variables de entorno en lugar de codificarlo directamente en el código fuente.

!!! note
`Base.metadata.create_all(engine)` en el lifespan es una comodidad para la guía rápida. En un proyecto de producción, sus tablas se gestionan mediante migraciones (como Alembic). Elimine esa llamada y apunte el `Admin` directamente a su motor existente. `starlette-admin` nunca modifica su esquema; solo lee y escribe filas.

## Esto escala más allá de la demostración

Todo lo anterior utiliza dos modelos, pero estas mismas mecánicas de `ModelView` pueden sostener un back office enorme. Puede implementar fácilmente subidas de archivos e imágenes, [autenticación con acceso basado en roles](../../user-guide/auth.md), [filtros personalizados](../../user-guide/filters.md), [acciones por fila y por lotes](../../user-guide/actions.md) e [i18n](../../user-guide/i18n.md) completo. Siempre que el comportamiento integrado se quede corto, cada consulta y cada paso del ciclo de vida ofrece un hook de sobrescritura. Esta flexibilidad es precisamente cómo se construyen patrones como [borrados suaves con una vista de papelera](soft-deletes-trash-view.md).

---

## Próximos pasos

- **[Conceptos](../../getting-started/concepts.md):** El vocabulario detrás de lo que acaba de construir, para que el resto de la documentación se lea con fluidez.
- **[Vistas](../../user-guide/views.md):** Un análisis profundo de todas las opciones de `ModelView`, incluidos los hooks de permisos.
- **[Borrados suaves y una vista de papelera para FastAPI](soft-deletes-trash-view.md):** La primera receta avanzada, construida directamente sobre los hooks de sobrescritura presentados aquí.
