---
title: Campos
description: Referencia completa de todos los campos integrados en starlette-admin
  para mapear sus columnas de base de datos a componentes de interfaz.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Campos

Los campos son los componentes básicos de sus vistas. En el fondo son simples dataclasses de Python: cada atributo que pasa al constructor de un campo se convierte en un campo del dataclass, y cada tipo de campo hereda de `BaseField`, por lo que puede inspeccionarlo, crear subclases o instanciarlo directamente.

## Atributos comunes

Cada tipo de campo hereda este conjunto de atributos de configuración de `BaseField`.

| Atributo | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `name` | `str` | **Obligatorio** | El nombre del atributo en su modelo. |
| `label` | `str | None` | `name` en formato título | La cabecera de columna y la etiqueta del formulario. |
| `help_text` | `str | None` | `None` | Texto de ayuda que se muestra debajo del campo del formulario. |
| `required` | `bool` | `False` | Exige un valor en los formularios, tanto en el cliente como en el servidor. |
| `validators` | `list[Validator]` | `[]` | Validadores del lado del servidor que se ejecutan contra el valor enviado. Consulte [Validación](#validacion). |
| `disabled` | `bool` | `False` | Atenúa y bloquea el campo en los formularios. |
| `read_only` | `bool` | `False` | Muestra el campo pero impide su edición. |
| `default` | `Any | Callable` | `None` | El valor de precarga en el formulario de creación. |
| `getter` | `Callable | None` | `None` | Reemplaza la búsqueda del atributo del modelo al leer el valor. Consulte [Cálculo, formateo y análisis de valores](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Formateo de visualización por acción, que reemplaza la serialización para esa acción. Consulte [Cálculo, formateo y análisis de valores](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Análisis de entrada por acción, que reemplaza el análisis predeterminado del campo. Consulte [Cálculo, formateo y análisis de valores](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Se incluye cuando coincide con el parámetro de búsqueda `q`. |
| `orderable` | `bool` | `True` | Agrega un enlace de ordenación en la cabecera de la lista. |
| `copy_to_clipboard` | `bool` | `False` | Agrega un botón de copiado junto al valor en la página de detalle. |
| `filters` | `list | None` | `None` | Sustitución explícita de los filtros de la página de lista. |
| `extra` | `dict[str, Any]` | `{}` | Un diccionario para sus propios metadatos. |

### Controles de visibilidad

Utilice estas marcas booleanas, todas con `False` como valor predeterminado, para controlar dónde aparece un campo:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Definición de valores predeterminados

El atributo `default` acepta un valor estático, una función sin argumentos o una función que recibe la petición:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Cálculo, formateo y análisis de valores {#computing-formatting-and-parsing-values}

Todo campo acepta tres hooks invocables, `getter`, `formatter` y `parser`, que interceptan y transforman los datos mientras se desplazan entre su modelo y la interfaz. Cada uno admite una función síncrona o asíncrona.

#### `getter`: lectura de valores personalizados

El hook `getter` reemplaza la búsqueda predeterminada con `getattr()` cuando el campo lee una instancia del modelo. El campo llama a `getter(request, obj)` y muestra el valor devuelto.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Como los valores de `getter` rara vez se corresponden con una columna física de la base de datos, funcionan mejor junto con una visualización de solo lectura. [`ComputedField`](#computedfield) es un atajo integrado para esa combinación.

#### `formatter`: transformación de la salida mostrada

El hook `formatter` define cómo se representa un valor almacenado en páginas específicas. Asocia una acción de `RequestAction`, como `LIST`, `DETAIL` o `EXPORT`, a una función `(request, value) -> value`.

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

**Comportamientos de formateo que debe tener en cuenta:**

* **Los nulos llegan al formatter:** A diferencia de la serialización predeterminada, los formatters reciben valores `None`, por lo que puede proporcionar texto alternativo, como `"unset"` en el ejemplo anterior.
* **La serialización se omite:** Un formatter coincidente reemplaza los métodos `serialize_value` y `serialize_none_value` del campo. El valor de retorno se utiliza tal cual, de modo que el formatter es plenamente responsable de la salida final.
* **Requisito de JSON:** Los valores devueltos para las acciones `LIST` y `RELATION_LOOKUP` deben seguir siendo serializables a JSON.

#### `parser`: procesamiento de datos entrantes

El hook `parser` anula el análisis predeterminado que realiza el campo sobre los datos enviados o importados. Asocia una acción de `RequestAction` a una función `(request, raw) -> value`.

* **Formularios (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` es la entrada del formulario enviado, o una lista cuando `multiple=True`.
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

Tras el análisis, el valor devuelto pasa por la cadena estándar de validación, primero `required` y luego `validators`, exactamente igual que si el campo hubiera analizado los datos por sí mismo.

!!! tip "¿Hooks o una subclase?"
    Para una personalización puntual en un único campo, rara vez necesita crear una subclase. Pase estos hooks como argumentos del constructor para gestionar la lectura, el formateo de visualización y el análisis de entrada. [Cree una subclase del campo](../advanced/custom-fields.md) cuando reutilice la lógica en varias vistas, o cuando necesite modificar las plantillas de renderizado HTML.

### Validación {#validacion}

La validación del lado del servidor se ejecuta en cada campo cuando se envía un formulario de creación o edición, de modo que los datos incorrectos nunca lleguen a la base de datos.

El ciclo de vida es fijo:

1. **Valores vacíos:** Cuando el valor enviado está vacío, por ejemplo `None`, `""` o una colección vacía, solo se comprueba la marca `required`. Los validadores se omiten.
2. **Valores poblados:** Cuando hay datos presentes, cada función de la lista `validators` se ejecuta en orden contra el valor analizado.

#### Firma de los validadores

Un validador recibe cuatro argumentos: `(request, field, value, form_values)`.

* **`request`:** El objeto de petición actual de Starlette.
* **`field`:** La instancia del campo que se está validando.
* **`value`:** El valor analizado enviado para este campo.
* **`form_values`:** Un diccionario con todos los datos analizados del formulario, indexados por nombre de campo, lo que le permite inspeccionar otros campos.

Para rechazar un valor, lance un `ValueError`. El administrador captura el primer error de un campo, omite los validadores restantes de ese campo y recopila todos los errores para mostrarlos junto a sus campos correspondientes.

#### Validadores integrados

El módulo [`starlette_admin.validators`](../api/validators.md) proporciona reglas estándar:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Validación personalizada y asíncrona

Escriba validadores personalizados como funciones síncronas o asíncronas. Reciben la petición (`request`), por lo que pueden consultar la base de datos para comprobar restricciones complejas.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Con el argumento `form_values`, un validador a nivel de campo también puede imponer una regla que dependa de otro campo enviado.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Reglas de validación según el contexto

* **Campos de relación:** `HasOne` y `HasMany` reciben las claves primarias de los registros relacionados durante la validación.
* **Campos de archivo:** La validación se ejecuta una vez por cada `UploadFile` en la carga útil. Consulte [Campos de archivo y multimedia](#campos-de-archivo-y-multimedia).
* **Validación entre campos:** Utilice `form_values` para una dependencia sencilla. Para una regla que abarque todo el formulario, anule el método `validate()` en su vista. La validación a nivel de vista se ejecuta únicamente después de que cada campo haya superado su propia cadena de validación.

### Almacenamiento de metadatos personalizados

`extra` es un simple `dict` que `starlette-admin` nunca lee ni escribe. Utilícelo para adjuntar sus propios datos a una instancia de campo, ya sea para una plantilla personalizada, un hook en su subclase de [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) o cualquier otro punto de integración, sin necesidad de crear una subclase del campo:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Campos de texto

### StringField & TextAreaField

`StringField` muestra un campo de texto de una sola línea para contenido breve. `TextAreaField` lo extiende con un elemento `<textarea>` para textos largos multilínea.

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
| `maxlength` and `minlength` | `int | None` | `None` | Restricciones de longitud de HTML. |
| `placeholder` | `str | None` | `None` | Texto de marcador de posición del campo. |
| `rows` *(solo TextArea)* | `int` | `6` | Número de líneas de texto visibles. |

### TinyMCEEditorField

Extiende `TextAreaField` con un editor WYSIWYG de la biblioteca TinyMCE. Requiere el paquete extra `tinymce`.

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

    `UUIDField` establece `copy_to_clipboard=True` de forma predeterminada. `IPAddressField` acepta `ipv4`, con `True` como valor predeterminado, e `ipv6`, con `False` como valor predeterminado, que controlan las familias de direcciones que acepta su validador predeterminado.

### PasswordField

Muestra un elemento `<input type="password">` en los formularios para ocultar lo que el usuario escribe.

!!! danger
    `PasswordField` enmascara la entrada únicamente en los formularios de creación y edición. No sustituye las plantillas de visualización, por lo que los valores se muestran como **texto plano** en las páginas de lista y detalle, y registra los valores enviados en bruto a nivel `DEBUG`.

    Establezca `exclude_from_list = True` y `exclude_from_detail = True` en los campos de contraseña, y desactive el registro `DEBUG` en producción.

## Campos numéricos

Los campos numéricos manejan enteros, flotantes y decimales.

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

| Atributo adicional | Aplica a | Descripción |
| --- | --- | --- |
| `min` y `max` | Integer, Decimal | Valores mínimo y máximo permitidos. |
| `step` | Integer, Decimal | La restricción de incremento. |

!!! note
    `FloatField` funciona de manera diferente: se muestra como un campo de texto plano, convierte el envío a `float` y no admite `min`, `max` ni `step`.

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
| `search_format` | `str | None` | Específico del ORM | Formato empleado para construir consultas de búsqueda en la base de datos. |

!!! note
    Cuando el soporte de zonas horarias está activado, `DateTimeField` convierte automáticamente entre la zona horaria de visualización y la de la base de datos.

### ArrowField

Una variante de `DateTimeField` respaldada por un objeto `Arrow`. Fuera de los formularios de edición, muestra un tiempo relativo humanizado, como «hace 3 horas». Requiere el paquete `arrow`.

## Campos de selección y colección

### EnumField

El campo de selección de propósito general. Muestra un menú desplegable `<select>`, o un multi-select `select2` cuando `multiple=True`. Puede respaldarlo con una subclase de `Enum` de Python, una lista de tuplas o opciones cargadas en tiempo de petición.

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
| `enum` | `type[Enum] | None` | Genera las opciones a partir de una clase `Enum` de Python. |
| `choices` | `Sequence | None` | Pares estáticos `(value, label)`, o valores sueltos. |
| `choices_loader` | `Callable | None` | Calcula las opciones por cada petición. |
| `multiple` | `bool` | Activa el multi-select y almacena los valores como una lista. |

!!! important
    Proporcione exactamente uno de los siguientes: `enum`, `choices` o `choices_loader`.

`TimeZoneField`, `CountryField` y `CurrencyField` son subclases de `EnumField` respaldadas por los datos de localización de Babel, lo que requiere el extra `i18n`. Localizan sus etiquetas según la petición actual.

### TagsField

Una entrada de etiquetado de texto libre basada en `select2`. Almacena una `list[str]` y no requiere opciones predefinidas.

### ListField

Envuelve otro campo para almacenar una lista ordenada de valores de ese tipo. Se muestra como filas repetibles con controles para añadir y eliminar. El nombre del campo envuelto se convierte en el nombre del `ListField`.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Agrupa varios subcampos en un objeto anidado. Úselo para datos embebidos o tipo estructura, como un documento embebido de MongoDB.

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

Muestra un editor de código y árbol JSON, y almacena un `dict` de Python. Pase un diccionario JSON Schema estándar a `validation_schema` para obtener retroalimentación en el lado del cliente.

### SlugField

Una variante de `StringField` que se completa automáticamente en el cliente a partir de la entrada de otro campo. Una edición manual detiene el autocompletado.

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

Un campo virtual de solo lectura, derivado de la instancia del modelo en el momento de la visualización, sin ninguna columna de base de datos detrás. Se construye sobre el [hook `getter`](#computing-formatting-and-parsing-values) que posee todo campo, y añade los valores predeterminados que necesita una columna virtual: excluido de los formularios de creación, de solo lectura, no buscable y no ordenable.

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

`getter` y `parse_obj` realizan el mismo trabajo: use `getter` para expresiones breves y cree una subclase de `ComputedField` cuando la lógica abarque varias líneas o se reutilice en varias vistas. En los formularios de edición, el campo sigue apareciendo como visualización de texto plano, de modo que el usuario ve el valor calculado actual.

Toda subclase de `ComputedField` mantiene el renderizado de `StringField`. Para calcular un valor que deba representarse como otro tipo, por ejemplo una fecha, una insignia o una imagen, establezca directamente `getter=` en ese tipo de campo, junto con las marcas `read_only` y `exclude_from_*` correspondientes.

## Campos de archivo y multimedia

`FileField` muestra un campo de carga de archivos, y `ImageField` añade una vista previa de imagen y una comprobación de validez. Adjunte un backend `storage=` para guardar las cargas automáticamente y almacenar un diccionario `FileInfo` en formato JSON en la base de datos. Para la configuración completa, consulte la [guía de File Storage](file-storage.md).

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
| `accept` | `str | None` | `None` | Lista separada por comas de extensiones de archivo o tipos MIME aceptados, que se pasa al atributo HTML `accept`. |
| `multiple` | `bool` | `False` | Admite varios archivos en un mismo campo. |
| `storage` | `BaseStorage | None` | `None` | Backend de almacenamiento que guarda las cargas. Sin él, el campo entrega las cargas en bruto a su backend. |
| `upload_folder` | `str` | `""` | Carpeta relativa al almacenamiento donde se guardan los archivos. |
| `max_size` | `int | None` | `None` | Tamaño máximo aceptado de carga, en bytes. |
| `validators` | `list[Validator]` | `[]` | Validadores personalizados; cada uno se invoca como `(request, field, upload)` una vez por archivo cargado, después de las comprobaciones de `accept` y `max_size`. Lance `ValueError` para rechazar. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | Solo para `ImageField`. Cuando está definido, Pillow genera una miniatura acotada al guardar, y la página de lista la utiliza en lugar de la imagen completa. |

!!! note
    `ImageField` antepone una comprobación de validez de imagen basada en Pillow a la lista de `validators`. Cuando Pillow está instalado y hay un almacenamiento configurado, también registra `width` y `height` en el `FileInfo` resultante.

Con `thumbnail_size` definido, el administrador genera una miniatura junto con la imagen completa, conservando la proporción y nunca ampliando la escala, y la almacena bajo su propia clave. Por ejemplo, a `covers/cat.jpg` se le añade un archivo hermano `covers/cat.thumb.jpg`. La página de lista utiliza la miniatura automáticamente. Las filas sin ella, provenientes de datos anteriores o porque `thumbnail_size` no esté definido, recurren a la imagen completa. Un fallo en la generación de la miniatura se registra en el log y nunca provoca el error de la carga.

La página de detalle abre cada imagen de `ImageField` en un lightbox, de modo que los visitantes puedan navegar entre imágenes a resolución completa. Las imágenes que pertenecen al mismo campo (`multiple=True`) se agrupan en una sola galería.

Consulte [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) para ver una aplicación completa y ejecutable, incluido un validador de tipo MIME personalizado.

### Sin almacenamiento

Sin ningún `storage=` adjunto, el campo entrega las cargas a su backend en bruto, en lugar de guardarlas:

* **En los formularios de creación y edición**, el valor analizado es una tupla, `(UploadFile | list[UploadFile] | None, bool)`. El primer elemento es el `UploadFile` en bruto de Starlette, una lista cuando `multiple=True`, o `None` cuando el usuario no seleccionó nada. El segundo elemento es `True` cuando el usuario marca la casilla de eliminación en el formulario de edición, lo que significa que desea eliminar el archivo existente sin reemplazarlo. La lógica `create()` y `edit()` de su backend guarda la carga y respeta la marca de eliminación.
* **En las páginas de lista y detalle**, el campo espera que el valor exponga tres claves, como `dict`, o tres atributos, como objeto: `url`, obligatorio, el destino del enlace; `filename`, la etiqueta de visualización; y `content_type`, que selecciona el icono del tipo de archivo.

Este contrato es la forma en que las integraciones ORM descritas a continuación conectan su propio manejo de archivos al mismo campo.

### Columnas de archivo nativas del ORM

**MongoEngine** admite `mongoengine.FileField` y `mongoengine.ImageField` desde el primer momento, con **GridFS** como almacenamiento. El administrador sube, sirve y elimina archivos en GridFS por usted. No necesita configuración de `storage=`: basta con listar el campo por su nombre.

**SQLAlchemy** recibe el mismo tratamiento mediante [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Declare sus tipos de columna `FileField` o `ImageField` en sus modelos, y `starlette-admin` los detectará, mostrará el campo de administrador correspondiente y registrará una ruta para servir los archivos almacenados. Configure el almacenamiento a través del propio `StorageManager` de sqlalchemy-file, respaldado por contenedores de Apache Libcloud, y las cargas se incorporan a la transacción de la sesión, de modo que una sesión revertida descarta el archivo almacenado.

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

Consulte [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) para ver una aplicación completa con varios almacenamientos, validación de tipo de contenido y campos con `multiple=True`.

## HasOne & HasMany

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

## ¿Qué sigue?

* [Filtros](filters.md): Personalice el constructor de filtros de sus páginas de lista.
* [File Storage](file-storage.md): Configure backends de almacenamiento para `FileField` e `ImageField`.
* [Campos personalizados](../advanced/custom-fields.md): Cree un campo personalizado.
