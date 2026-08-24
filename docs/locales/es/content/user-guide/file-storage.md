---
title: Almacenamiento de archivos
description: Gestione la subida de archivos e imágenes en starlette-admin mediante
  LocalStorage o un backend de almacenamiento compatible con S3.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Almacenamiento de archivos

`FileField` y `ImageField` almacenan los archivos subidos a través de un backend de almacenamiento que usted configura con el parámetro `storage` del campo.

Cree el backend de almacenamiento una sola vez y reutilícelo en todos los campos que guarden archivos en la misma ubicación.


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

Cuando un usuario sube una portada a través del admin, este:

* guarda el archivo en `uploads/covers/`
* almacena un objeto JSON de metadatos en la columna `cover`

La base de datos nunca contiene el archivo en sí, una ruta del sistema de archivos ni datos binarios.


## Qué se guarda en la base de datos

El admin representa un archivo subido como un objeto [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) serializado en el campo del modelo.

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

* `filename`: nombre de archivo original saneado, usado para mostrarlo
* `content_type`: tipo MIME detectado en el momento de la subida
* `size`: tamaño del archivo en bytes
* `storage`: nombre del backend registrado, usado para resolver la ubicación del archivo al generar URLs y al eliminarlo
* `key`: ruta relativa al almacenamiento o clave del objeto
* `url`: URL pública almacenada en caché

`LocalStorage` guarda un valor vacío en `url`, porque las URLs dependen de la petición activa. `S3Storage` guarda una URL pública o presignada, según su configuración.

Sea cual sea el backend, `FileField` regenera la URL en el momento de renderizar mediante `storage.url()` en lugar de confiar en el valor almacenado.

`ImageField` añade `width` y `height`.

El admin sanea cada nombre de archivo con `secure_filename` antes de almacenarlo: elimina los componentes de ruta y reemplaza los caracteres fuera de `[A-Za-z0-9_.-]` por `_`. Consulte [Seguridad](security.md).


## Backends de almacenamiento

### Almacenamiento local

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parámetro | Tipo | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | obligatorio | Directorio raíz donde se guardan los archivos. Se crea automáticamente si no existe. |
| `name` | `str | None` | `"local"` | Nombre de registro que identifica al backend. Debe ser único si utiliza varias instancias. |

El admin sirve los archivos a través de esta ruta:

```
/_files/{storage}/{path}
```

No necesita ninguna configuración adicional de archivos estáticos.

`LocalStorage.url()` construye las URLs a partir del contexto de la petición actual, por lo que el campo `url` almacenado permanece vacío y se recalcula bajo demanda.

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

| Parámetro | Tipo | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `bucket` | `str` | obligatorio | Nombre del bucket de S3. |
| `prefix` | `str` | `"uploads/"` | Prefijo de clave aplicado a cada objeto almacenado. |
| `region` | `str` | `"us-east-1"` | Región de AWS utilizada para firmar y generar URLs. |
| `access_key` y `secret_key` | `str | None` | `None` | Credenciales opcionales. Si no se indican, se usa la cadena de credenciales predeterminada de AWS. |
| `public` | `bool` | `True` | Cuando es `True`, devuelve una URL pública. Cuando es `False`, genera URLs presignadas. |
| `expires` | `int` | `3600` | Tiempo de expiración de las URLs presignadas, en segundos. |
| `endpoint_url` | `str | None` | `None` | Endpoint personalizado compatible con S3, como MinIO, R2 o B2. |
| `name` | `str | None` | `"s3"` | Nombre de registro que identifica al backend. |

Cuando usted proporciona `endpoint_url`, el admin construye las URLs como:

```
{endpoint_url}/{bucket}/{key}
```

en lugar de usar el formato virtual-hosted de AWS.


!!! important
    Los campos de archivo deben mapearse a una columna de base de datos compatible con JSON. La base de datos solo contiene los metadatos. El backend de almacenamiento contiene el archivo en sí.


