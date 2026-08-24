---
title: Integración con SQLAlchemy
description: Aprenda a integrar starlette-admin con SQLAlchemy. Cree un panel de administración
  para sus modelos de base de datos relacional en FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

El backend de SQLAlchemy sirve como implementación de referencia para `BaseModelView`. Solo se ha probado con modelos de `DeclarativeBase` de SQLAlchemy 2. Otros backends (como Beanie, MongoEngine, Tortoise ORM o su propia implementación) cumplen este mismo contrato frente a sus respectivos almacenes de datos.

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

Sustituya `aiosqlite` por `asyncpg` (PostgreSQL) o `aiomysql`/`asyncmy` (MySQL) si prefiere no usar SQLite. El controlador de la base de datos solo es relevante para los motores asíncronos. Un motor síncrono usa el controlador DBAPI estándar que requiere SQLAlchemy plano (como `psycopg2` o `pymysql`) y no necesita paquetes adicionales de `starlette-admin`.

## Motores asíncronos frente a síncronos

`Admin` acepta tanto un `Engine` como un `AsyncEngine`. Pase la instancia que tenga configurada:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` inspecciona el motor una sola vez en el momento de la solicitud y abre el tipo de sesión correspondiente: una `AsyncSession` para un `AsyncEngine`, o una `Session` normal para un `Engine` síncrono. Internamente, `ModelView` se bifurca según `isinstance(session, AsyncSession)`. Para las sesiones síncronas, enruta la llamada bloqueante a través de `anyio.to_thread.run_sync` para evitar bloquear el bucle de eventos.

## Pasar un `sessionmaker` en lugar de un motor

El parámetro `session_provider` también acepta un `sessionmaker` o un `async_sessionmaker`. Proporcione un generador de sesiones en lugar de un motor puro cuando deba configurar la sesión directamente.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
El middleware de sesión invoca `session_maker()` para generar una nueva sesión en cada solicitud, en lugar de construirla internamente.

## `sqla.Admin` y `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` acepta los mismos argumentos que `starlette_admin.BaseAdmin`, junto con un argumento posicional obligatorio: `session_provider`. Este proveedor puede ser un `Engine`, un `AsyncEngine`, un `sessionmaker` o un `async_sessionmaker`. Durante la inicialización, el panel de administración configura un middleware de sesión vinculado al proveedor elegido y lo inserta al principio de la pila de middleware. Este mecanismo garantiza que `request.state.session` se rellene automáticamente en cada solicitud antes de que se ejecute el código de su vista.

`sqla.ModelView` requiere un modelo de SQLAlchemy. Durante la inicialización, inspecciona el modelo para detectar automáticamente los campos, gestionar las claves primarias y configurar el registro de filtros directamente a partir de los metadatos.

## Declaración de modelos

Defina sus modelos usando clases declarativas estándar de SQLAlchemy:

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

Si no establece `fields` en la vista, `ModelView` usa todos los atributos declarados en el modelo en el orden en que aparecen. La clave primaria se detecta automáticamente y se excluye de los formularios de creación y edición. Todas las demás columnas y relaciones se convierten automáticamente en el tipo de campo apropiado (como `IntegerField`, `StringField`, `EnumField`, `HasOne` o `HasMany`).

## Valores predeterminados detectados automáticamente

La configuración `default=` del lado de Python de una columna se rellena automáticamente la primera vez que abre el formulario de creación. No es necesario repetir esta definición en el propio campo:

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
    Las columnas de clave primaria nunca reciben un valor predeterminado precompletado, incluso si hay uno definido. Se asume que son generadas por el servidor (mediante `autoincrement` o una secuencia) y se excluyen por completo de los formularios de creación y edición. Los valores predeterminados basados en expresiones SQL (como `server_default=func.now()` o un `DEFAULT` del lado de la base de datos) también se omiten, porque no existe un valor a nivel de Python que mostrar. La base de datos se encarga de rellenar estos valores durante la inserción.

## Campos de relación

Una `relationship()` de SQLAlchemy en el modelo se convierte automáticamente en `HasOne` (de muchos a uno o de uno a uno) o en `HasMany` (de uno a muchos o de muchos a muchos) según el atributo `RelationshipProperty.direction`. No necesita declarar explícitamente el tipo de campo:

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

Al establecer `PostView.fields = ["id", "title", "author"]`, el campo `author` se renderiza como un menú desplegable Select2. Este menú desplegable se rellena mediante AJAX desde el endpoint `/_api/{key}/relation-lookup` de la vista relacionada (donde `{key}` representa `author`, la clave de `AuthorView`). La aplicación nunca carga la tabla completa de autores en la página de una sola vez. Este comportamiento de carga diferida es fundamental para el rendimiento cuando la tabla relacionada contiene miles de filas. De manera similar, al establecer `AuthorView.fields = ["id", "name", "posts"]`, el campo `posts` se renderiza como un control de selección múltiple que utiliza el mismo endpoint de búsqueda.

## Claves primarias compuestas

Los modelos que utilizan varias columnas con `primary_key=True` para claves primarias compuestas son compatibles de forma predeterminada, sin necesidad de configuración adicional. Esto incluye escenarios donde cada columna de la clave primaria sirve también como clave externa, como ocurre en un objeto de asociación de muchos a muchos.

Consulte [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks) para ver un ejemplo completo y ejecutable.

## Registro de filtros

Cada tipo de campo recibe un conjunto predeterminado de filtros de `SqlaFilterRegistry`. Estos se resuelven recorriendo la jerarquía de clases del campo, tal como se detalla en la documentación de [Filters](../user-guide/filters.md) (filtros). Un detalle específico de SQLAlchemy es cómo cada filtro se traduce en un fragmento de consulta. Cada método `apply()` de este módulo devuelve una cláusula booleana independiente de SQLAlchemy (como `column == value` o `column.between(a, b)`).

!!! note
    El filtro `Is null` sobre una relación evalúa `~column.has()` (para relaciones de muchos a uno) o `~column.any()` (para relaciones de uno a muchos y de muchos a muchos) en lugar de `column.is_(None)`. Como el atributo de una relación no es una columna estándar que contenga un valor `NULL`, su nulidad depende completamente de la existencia de filas relacionadas.

!!! note
    El backend de SQLAlchemy no proporciona `ArrayInFilter` ni `ArrayNotInFilter` (los filtros «is one of» para columnas con valores de lista), a diferencia de Beanie y MongoEngine. Debe escribir su propia lógica de `apply()` si necesita filtrado «is one of» sobre una columna JSON o ARRAY respaldada por un `TagsField`. Consulte la documentación de [Custom Filters](../advanced/custom-filters.md) (filtros personalizados) para obtener más detalles.

## Sesiones y transacciones

El middleware de sesión abre exactamente una sesión por solicitud y la almacena de forma segura en `request.state.session`. Este objeto será una `AsyncSession` cuando use un motor asíncrono (o un `async_sessionmaker`), y una `Session` estándar en cualquier otro caso. Todos los componentes involucrados en la solicitud comparten esta única sesión. La consulta de la página de lista, las búsquedas de relaciones dentro de los formularios y cualquier lógica personalizada que se ejecute en un hook, una acción o un endpoint operarán dentro de la misma transacción. Puede recuperarla de manera uniforme independientemente del tipo de motor subyacente:

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

Cuando use un motor síncrono, `request.state.session` evalúa a una `Session` estándar y `session.flush()` se llama sin `await`. El resto del fragmento de código anterior permanece idéntico. No necesita importar una dependencia `get_session()` aparte. La sesión se adjunta a la solicitud antes de que se ejecute su hook o acción, porque el middleware de sesión establece la conexión antes de invocar el manejador de la ruta.

**Una confirmación (commit) por solicitud.** Nunca debe invocar `session.commit()` manualmente. Llamar a `flush()` (o no hacer nada si realiza consultas de solo lectura) es suficiente. El middleware de sesión confirma la sesión exactamente una vez después de que el manejador de la ruta devuelva, siempre que la respuesta indique éxito. Si se produce un error, el middleware revierte toda la transacción automáticamente:

* Si el manejador lanza una excepción, la sesión se revierte y la aplicación vuelve a lanzar la excepción.
* Si el manejador devuelve una respuesta con un `status_code >= 400` (como un fallo de validación del formulario), la sesión se revierte y el servidor devuelve la respuesta sin modificar. Esta reversión es crucial porque, en ese punto, la transacción puede contener un flush fallido. Confirmarla podría persistir involuntariamente un registro escrito parcialmente.
* Si la propia operación de commit lanza una excepción (como una violación de restricción de la base de datos detectada en el momento del flush), la sesión se revierte y la excepción se vuelve a lanzar.

En todos los demás escenarios donde el manejador produce una respuesta 2xx o 3xx, el middleware confirma la sesión y libera la conexión. Este ciclo de vida explica por qué la acción `publish` mostrada anteriormente no requiere instrucciones explícitas de commit ni de cierre. El middleware de sesión abre la sesión antes de que se ejecute su código y, posteriormente, gestiona las operaciones de commit o rollback antes de que la respuesta salga de la vista.

## Validación con Pydantic

Es posible que utilice modelos de SQLAlchemy puros pero que aun así desee validar los datos del formulario contra un esquema de Pydantic antes de guardarlos. En este caso, `starlette_admin.contrib.sqla.ext.pydantic.ModelView` acepta un argumento `pydantic_model` para ejecutar la validación contra ese esquema en lugar de contra los tipos de columna de SQLAlchemy subyacentes:

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

Enviar `full_name="Madonna"` (una sola palabra) hace fallar el método `validate_full_name`. El formulario de creación o edición se vuelve a renderizar con el error adjunto explícitamente al campo `full_name`. La columna de SQLAlchemy subyacente `String(100)` no tiene esa regla. La restricción reside enteramente en el modelo de Pydantic `UserIn`. Consulte [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi) para ver el ejemplo completo, que incluye también una vista secundaria (`PostIn`) adjunta al mismo panel de administración.

## Ejemplo completo funcional


Aquí tiene un ejemplo completo de SQLAlchemy con starlette-admin. Vea [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) para la versión ejecutable.

### 1. Instalar las dependencias

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

El paquete `fastapi[standard]` incluye la CLI de FastAPI, lo que permite iniciar el servidor de desarrollo ejecutando `fastapi dev`.

### 2. Crear la aplicación

Guarde el siguiente código como `main.py`. Este script utiliza una base de datos SQLite local (`blog.db`) con fines de demostración, aunque Starlette-Admin admite motores síncronos y asíncronos para PostgreSQL, MySQL y SQLite.

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

Ahora puede navegar a [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) en su navegador para ver e interactuar con el panel de administración.

---

## Qué leer a continuación

* **[Views](../user-guide/views.md)**: explore las opciones de configuración de `BaseModelView` independientes del backend.
* [Filters](../user-guide/filters.md): detalles sobre el constructor de filtros y el formato de URL impulsado por el registro de filtros.
* [Views](../user-guide/views.md): una lista completa de todas las opciones de configuración de `ModelView` (independiente del backend).
* [SQLModel](sqlmodel.md): un envoltorio ligero alrededor de este backend que añade validación de Pydantic a los formularios.
* [Beanie](beanie.md): una guía para usar la misma API de `ModelView` contra una base de datos MongoDB.
* [Tortoise ORM](tortoise.md): el otro backend relacional integrado en starlette-admin.
