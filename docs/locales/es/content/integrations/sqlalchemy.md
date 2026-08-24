---
title: Integración con SQLAlchemy
description: Aprenda a integrar starlette-admin con SQLAlchemy. Cree un panel de administración
  para los modelos de su base de datos relacional en FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

El backend de SQLAlchemy sirve como implementación de referencia para `BaseModelView`. Solo se ha probado contra modelos `DeclarativeBase` de SQLAlchemy 2. Otros backends (como Beanie, MongoEngine, Tortoise ORM o su propia implementación personalizada) cumplen este mismo contrato frente a sus respectivos almacenes de datos.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


class ProductView(ModelView):
    fields = ["id", "name", "price"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

## Instalación

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

Sustituya `aiosqlite` por `asyncpg` (PostgreSQL) o `aiomysql`/`asyncmy` (MySQL) si prefiere no usar SQLite. El driver de la base de datos solo es relevante para motores asíncronos. Un motor síncrono utiliza el driver DBAPI estándar que requiere el SQLAlchemy convencional (como `psycopg2` o `pymysql`) y no necesita paquetes adicionales de `starlette-admin`.

## Motores asíncronos frente a síncronos

`Admin` acepta tanto un `Engine` como un `AsyncEngine`. Pase la instancia que tenga configurada:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` inspecciona el motor una sola vez en tiempo de solicitud y abre el tipo de sesión correspondiente: una `AsyncSession` para un `AsyncEngine` o una `Session` convencional para un `Engine` síncrono. Internamente, `ModelView` se ramifica según `isinstance(session, AsyncSession)`. Para sesiones síncronas, enruta la llamada bloqueante a través de `anyio.to_thread.run_sync` para evitar bloquear el event loop.

## Pasar un `sessionmaker` en lugar de un motor

El parámetro `session_provider` también acepta un `sessionmaker` o un `async_sessionmaker`. Proporcione un session maker en lugar de un motor directamente cuando necesite configurar la sesión de forma explícita.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
El middleware de sesión invoca `session_maker()` para generar una nueva sesión en cada solicitud en lugar de construirla internamente.

## `sqla.Admin` y `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` acepta los mismos argumentos que `starlette_admin.BaseAdmin`, junto con un argumento posicional obligatorio: `session_provider`. Este proveedor puede ser un `Engine`, un `AsyncEngine`, un `sessionmaker` o un `async_sessionmaker`. Durante la inicialización, el panel de administración configura un middleware de sesión vinculado al proveedor elegido y lo inserta al principio del stack de middleware. Este mecanismo garantiza que `request.state.session` se rellene automáticamente en cada solicitud antes de que se ejecute el código de su vista.

`sqla.ModelView` requiere un modelo de SQLAlchemy. En la inicialización, inspecciona el modelo para detectar automáticamente los campos, gestionar las claves primarias y configurar el registro de filtros directamente a partir de los metadatos.

## Declaración de modelos

Defina sus modelos utilizando clases declarativas estándar de SQLAlchemy:

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

Si no establece `fields` en la vista, `ModelView` utiliza todos los atributos declarados en el modelo en el orden en que aparecen. La clave primaria se detecta automáticamente y se excluye de los formularios de creación y edición. Todas las demás columnas y relaciones se convierten en el tipo de campo apropiado (como `IntegerField`, `StringField`, `EnumField`, `HasOne` o `HasMany`) de forma automática.

## Valores predeterminados autodetectados

La configuración `default=` del lado Python de una columna se rellena automáticamente la primera vez que abre el formulario de creación. No es necesario repetir esta definición en el propio campo:

```python
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    views: Mapped[int] = mapped_column(default=0)  # form shows 0
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )  # form shows now()
```

Un valor predeterminado escalar (`default=0`) se copia exactamente como está definido. Un valor predeterminado invocable (`default=datetime.utcnow` o `default=uuid.uuid4`) se ejecuta una vez al renderizar el formulario, lo que permite ver un valor real en lugar del formato `repr` de la función.

!!! important
    Las columnas de clave primaria nunca reciben un valor predeterminado prellenado, aunque esté definido. Se asume que son generadas por el servidor (mediante `autoincrement` o una secuencia) y se excluyen por completo de los formularios de creación y edición. Los valores predeterminados basados en expresiones SQL (como `server_default=func.now()` o un `DEFAULT` del lado de la base de datos) también se omiten porque no existe un valor a nivel de Python que mostrar. La base de datos se encarga de poblar estos valores durante la inserción.

## Campos de relación

Una `relationship()` de SQLAlchemy en el modelo se convierte automáticamente en `HasOne` (muchos a uno o uno a uno) o `HasMany` (uno a muchos o muchos a muchos) según el atributo `RelationshipProperty.direction`. No es necesario declarar explícitamente el tipo de campo:

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")
```