## Múltiples archivos (`multiple=True`)

Establezca `multiple=True` en un `FileField` o `ImageField` para aceptar varias subidas en un mismo campo.

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

La base de datos guarda una lista JSON de objetos `FileInfo`, y el admin procesa cada archivo de forma independiente durante la validación y el almacenamiento.


!!! warning
    Al guardar el formulario, toda la lista de archivos se reemplaza por los archivos enviados. No hay forma de añadir ni eliminar un único archivo. Para gestionar el ciclo de vida de cada archivo, utilice un modelo inline con su propio `FileField`.

!!! important
    `ListField(FileField(...))` no está soportado. Use `multiple=True` para colecciones simples y modelos inline para datos de archivo estructurados.

## Validación

La validación se ejecuta en este orden:

1. `accept`
2. `max_size`
3. `validators` personalizados

Un validador personalizado es un callable que recibe la petición, el campo, un `UploadFile` y los valores completos del formulario enviado. Debe devolver `None` o lanzar `ValueError`.

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

!!! important "Restablecer el puntero del archivo"
    Restablezca siempre el puntero del archivo con `seek(0)` antes y después de inspeccionarlo, para que la capa de almacenamiento pueda leer el archivo completo.

!!! note
    Los validadores se ejecutan por archivo, de modo que con `multiple=True` cada archivo se valida de forma independiente. `ImageField` aplica su propia validación de imágenes antes de cualquier validador personalizado.


!!! tip "Buenas prácticas"
    Use `accept` y `max_size` para una validación ligera.

    Use validadores personalizados cuando necesite inspeccionar el contenido del archivo o aplicar reglas específicas de la aplicación.

    No dependa de las extensiones de archivo ni de las cabeceras `Content-Type` para validaciones sensibles a la seguridad. Inspeccione el contenido en su lugar, con una librería como `filetype` o `python-magic`.


## Limitaciones en la limpieza de archivos

`starlette-admin` sube los archivos al backend de almacenamiento y escribe los metadatos `FileInfo` en la base de datos, pero no limpia los archivos tras un fallo o una eliminación. De ello se derivan dos comportamientos:

* **Transacciones fallidas:** Si una transacción de base de datos se revierte después de que la subida haya finalizado, el archivo permanece en el backend de almacenamiento. Las escrituras en el almacenamiento no disponen de mecanismo de rollback.
* **Eliminaciones y actualizaciones:** Eliminar una fila o reemplazar un archivo elimina la referencia `FileInfo` de la base de datos, pero el archivo antiguo permanece en `LocalStorage` o `S3Storage`.

Este diseño mantiene simple la capa de almacenamiento y evita que errores a nivel de aplicación desencadenen operaciones destructivas. La contrapartida es que se acumulan archivos huérfanos. Para evitar que el almacenamiento crezca sin límite, deberá reconciliarlos usted mismo. Un patrón habitual es un trabajo periódico en segundo plano que compare las claves de su backend de almacenamiento con las referencias `FileInfo` activas de su base de datos.

### Alternativa transaccional

Si su aplicación necesita que las operaciones de almacenamiento de archivos sean transaccionales junto con las escrituras en la base de datos, utilice una librería que vincule el almacenamiento de archivos con la unidad de trabajo de SQLAlchemy.

En lugar del parámetro `storage=` del campo, use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Esta librería almacena los archivos como parte del ciclo de flush y rollback del ORM, de modo que una transacción fallida o la eliminación de una fila deshacen la escritura correspondiente del archivo. Para ver un ejemplo funcional, consulte [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Próximos pasos

* **[Campos](fields.md):** Referencia de `FileField` e `ImageField`.
* **[Exportación e importación](export-import.md):** Cómo se incluyen los archivos en los paquetes de exportación.
* **[Seguridad](security.md):** Comportamiento de saneamiento automático y validación.
