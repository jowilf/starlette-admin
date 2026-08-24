---
title: Exportación e importación
description: Habilite la funcionalidad de exportación en CSV, JSON y PDF, así como
  las importaciones masivas de datos con validación en starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# Exportación e importación

Cada página de lista permite a los usuarios exportar datos a un archivo e importar datos desde un archivo, de modo que no tenga que escribir rutas personalizadas.

## Visión general

* **Exportación:** Los usuarios seleccionan el botón de la barra de herramientas y luego configuran el alcance, los campos, el formato y el nombre del archivo.
* **Importación:** Los usuarios seleccionan el botón de la barra de herramientas para abrir un asistente de tres pasos: carga, vista previa y resultados.
* **Formatos:** CSV, JSON, XLSX, ODS, YAML, PDF y formatos personalizados están disponibles de forma predeterminada.
* **Upsert:** Las importaciones pueden actualizar opcionalmente registros existentes que coincidan por clave primaria.
* **Integración:** Ambas funciones funcionan junto con el filtrado, la ordenación, la selección de filas y los campos respaldados por almacenamiento.
* **Sin endpoints adicionales:** Todo viene incluido con la vista.

## Ejemplo mínimo

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()

class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))

```

`ProductView` ahora muestra un botón de **Exportar** y un botón de **Importar** en la barra de herramientas de la lista. Cada cuadro de diálogo ofrece exactamente los formatos que usted indique en `exporters` e `importers`.

---

## Habilitar la exportación

El atributo `exporters` enumera los formatos que se expondrán, como cadenas simples de extensión:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

El valor predeterminado es `["csv", "json"]`. La siguiente tabla enumera todos los formatos integrados y el paquete que requieren. Los formatos `csv`, `tsv` y `json` no necesitan dependencias adicionales. Todos los demás formatos tabulares usan `tablib`, y `pdf` usa `reportlab`. Una cadena de formato desconocida, o un formato cuyo paquete no esté instalado, genera un error al inicio.

| Formato | Requisito de instalación |
| --- | --- |
| `csv`, `tsv`, `json` | Incluido en el núcleo |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Anular las opciones de formato

Cada cadena de formato corresponde a una instancia de exporter preconfigurada con valores predeterminados sensatos. Cuando un formato necesita una configuración diferente, pase una instancia del exporter en lugar de la cadena. Puede mezclar cadenas e instancias en la misma lista:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` reenvía los argumentos por palabra clave a `csv.writer` y acepta un parámetro `escape_formulas`. `TablibExporter(format, **kwargs)` cubre todos los formatos de tablib y reenvía los argumentos por palabra clave a `tablib.Dataset.export()`.