Al establecer `PostView.fields = ["id", "title", "author"]`, el campo `author` se renderiza como un desplegable Select2. Este desplegable se rellena mediante AJAX desde el endpoint `/_api/{key}/relation-lookup` de la vista relacionada (donde `{key}` representa `author`, la clave de `AuthorView`). La aplicación nunca carga la tabla completa de autores en la página de una sola vez. Este comportamiento de carga diferida es fundamental para el rendimiento cuando la tabla relacionada contiene miles de filas. De manera análoga, al establecer `AuthorView.fields = ["id", "name", "posts"]`, el campo `posts` se renderiza como un control de selección múltiple que utiliza el mismo endpoint de búsqueda.

## Claves primarias compuestas

Los modelos que utilizan varias columnas con `primary_key=True` para formar claves primarias compuestas están soportados de forma nativa, sin necesidad de ninguna configuración adicional. Esto incluye escenarios donde cada columna de la clave primaria es también una clave foránea, como ocurre en un objeto de asociación de muchos a muchos.

Consulte [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks) para ver un ejemplo completamente ejecutable.

## Registro de filtros {#filter-registry}

Cada tipo de campo recibe un conjunto predeterminado de filtros de `SqlaFilterRegistry`. Estos se resuelven recorriendo la jerarquía de clases del campo, tal como se detalla en la documentación de [Filters](../user-guide/filters.md). Un detalle crucial específico de SQLAlchemy es cómo se traduce cada filtro en un fragmento de consulta. Cada método `apply()` de este módulo devuelve una cláusula booleana de SQLAlchemy independiente (como `column == value` o `column.between(a, b)`).

!!! note
    El filtro `Is null` sobre una relación evalúa `~column.has()` (para relaciones muchos a uno) o `~column.any()` (para relaciones uno a muchos y muchos a muchos) en lugar de `column.is_(None)`. Como un atributo de relación no es una columna estándar que contenga un valor `NULL`, su nulidad depende por completo de la existencia de filas relacionadas.

!!! note
    El backend de SQLAlchemy no proporciona `ArrayInFilter` ni `ArrayNotInFilter` (los filtros «is one of» para columnas con valores de lista), a diferencia de Beanie y MongoEngine. Deberá escribir su propia lógica de `apply()` si necesita filtrado «is one of» sobre una columna JSON o ARRAY respaldada por un `TagsField`. Consulte la documentación de [Custom Filters](../advanced/custom-filters.md) para obtener más detalles.

## Sesiones y transacciones

El middleware de sesión abre exactamente una sesión por solicitud y la guarda de forma segura en `request.state.session`. Este objeto será una `AsyncSession` cuando utilice un motor asíncrono (o un `async_sessionmaker`) y una `Session` estándar en cualquier otro caso. Todos los componentes que intervienen en la solicitud comparten esta única sesión. La consulta de listado, las búsquedas de relaciones dentro de los formularios y cualquier lógica personalizada que se ejecute en un hook, action o endpoint operarán todos dentro de la misma transacción. La obtiene de forma uniforme, independientemente del tipo de motor subyacente:

```python
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    @action(name="publish", text="Publish selected")
    async def publish(self, request: Request, pks: list[Any]) -> str:
        session: AsyncSession = request.state.session
        for post in await self.find_by_pks(request, pks):
            post.status = "PUBLISHED"
            session.add(post)
        await session.flush()
        return f"{len(pks)} post(s) published."
```

