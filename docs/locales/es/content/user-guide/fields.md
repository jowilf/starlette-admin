---
title: Campos
description: Referencia completa de todos los campos integrados en starlette-admin
  para mapear las columnas de su base de datos a componentes de interfaz.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Campos

Los campos son los componentes básicos de sus vistas. Internamente, son dataclasses de Python simples: cada atributo que pase al constructor de un campo se convierte en un atributo del dataclass, y cada tipo de campo hereda de `BaseField`, por lo que puede inspeccionarlo, crear una subclase o instanciarlo directamente.

## Atributos comunes

Cada tipo de campo hereda este conjunto de atributos de configuración de `BaseField`.

| Atributo | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `name` | `str` | **Obligatorio** | El nombre del atributo en su modelo. |
| `label` | `str | None` | `name` con formato de título | El encabezado de la columna y la etiqueta del formulario. |
| `help_text` | `str | None` | `None` | Texto de ayuda que se muestra debajo del campo del formulario. |
| `required` | `bool` | `False` | Exige un valor en los formularios, tanto en el cliente como en el servidor. |
| `validators` | `list[Validator]` | `[]` | Validadores del lado servidor que se ejecutan contra el valor enviado. Consulte [Validación](#validacion). |
| `disabled` | `bool` | `False` | Atenúa y bloquea el campo en los formularios. |
| `read_only` | `bool` | `False` | Muestra el campo pero impide editarlo. |
| `default` | `Any | Callable` | `None` | El valor de relleno previo en el formulario de creación. |
| `getter` | `Callable | None` | `None` | Reemplaza la búsqueda del atributo del modelo al leer el valor. Consulte [Calcular, formatear y analizar valores](#calcular-formatear-y-analizar-valores). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Formato de visualización por acción, que reemplaza la serialización para esa acción. Consulte [Calcular, formatear y analizar valores](#calcular-formatear-y-analizar-valores). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Análisis de entrada por acción, que reemplaza el análisis predeterminado del campo. Consulte [Calcular, formatear y analizar valores](#calcular-formatear-y-analizar-valores). |
| `searchable` | `bool` | `True` | Se incluye cuando coincide el parámetro de búsqueda `q`. |
| `orderable` | `bool` | `True` | Añade un enlace de ordenación en el encabezado de la página de lista. |
| `copy_to_clipboard` | `bool` | `False` | Añade un botón de copiado junto al valor en la página de detalle. |
| `filters` | `list | None` | `None` | Sustitución explícita de los filtros de la página de lista. |
| `extra` | `dict[str, Any]` | `{}` | Un diccionario para sus propios metadatos. |

### Controles de visibilidad

Use estos indicadores booleanos, todos con valor `False` de forma predeterminada, para controlar dónde aparece un campo:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Definir valores predeterminados

El atributo `default` acepta un valor estático, una función sin argumentos o una función que recibe la solicitud:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Calcular, formatear y analizar valores

Cada campo acepta tres hooks que son funciones: `getter`, `formatter` y `parser`, que interceptan y transforman los datos a medida que se mueven entre su modelo y la interfaz. Cada uno acepta una función síncrona o asíncrona.

#### `getter`: leer valores personalizados

El hook `getter` reemplaza la búsqueda predeterminada mediante `getattr()` cuando el campo lee una instancia del modelo. El campo llama a `getter(request, obj)` y muestra el valor devuelto.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Dado que los valores de `getter` rara vez se corresponden con una columna física de la base de datos, funcionan mejor junto con una visualización de solo lectura. [`ComputedField`](#computedfield) es un atajo integrado para esa combinación.

#### `formatter`: transformar la salida mostrada

El hook `formatter` define cómo se representa un valor almacenado en páginas específicas. Asocia un `RequestAction`, como `LIST`, `DETAIL` o `EXPORT`, a una función `(request, value) -> value`.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Comportamiento del formato que debe tener en cuenta:**

* **Los valores nulos llegan al formatter:** A diferencia de la serialización predeterminada, los formatters reciben valores `None`, por lo que puede suministrar texto alternativo, como `"unset"` en el ejemplo anterior.
* **Se omite la serialización:** Un formatter coincidente reemplaza los métodos `serialize_value` y `serialize_none_value` del campo. El valor devuelto se usa tal cual, por lo que el formatter es totalmente responsable de la salida final.
* **Requisito de JSON:** Los valores devueltos para las acciones `LIST` y `RELATION_LOOKUP` deben seguir siendo serializables a JSON.

#### `parser`: procesar datos entrantes

El hook `parser` anula el análisis predeterminado del campo para los datos enviados o importados. Asocia un `RequestAction` a una función `(request, raw) -> value`.

* **Formularios (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` es la entrada del formulario enviada, o una lista cuando `multiple=True`.
* **Importaciones (`IMPORT`):** `raw` es el valor sin procesar de la celda en el archivo.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

Tras el análisis, el valor devuelto pasa por la cadena estándar de validación, primero `required` y después `validators`, exactamente igual que si el propio campo hubiera analizado los datos.

!!! tip "¿Hooks o una subclase?"
    Para una personalización puntual en un solo campo, rara vez necesita una subclase. Pase estos hooks como argumentos del constructor para gestionar la lectura, el formato de visualización y el análisis de la entrada. [Cree una subclase del campo](../advanced/custom-fields.md) cuando reutilice la lógica en varias vistas, o cuando necesite modificar las plantillas de renderizado HTML.

### Validación

La validación del lado servidor se ejecuta sobre cada campo cuando se envía un formulario de creación o edición, de modo que los datos incorrectos nunca lleguen a la base de datos.

El ciclo de vida es fijo:

1. **Valores vacíos:** Cuando el valor enviado está vacío, como `None`, `""` o una colección vacía, solo se comprueba el indicador `required`. Los validadores se omiten.
2. **Valores con contenido:** Cuando hay datos presentes, cada función de la lista `validators` se ejecuta en orden contra el valor analizado.

#### Firma del validador

Un validador recibe cuatro argumentos: `(request, field, value, form_values)`.

* **`request`:** El objeto de solicitud actual de Starlette.
* **`field`:** La instancia del campo que se está validando.
* **`value`:** El valor analizado enviado para este campo.
* **`form_values`:** Un diccionario con todos los datos analizados del formulario, indexados por nombre de campo, lo que permite inspeccionar otros campos.

Para rechazar un valor, lance una `ValueError`. El panel de administración captura el primer error de un campo, omite los validadores restantes de ese campo y recopila todos los errores para mostrarlos junto a sus campos correspondientes.

#### Validadores integrados

El módulo [`starlette_admin.validators`](../api/validators.md) proporciona reglas estándar:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Validación personalizada y asíncrona

Escriba validadores personalizados como funciones síncronas o asíncronas. Reciben el objeto `request`, por lo que pueden consultar la base de datos para comprobar restricciones complejas.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Con el argumento `form_values`, un validador a nivel de campo también puede aplicar una regla que dependa de otro campo enviado.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Reglas de validación según el contexto

* **Campos de relación:** `HasOne` y `HasMany` reciben las claves primarias de los registros relacionados durante la validación.
* **Campos de archivos:** La validación se ejecuta una vez por cada `UploadFile` en la carga útil. Consulte [Campos de archivos y medios](#campos-de-archivos-y-medios).
* **Validación entre campos:** Use `form_values` para una dependencia sencilla. Para una regla que abarque todo el formulario, anule el método `validate()` en su vista. La validación a nivel de vista se ejecuta solo después de que cada campo supere su propia cadena de validación.

### Almacenar metadatos personalizados

`extra` es un `dict` simple que `starlette-admin` nunca lee ni escribe. Úselo para adjuntar sus propios datos a una instancia de campo, ya sea para una plantilla personalizada, un hook en su subclase de [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) o cualquier otro punto de integración, sin necesidad de crear una subclase del campo:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Campos de texto

### StringField y TextAreaField

`StringField` muestra un campo de texto de una sola línea para contenido corto. `TextAreaField` lo amplía con un elemento `<textarea>` para texto largo de varias líneas.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Atributo adicional | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `maxlength` and `minlength` | `int | None` | `None` | Restricciones de longitud HTML. |
| `placeholder` | `str | None` | `None` | Texto de marcador del campo. |
| `rows` *(solo TextArea)* | `int` | `6` | Número de líneas de texto visibles. |

### TinyMCEEditorField

Amplía `TextAreaField` con un editor WYSIWYG de la biblioteca TinyMCE. Requiere el paquete extra `tinymce`.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Los atributos `height`, `menubar`, `statusbar` y `toolbar` controlan la interfaz del editor. Pase cualquier otra configuración nativa de TinyMCE mediante `extra_options`.

### Campos de texto con formato

Estas variantes de `StringField` muestran un tipo de entrada HTML correspondiente y dan formato al valor cuando se muestra el registro.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` e `IPAddressField` añaden cada uno un validador correspondiente (`email`, `url`, `uuid` e `ip_address` de [`starlette_admin.validators`](../api/validators.md)) cuando deja `validators` vacío. Pase sus propios `validators` para sobrescribirlo.

    `UUIDField` establece `copy_to_clipboard=True` de forma predeterminada. `IPAddressField` acepta `ipv4`, `True` de forma predeterminada, y `ipv6`, `False` de forma predeterminada, que controlan las familias de direcciones que acepta su validador predeterminado.

### PasswordField

Muestra un elemento `<input type="password">` en los formularios para ocultar lo que el usuario escribe.

!!! danger
    `PasswordField` enmascara la entrada únicamente en los formularios de creación y edición. No sobrescribe las plantillas de visualización, por lo que los valores se muestran como **texto plano** en las páginas de lista y de detalle, y registra los valores enviados sin procesar a nivel `DEBUG`.

    Establezca `exclude_from_list = True` y `exclude_from_detail = True` en los campos de contraseñas, y desactive el registro `DEBUG` en producción.

## Campos numéricos

Los campos numéricos manejan enteros, números de coma flotante y decimales.

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| Atributo adicional | Se aplica a | Descripción |
| --- | --- | --- |
| `min` y `max` | Integer, Decimal | Valores mínimo y máximo permitidos. |
| `step` | Integer, Decimal | La restricción de incremento. |

!!! note
    `FloatField` funciona de manera diferente: se muestra como un campo de texto simple, convierte el valor enviado a un `float` y no admite `min`, `max` ni `step`.

## Campos de fecha y hora

Estos campos utilizan los selectores nativos de fecha y hora del navegador, respaldados por los tipos correspondientes de la biblioteca estándar (`datetime.date`, `datetime.datetime` y `datetime.time`).

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| Atributo adicional | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Formato de visualización de Babel: `"short"`, `"medium"`, `"long"`, `"full"` o un patrón personalizado. |
| `search_format` | `str | None` | Específico del ORM | Formato utilizado para construir las consultas de búsqueda en la base de datos. |

!!! note
    Cuando el soporte de zonas horarias está activado, `DateTimeField` realiza por usted las conversiones entre la zona horaria de visualización y la zona horaria de la base de datos.

### ArrowField

Una variante de `DateTimeField` respaldada por un objeto `Arrow`. Fuera de los formularios de edición, muestra un tiempo relativo humanizado, como «hace 3 horas». Requiere el paquete `arrow`.

## Campos de selección y colección

### EnumField

El campo de selección de propósito general. Muestra un menú desplegable `<select>`, o un multiselector `select2` cuando `multiple=True`. Puede respaldarlo con una subclase de `Enum` de Python, una lista de tuplas o opciones cargadas en tiempo de solicitud.

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| Atributo adicional | Tipo | Descripción |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Construye las opciones a partir de una clase `Enum` de Python. |
| `choices` | `Sequence | None` | Pares `(valor, etiqueta)` estáticos, o valores sueltos. |
| `choices_loader` | `Callable | None` | Calcula las opciones por solicitud. |
| `multiple` | `bool` | Activa la selección múltiple y almacena los valores como una lista. |

!!! important
    Proporcione exactamente uno de los siguientes: `enum`, `choices` o `choices_loader`.

`TimeZoneField`, `CountryField` y `CurrencyField` son subclases de `EnumField` respaldadas por datos de configuración regional de Babel, lo que requiere el extra `i18n`. Localizan sus etiquetas según la solicitud actual.

### TagsField

Un campo de etiquetado de texto libre basado en `select2`. Almacena un `list[str]` y no necesita opciones predefinidas.

### ListField

Encapsula otro campo para almacenar una lista ordenada de valores de ese tipo. Se muestra como filas repetibles con controles para añadir y eliminar. El nombre del campo encapsulado se convierte en el nombre del `ListField`.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Agrupa varios subcampos en un único objeto anidado. Úselo para datos incrustados o similares a estructuras, como un documento incrustado de MongoDB.

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## Campos especializados

### JSONField

Muestra un árbol JSON y un editor de código, y almacena un `dict` de Python. Pase un diccionario JSON Schema estándar a `validation_schema` para obtener retroalimentación en el lado cliente.

### SlugField

Una variante de `StringField` que se rellena automáticamente en el cliente a partir de la entrada de otro campo. Una edición manual detiene el autocompletado.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` es obligatorio y debe apuntar a otro campo del mismo formulario. El slug generado se envía y se almacena como cualquier otra cadena.

### ComputedField

Un campo virtual de solo lectura derivado de la instancia del modelo en el momento de la visualización, sin ninguna columna de base de datos detrás. Se basa en el hook [`getter`](#calcular-formatear-y-analizar-valores) que tiene todo campo, y añade los valores predeterminados que necesita una columna virtual: excluido de los formularios de creación, de solo lectura, no buscable y no ordenable.

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

Para lógica compleja o reutilizable, cree una subclase de `ComputedField` y anule `parse_obj()` en lugar de pasar un `getter` en línea:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` y `parse_obj` hacen el mismo trabajo: use `getter` para expresiones cortas y cree una subclase de `ComputedField` cuando la lógica ocupe varias líneas o se reutilice en varias vistas. En los formularios de edición, el campo sigue apareciendo como texto plano, de modo que el usuario ve el valor calculado actual.

Toda subclase de `ComputedField` mantiene el renderizado de `StringField`. Para calcular un valor que deba mostrarse como otro tipo, como una fecha, una insignia o una imagen, establezca `getter=` directamente en ese tipo de campo, junto con los indicadores `read_only` y `exclude_from_*` correspondientes.

## Campos de archivos y medios

`FileField` muestra un campo de carga de archivos, y `ImageField` añade una vista previa de imagen y una comprobación de validez. Adjunte un backend `storage=` para guardar las cargas automáticamente y almacenar un diccionario JSON `FileInfo` en la base de datos. Para la configuración completa, consulte la [guía de almacenamiento de archivos](file-storage.md).

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| Atributo adicional | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Lista separada por comas de extensiones de archivo o tipos MIME aceptados, pasada al atributo HTML `accept`. |
| `multiple` | `bool` | `False` | Acepta varios archivos en un mismo campo. |
| `storage` | `BaseStorage | None` | `None` | Backend de almacenamiento que guarda las cargas. Sin él, el campo entrega las cargas sin procesar a su backend. |
| `upload_folder` | `str` | `""` | La carpeta relativa al almacenamiento donde se guardan los archivos. |
| `max_size` | `int | None` | `None` | Tamaño máximo aceptado de carga, en bytes. |
| `validators` | `list[Validator]` | `[]` | Validadores personalizados, cada uno invocado como `(request, field, upload)` una vez por archivo cargado, después de las comprobaciones de `accept` y `max_size`. Lance `ValueError` para rechazar. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | Solo `ImageField`. Cuando se establece, Pillow genera una miniatura acotada al guardar, y la página de lista la usa en lugar de la imagen completa. |

!!! note
    `ImageField` antepone una comprobación de validez de imagen basada en Pillow a la lista `validators`. Cuando Pillow está instalado y el almacenamiento está configurado, también registra `width` y `height` en el `FileInfo` resultante.

Con `thumbnail_size` establecido, el panel de administración genera una miniatura junto a la imagen completa, preservando la relación de aspecto y sin ampliarla, y la almacena bajo su propia clave. Por ejemplo, `covers/cat.jpg` obtiene un hermano `covers/cat.thumb.jpg`. La página de lista usa la miniatura automáticamente. Las filas sin ella, ya sea por datos preexistentes o porque `thumbnail_size` no está establecido, recurren a la imagen completa. Un fallo en la generación de la miniatura se registra en el log y jamás hace fallar la carga.

La página de detalle abre cada imagen de `ImageField` en un lightbox, de modo que los usuarios pueden navegar por imágenes a resolución completa. Las imágenes que pertenecen al mismo campo (`multiple=True`) se agrupan en una sola galería.

Consulte [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) para ver una aplicación completa y ejecutable, que incluye un validador personalizado de tipos MIME.

### Sin almacenamiento

Sin ningún `storage=` adjunto, el campo entrega las cargas sin procesar directamente a su backend, en lugar de guardarlas:

* **En los formularios de creación y edición**, el valor analizado es una tupla, `(UploadFile | list[UploadFile] | None, bool)`. El primer elemento es el `UploadFile` sin procesar de Starlette, una lista cuando `multiple=True`, o `None` cuando el usuario no seleccionó nada. El segundo elemento es `True` cuando el usuario marca la casilla de eliminación en el formulario de edición, lo que significa que quiere eliminar el archivo existente sin reemplazarlo. La lógica `create()` y `edit()` de su backend debe almacenar la carga y respetar el indicador de eliminación.
* **En las páginas de lista y de detalle**, el campo espera que el valor exponga tres claves, como un `dict`, o tres atributos, como un objeto: `url`, obligatoria, el destino del enlace; `filename`, la etiqueta de visualización; y `content_type`, que selecciona el icono del tipo de archivo.

Este contrato es la forma en que las siguientes integraciones ORM conectan su propio manejo de archivos al mismo campo.

### Columnas de archivos nativas del ORM

**MongoEngine** admite `mongoengine.FileField` y `mongoengine.ImageField` desde el inicio, usando **GridFS** como almacenamiento. El panel de administración carga, sirve y elimina archivos en GridFS por usted. No necesita ninguna configuración de `storage=`: basta con listar el campo por su nombre.

**SQLAlchemy** recibe el mismo tratamiento mediante [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Declare sus tipos de columna `FileField` o `ImageField` en sus modelos, y `starlette-admin` los detecta, muestra el campo de administración correspondiente y registra una ruta para servir los archivos almacenados. Usted configura el almacenamiento mediante el `StorageManager` propio de sqlalchemy-file, respaldado por contenedores de Apache Libcloud, y las cargas se incorporan a la transacción de la sesión, de modo que una sesión revertida descarta el archivo almacenado.

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

Consulte [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) para ver una aplicación completa con varios almacenamientos, validación de tipos de contenido y campos con `multiple=True`.

## HasOne y HasMany

Campos relacionales que se muestran como entradas `select2`, respaldados por el endpoint de búsqueda de la vista relacionada.

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

El parámetro `key` apunta al `ModelView` correspondiente. Registre ambas vistas en la misma instancia de `Admin` para que las claves se resuelvan correctamente.

---

## Próximos pasos

* [Filtros](filters.md): Personalice el constructor de filtros en sus páginas de lista.
* [Almacenamiento de archivos](file-storage.md): Configure backends de almacenamiento para `FileField` e `ImageField`.
* [Campos personalizados](../advanced/custom-fields.md): Cree un campo personalizado.