!!! warning
    El escape de fórmulas está desactivado de manera predeterminada. Si los campos exportados pueden contener cadenas proporcionadas por el usuario, establezca `escape_formulas=True` en `CsvExporter`, `TsvExporter` o `TablibExporter` para evitar la inyección de fórmulas cuando alguien abra el archivo en una aplicación de hojas de cálculo. Consulte [Inyección de fórmulas](security.md#formula-injection).

La exportación está activada de forma predeterminada. El botón de **Exportar** aparece en la barra de herramientas siempre que la lista `exporters` no esté vacía. Para restringir quién puede exportar, anule el método `can_export(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### El cuadro de diálogo de exportación

La exportación es una acción global integrada. Al seleccionar **Exportar**, se abre un cuadro de diálogo donde el usuario configura la exportación antes de descargarla.

* **Alcance:** Qué exportar. Las opciones son «Filas seleccionadas», la opción predeterminada cuando hay filas marcadas; «Todas las filas coincidentes», disponible desde el banner de seleccionar todo; y «Página actual», la opción predeterminada cuando no hay nada seleccionado.
* **Campos:** Una casilla de verificación por cada campo exportable. Si desmarca una casilla, esa columna se descarta. Los campos marcados con `exclude_from_export=True` nunca aparecen aquí.
* **Formato:** Una entrada por cada formato en `exporters`.
* **Nombre de archivo:** De forma predeterminada, es la clave de la vista. El servidor añade la extensión del archivo.

Todos los alcances respetan la búsqueda, los filtros y el orden de clasificación actuales de la página de lista, de modo que lo que el usuario ve es exactamente lo que exporta.

### El límite de filas

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)

```

`ExportConfig.max_rows` tiene un valor predeterminado de 100 000. El límite se aplica a la cantidad de filas que realmente produciría el alcance elegido, y el panel de administración comprueba ese recuento antes de obtener cualquier fila. Cuando el recuento supera el límite, el administrador muestra un mensaje de error y redirige de vuelta a la página de lista en lugar de generar el archivo. Esto evita que una exportación amplia sin filtrar sobre una tabla grande bloquee la solicitud. Establezca `max_rows=None` para eliminar el límite.

---

## Habilitar la importación

El atributo `importers` funciona exactamente igual que `exporters` y acepta cadenas de formato:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Los formatos de importación integrados son `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` y `html`, con las mismas dependencias que sus contrapartes de exportación. Para anular los valores predeterminados de un formato, pase una instancia del importer, como `CsvImporter(delimiter=";")` desde `starlette_admin.importers`.

La importación está activada de forma predeterminada, con `["csv", "json"]`. El botón de **Importar** aparece en la barra de herramientas siempre que la lista `importers` no esté vacía. Para restringir quién puede importar, anule el método `can_import(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### El asistente de importación

Al seleccionar **Importar**, se abre un asistente de tres pasos. No se escribe nada en la base de datos antes de la confirmación final, y ningún archivo se almacena en el servidor entre pasos: el navegador retiene el archivo y lo vuelve a enviar en cada paso.

1. **Carga:** Elija un formato, seleccione un archivo y, opcionalmente, marque **Actualizar registros existentes por clave primaria**. Al marcar esta opción, una fila cuya clave primaria coincide con un registro existente actualiza dicho registro en lugar de crear uno nuevo. De lo contrario, todas las filas se crean.
2. **Vista previa:** Al enviar la carga se ejecuta una pasada completa de validación sin escribir nada. El asistente muestra un resumen, los mapeos de columnas, filas de ejemplo y una tabla detallada de errores.
3. **Resultado:** El asistente confirma la importación y reporta los recuentos finales de registros creados, actualizados y omitidos. Las filas que fallaron la validación en la vista previa se omiten.

!!! tip
    Para permitir que el backend genere las claves primarias, desmarque la columna de la clave primaria en el mapeo de la vista previa. Las filas importadas no llevarán entonces ningún valor de clave, de modo que volver a importar un archivo que usted exportó creará registros nuevos en lugar de fallar por identificadores obsoletos.

### Límites de carga y filas

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

El endpoint de importación refleja el límite de filas de la exportación. `ImportConfig.max_rows` tiene un valor predeterminado de 100 000 y se aplica antes de crear cualquier registro. El administrador cuenta las filas del archivo cargado en una pasada preliminar y rechaza con un error HTTP 400 todo archivo que contenga más filas que el límite. Establezca `max_rows=None` para eliminar el límite. `ImportConfig.max_upload_size` también limita las cargas a 10 MB de forma predeterminada.

### Coincidencia de encabezados

El asistente compara cada encabezado del archivo primero con el `label` de su campo y luego con su `name`. Un archivo con la columna `Name` y un archivo con la columna `name` se mapean ambos a un campo llamado `name`. Las columnas sin coincidencia se ignoran, y los campos sin una columna correspondiente reciben `None`.

## Campos de archivo

Una vista con un `FileField` o un `ImageField` respaldado por almacenamiento se exporta como un archivo ZIP, de modo que el contenido de los archivos viaja junto con los datos de las filas:

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

Exportar `ProductView` a CSV produce un `export.zip` con esta estructura:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

La columna `photo` en `export.csv` contiene la ruta relativa al ZIP del archivo, `assets/<storage-name>/<key>`, lo que mantiene el CSV legible en una aplicación de hojas de cálculo. El administrador obtiene cada archivo referenciado desde su backend de almacenamiento y lo empaqueta bajo `assets/`.

La importación no acepta archivos ZIP. `FileField` e `ImageField` siempre se excluyen de la importación, porque tienen `exclude_from_import=True` de forma predeterminada, por lo que el asistente ignora la columna `photo` durante la carga. Vuelva a importar un archivo de datos simple y luego adjunte los archivos mediante los formularios de creación o edición.


## Escribir un exporter personalizado

Para escribir un exporter personalizado, cree una subclase de `BaseExporter` e implemente el método `generate`. La clase base gestiona el empaquetado en ZIP, la descarga de archivos y los encabezados de respuesta:

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField

class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

Los datos de `rows` llegan ya depurados: el administrador reemplaza previamente cada valor de `FileField` e `ImageField` por su cadena de ruta relativa al ZIP, de modo que su método `generate` nunca manipula diccionarios de archivos. Registre `MarkdownExporter()` en su lista `exporters` para mostrarlo en el menú desplegable de formatos.

## Escribir un importer personalizado

Para escribir un importer personalizado, cree una subclase de `BaseImporter` e implemente `parse` como un generador asíncrono que produce un diccionario por fila:

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext

class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## Próximos pasos

* **[Almacenamiento de archivos](file-storage.md):** Configure los backends de almacenamiento referenciados en el paquete ZIP de exportación.
* **[Seguridad](security.md):** Límites de filas para la exportación y límites de tamaño de carga para la importación.
* **[Acciones](actions.md):** Añada acciones masivas y por fila junto a la exportación e importación.