Cuando utilice un motor síncrono, `request.state.session` se evalúa como una `Session` estándar y `session.flush()` se llama sin `await`. El resto del fragmento de código anterior permanece idéntico. No necesita importar una dependencia `get_session()` aparte. La sesión se adjunta a la solicitud antes de que se ejecute su hook o action, porque el middleware de sesión establece la conexión antes de invocar el route handler.

**Un commit por solicitud.** Nunca debe invocar `session.commit()` manualmente. Basta con llamar a `flush()` (o no hacer nada si realiza consultas de solo lectura). El middleware de sesión hace commit de la sesión exactamente una vez después de que el route handler devuelva, siempre que la respuesta indique éxito. Si se produce un error, el middleware revierte toda la transacción automáticamente:

* Si el handler lanza una excepción, la sesión se revierte y la aplicación vuelve a lanzar la excepción.
* Si el handler devuelve una respuesta con un `status_code >= 400` (por ejemplo, un fallo de validación de formulario), la sesión se revierte y el servidor devuelve la respuesta sin modificar. Esta reversión es fundamental porque la transacción podría contener un flush fallido en ese punto. Hacer commit podría persistir inadvertidamente un registro escrito parcialmente.
* Si la propia operación de commit lanza una excepción (por ejemplo, una violación de restricción de la base de datos detectada en el momento del flush), la sesión se revierte y se vuelve a lanzar la excepción.

En todos los demás escenarios donde el handler produce una respuesta 2xx o 3xx, el middleware hace commit de la sesión y libera la conexión. Este ciclo de vida explica por qué la acción `publish` mostrada anteriormente no requiere instrucciones explícitas de commit o close. El middleware de sesión abre la sesión antes de que se ejecute su código y, posteriormente, gestiona las operaciones de commit o rollback antes de que la respuesta salga de la vista.

## Validación con Pydantic {#pydantic-validation}

Es posible que utilice modelos de SQLAlchemy puros pero que aun así quiera validar los datos del formulario contra un esquema de Pydantic antes de guardarlos. En ese caso, `starlette_admin.contrib.sqla.ext.pydantic.ModelView` acepta un argumento `pydantic_model` para ejecutar la validación contra dicho esquema en lugar de los tipos de columna de SQLAlchemy subyacentes:

```python
from sqlalchemy import ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///users.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip().split()) < 2:
            raise ValueError("Must include both first and last name (e.g. John Doe)")
        return v


admin = Admin(engine, title="Users Admin", secret_key="change-me")
admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

Enviar `full_name="Madonna"` (una sola palabra) hace fallar el método `validate_full_name`. El formulario de creación o edición se vuelve a renderizar entonces con el error adjunto explícitamente al campo `full_name`. La columna de SQLAlchemy subyacente `String(100)` no tiene regla alguna de este tipo. La restricción reside íntegramente en el modelo de Pydantic `UserIn`. Consulte [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi) para ver el ejemplo completo, que también incluye una vista secundaria (`PostIn`) adjunta al mismo panel de administración.

## Ejemplo completo funcional


Aquí tiene un ejemplo completo de SQLAlchemy con starlette-admin. Vea [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) para la versión ejecutable.

### 1. Instale las dependencias

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la FastAPI CLI, lo que le permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Cree la aplicación

Guarde el siguiente código como `main.py`. Este script utiliza una base de datos SQLite local (`blog.db`) con fines de demostración, aunque Starlette-Admin soporta tanto motores síncronos como asíncronos para PostgreSQL, MySQL y SQLite.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import SlugField
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")


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
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
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

Ya puede dirigirse a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver e interactuar con el panel de administración.

---

## Qué leer a continuación

* **[Views](../user-guide/views.md)**: Explore las opciones de configuración de `BaseModelView` independientes del backend.
* [Filters](../user-guide/filters.md): Detalles sobre el constructor de filtros y el formato de URL impulsado por el registro de filtros.
* [Views](../user-guide/views.md): Una lista exhaustiva de todas las opciones de configuración de `ModelView` (independiente del backend).
* [SQLModel](sqlmodel.md): Una capa ligera sobre este backend que añade validación de Pydantic a los formularios.
* [Beanie](beanie.md): Una guía para utilizar la misma API de `ModelView` contra una base de datos MongoDB.
* [Tortoise ORM](tortoise.md): El otro backend relacional integrado en starlette-admin.
