---
title: Almacenamiento de archivos
description: Gestione las cargas de archivos e imágenes en starlette-admin mediante
  LocalStorage o backends de almacenamiento compatibles con S3.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Almacenamiento de archivos

`FileField` y `ImageField` almacenan los archivos cargados mediante un backend de almacenamiento que usted configura con el parámetro `storage` del campo.

Cree un backend de almacenamiento una sola vez y reutilícelo en todos los campos que guardan archivos en la misma ubicación.


## Ejemplo mínimo

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

Cuando un usuario carga una portada a través del panel de administración, este:

* guarda el archivo en `uploads/covers/`
* almacena un objeto de metadatos JSON en la columna `cover`

La base de datos nunca contiene el archivo en sí, ni una ruta del sistema de archivos, ni datos binarios.


## Qué se guarda en la base de datos

El panel de administración representa una carga de archivo como un objeto [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) serializado en el campo del modelo.

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename`: nombre de archivo original saneado, usado para su visualización
* `content_type`: tipo MIME detectado en el momento de la carga
* `size`: tamaño del archivo en bytes
* `storage`: nombre del backend registrado, usado para resolver la ubicación del archivo a fin de generar URLs y eliminarlo
* `key`: ruta relativa al almacenamiento o clave del objeto
* `url`: URL pública almacenada en caché

`LocalStorage` guarda un valor vacío en `url`, porque las URLs dependen de la solicitud activa. `S3Storage` guarda una URL pública o prefirmada (presigned), según su configuración.

Sea cual sea el backend, `FileField` regenera la URL en el momento de la renderización con `storage.url()` en lugar de confiar en el valor almacenado.

`ImageField` añade `width` y `height`.

El panel de administración sanea cada nombre de archivo con `secure_filename` antes de almacenarlo: elimina los componentes de ruta y sustituye por `_` los caracteres fuera de `[A-Za-z0-9_.-]`. Consulte [Seguridad](security.md).


## Backends de almacenamiento

### Almacenamiento local

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parámetro | Tipo | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | obligatorio | Directorio raíz para los archivos almacenados. Se crea automáticamente si no existe. |
| `name` | `str | None` | `"local"` | Nombre en el registro que identifica al backend. Debe ser único cuando utilice varias instancias. |

El panel de administración sirve los archivos a través de esta ruta:

```
/_files/{storage}/{path}
```

No necesita ninguna configuración adicional de archivos estáticos.

`LocalStorage.url()` construye las URLs a partir del contexto de la solicitud actual, de modo que el campo `url` almacenado permanece vacío y se recalcula bajo demanda.

!!! note
    Vea [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) para ver un ejemplo de código.

### Almacenamiento en Amazon S3

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

Instale las dependencias opcionales:

```bash
pip install starlette-admin[s3]
```

Esto instala `aiobotocore`.

| Parámetro | Tipo | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `bucket` | `str` | obligatorio | Nombre del bucket de S3. |
| `prefix` | `str` | `"uploads/"` | Prefijo de clave aplicado a cada objeto almacenado. |
| `region` | `str` | `"us-east-1"` | Región de AWS utilizada para firmar y generar URLs. |
| `access_key` y `secret_key` | `str | None` | `None` | Credenciales opcionales. Si no se indican, se usa la cadena de credenciales predeterminada de AWS. |
| `public` | `bool` | `True` | Cuando es `True`, devuelve una URL pública. Cuando es `False`, genera URLs prefirmadas (presigned). |
| `expires` | `int` | `3600` | Tiempo de expiración de las URLs prefirmadas, en segundos. |
| `endpoint_url` | `str | None` | `None` | Endpoint compatible con S3 personalizado, como MinIO, R2 o B2. |
| `name` | `str | None` | `"s3"` | Nombre en el registro que identifica al backend. |

Cuando usted proporciona `endpoint_url`, el panel de administración construye las URLs como:

```
{endpoint_url}/{bucket}/{key}
```

en lugar de usar el formato virtual-hosted de AWS.


!!! important
    Los campos de archivo deben mapearse a una columna de base de datos compatible con JSON. La base de datos solo contiene los metadatos. El backend de almacenamiento contiene el archivo en sí.


## Varios archivos (`multiple=True`)

Establezca `multiple=True` en un `FileField` o un `ImageField` para aceptar varias cargas en un mismo campo.

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

La base de datos guarda una lista JSON de objetos `FileInfo`, y el panel de administración procesa cada archivo de forma independiente durante la validación y el almacenamiento.


!!! warning
    Al guardar el formulario, se reemplaza toda la lista de archivos por los archivos enviados. No hay forma de añadir ni eliminar un único archivo. Para gestionar el ciclo de vida de cada archivo, use un modelo inline con su propio `FileField`.

!!! important
    `ListField(FileField(...))` no está soportado. Use `multiple=True` para colecciones simples y modelos inline para datos estructurados de archivos.

## Validación

La validación se ejecuta en este orden:

1. `accept`
2. `max_size`
3. `validators` personalizados

Un validador personalizado es un objeto invocable que recibe la solicitud, el campo, un `UploadFile` y todos los valores enviados del formulario. Debe devolver `None` o lanzar `ValueError`.

El siguiente ejemplo valida el contenido real del archivo con la librería `filetype`:

```python
import filetype
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import BaseField

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile, form_values: dict
) -> None:
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)

    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )
```

!!! important "Restablezca el puntero del archivo"
    Restablezca siempre el puntero del archivo con `seek(0)` antes y después de inspeccionarlo, para que la capa de almacenamiento pueda leer el archivo completo.

!!! note
    Los validadores se ejecutan por archivo, de modo que con `multiple=True` cada archivo se valida de forma independiente. `ImageField` aplica su propia validación de imágenes antes que cualquier validador personalizado.


!!! tip "Buenas prácticas"
    Utilice `accept` y `max_size` para una validación ligera.

    Utilice validadores personalizados cuando necesite inspeccionar el contenido de los archivos o aplicar reglas específicas de la aplicación.

    No confíe en las extensiones de archivo ni en las cabeceras `Content-Type` para validaciones sensibles a la seguridad. En su lugar, inspeccione el contenido con una librería como `filetype` o `python-magic`.


## Limitaciones en la limpieza de archivos

`starlette-admin` carga los archivos al backend de almacenamiento y escribe los metadatos `FileInfo` en la base de datos, pero no realiza la limpieza de los archivos tras un fallo o una eliminación. De ello se derivan dos comportamientos:

* **Transacciones fallidas:** Si una transacción de la base de datos se revierte después de que la carga haya finalizado, el archivo permanece en el backend de almacenamiento. Las escrituras en el almacenamiento no disponen de ningún mecanismo de reversión.
* **Eliminaciones y actualizaciones:** Al borrar una fila o reemplazar un archivo, se elimina la referencia `FileInfo` de la base de datos, pero el archivo antiguo permanece en `LocalStorage` o `S3Storage`.

Este diseño mantiene simple la capa de almacenamiento y evita que errores a nivel de aplicación desencadenen operaciones destructivas. La contrapartida es que los archivos huérfanos se acumulan. Para evitar que el almacenamiento crezca sin límite, debe reconciliarlos usted mismo. Un patrón habitual es un trabajo periódico en segundo plano que compare las claves de su backend de almacenamiento con las referencias `FileInfo` activas de su base de datos.

### Alternativa transaccional

Si su aplicación necesita que las operaciones de almacenamiento de archivos sean transaccionales junto con las escrituras en la base de datos, use una librería que vincule el almacenamiento de archivos con la unidad de trabajo de SQLAlchemy.

En lugar del parámetro `storage=` del campo, use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Esta librería almacena los archivos como parte del ciclo de flush y rollback del ORM, de modo que una transacción fallida o la eliminación de una fila deshace la escritura correspondiente del archivo. Para ver un ejemplo funcional, consulte [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Próximos pasos

* **[Campos](fields.md):** referencia de `FileField` e `ImageField`.
* **[Exportación e importación](export-import.md):** cómo se incluyen los archivos en los paquetes de exportación.
* **[Seguridad](security.md):** comportamiento automático de saneamiento y validación.
