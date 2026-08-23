---
title: Guía de migración
description: Guía de actualización para migrar de versiones anteriores de starlette-admin
  a la última versión, incluyendo cambios importantes y nuevas funcionalidades.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Guía de migración

Esta página recopila las instrucciones de actualización entre las versiones de `starlette-admin`. Vaya a la sección que corresponda a la versión desde la que está actualizando.

---

## De 0.17.x a 1.0.0

Esta versión refactoriza los componentes internos de `starlette-admin` e introduce un amplio conjunto de nuevas funcionalidades. Si bien la API de alto nivel se mantiene prácticamente sin cambios, la actualización más significativa es la reescritura del renderizado de la página de lista. Hemos eliminado DataTables en favor de una tabla renderizada en el servidor. La mayoría de las demás actualizaciones consisten en cambios de nombre o modificaciones menores en las firmas.

Esta guía cubre todos los cambios importantes en el orden en el que es más probable que los encuentre. Cada sección compara la API antigua con su reemplazo. Si su implementación se basa en lo básico o en personalizaciones ligeras (como una instancia de `Admin`, algunas subclases de `ModelView`, `fields` y `searchable_fields`), su migración probablemente se limitará a las secciones de [Requisitos](#requisitos) y [El constructor de Admin](#el-constructor-de-admin), además de algunos cambios de nombre.

Las personalizaciones de la antigua página de lista requieren mayor atención. Las opciones de DataTables y las funciones de renderizado en JavaScript no tienen un equivalente directo y deben trasladarse a plantillas del lado del servidor (consulte [Eliminación de DataTables](#eliminacion-de-datatables)).

!!! tip
    Actualice sus dependencias en un solo paso e inicie su aplicación. La mayoría de los atributos eliminados o renombrados generan errores claros al arrancar en lugar de fallar silenciosamente en tiempo de ejecución.

### Novedades

Además de los cambios importantes descritos a continuación, esta versión incluye:

* **Tablas de lista nativas:** DataTables ha sido eliminado en favor de una implementación integrada y renderizada en el servidor. El estado de la tabla ahora se controla completamente mediante la URL, lo que significa que todas las configuraciones de página, filtros y ordenación se pueden compartir y marcar como favoritos de inmediato.
* **[Filtros](user-guide/filters.md):** Un constructor de filtros anidado `AND`/`OR` reemplaza al SearchBuilder de DataTables. Los filtros se derivan de los tipos de campo y son totalmente extensibles en Python puro. Puede escribir una clase de filtro sin necesidad de JavaScript.
* **[Importación y exportación del lado del servidor](user-guide/export-import.md):** Importe datos desde CSV, JSON, Excel y más, con informes de errores por fila, junto con exportadores del lado del servidor (CSV, JSON, Excel, PDF, etc.) que reemplazan los botones del lado del cliente de DataTables.
* **[Eventos](advanced/events.md):** Suscríbase a hooks del ciclo de vida como `before_create`, `after_edit_committed`, `after_login` y varios eventos de acciones.
* **[Temas](advanced/custom-themes.md) y [Plugins](advanced/plugins.md):** Empaquete y reutilice estéticas y comportamientos personalizados. Hay plantillas de Cookiecutter disponibles para ayudarle a comenzar rápidamente.
* **[Widgets y paneles de control](user-guide/custom-views.md):** Cree páginas de índice y vistas personalizadas usando `StatWidget`, `ChartWidget`, `TableWidget` y más.
* **[Diseño de formularios](advanced/form-layout.md):** Organice los formularios de creación/edición de forma lógica usando filas, columnas, fieldsets y pestañas.
* **[Edición en línea](user-guide/inline-edit.md):** Edite un solo campo directamente desde la página de lista.
* **[Formularios en línea](user-guide/inline-forms.md):** Edite modelos relacionados dentro de un formulario principal usando `InlineModelView`.
* **Otras mejoras:** [Mensajes flash](user-guide/flash-messages.md), [inicio de sesión OAuth](user-guide/auth.md), un [backend para Tortoise ORM](integrations/tortoise.md), nuevos campos (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), `validators` a nivel de campo y funcionalidad de copiado al portapapeles en cualquier campo.
* **[Registro de eventos](user-guide/admin.md#depuracion):** El paquete ahora registra internamente bajo el namespace `starlette_admin`, silencioso por defecto. Pase `Admin(debug=True)` o llame a `starlette_admin.logging.configure_logging()` para ver el enrutamiento de solicitudes, el middleware y las decisiones de permisos en la consola, lo cual resulta especialmente útil durante la migración.
* **Mayor cobertura de pruebas:** La suite de pruebas es ahora sustancialmente más grande e incluye pruebas end-to-end con Playwright que validan los flujos de trabajo críticos de la interfaz de administración.
* **Paquete más ligero:** El tamaño del paquete publicado en PyPI se ha reducido en un ~50 %.

### Requisitos

* **Soporte de Python:** Se requiere Python 3.11 o posterior. El soporte para Python 3.9 y 3.10 ha sido eliminado.
* **Dependencias principales:** `itsdangerous` es ahora una dependencia principal utilizada para firmar las cookies del panel de administración (tokens CSRF y mensajes flash).
* **Nuevos extras opcionales:**

    | Extra | Habilita |
    | --- | --- |
    | `starlette-admin[email]` | Validación del lado del servidor de `EmailField` mediante `email-validator` |
    | `starlette-admin[pdf]` | Exportación a PDF mediante `reportlab` |
    | `starlette-admin[s3]` | Almacenamiento de archivos en S3 mediante `aiobotocore` |
    | `starlette-admin[tinymce]` | Sanitización de HTML de `TinyMCEEditorField` mediante `nh3` |
    | `starlette-admin[i18n]` | Traducciones mediante `babel` (sin cambios) |

* **Backend Beanie:** Se requiere Beanie 2.0 o posterior.
* **Backend Odmantic:** Eliminado. Si depende de él, manténgase en `starlette-admin<=0.17.1` y muestre su interés [abriendo un issue](https://github.com/jowilf/starlette-admin/issues); el soporte puede volver a agregarse si hay suficiente demanda.

### El constructor de Admin

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` se renombra a `static_dir`.
* **Defina un `secret_key`.** Esta clave firma las cookies de CSRF y de mensajes flash. Si se omite, se genera una clave aleatoria al arrancar (lo cual es aceptable para desarrollo). Sin embargo, los valores firmados se invalidarán en cada reinicio y entre varios workers. Pase siempre un secreto estable en producción.
* `logo_url`, `login_logo_url` y `favicon_url` aceptan ahora un callable `(request) -> str | None`. Esto reemplaza la personalización de marca por solicitud que proporcionaba anteriormente `AdminConfig`.
* **Nuevos parámetros opcionales:** `theme`, `plugins`, `additional_loaders`, `import_config` y `export_config`.
* **Especificidades de SQLAlchemy:** El primer argumento es ahora `session_provider`. Acepta un `Engine` o `AsyncEngine`, y ahora también acepta un `sessionmaker` o `async_sessionmaker`. Las llamadas existentes a `Admin(engine)` seguirán funcionando.
* `timezone_config` tiene como valor predeterminado `TimezoneConfig()` en lugar de `None`. Los valores de fecha y hora se muestran ahora en la zona horaria local del usuario de forma predeterminada. Pase `timezone_config=None` para conservar los valores originales.

### Identificadores de vista renombrados

La convención de nombres para las vistas está ahora unificada. Actualice los constructores de `ModelView` y los atributos de clase en consecuencia:

| Antes | Después |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

Tenga en cuenta que `Link` y `DropDown` también usan `menu_label` en lugar de `label`.

### Eliminación de DataTables

La página de lista ya no utiliza DataTables. Los atributos que anteriormente lo configuraban han sido eliminados por completo:

| Eliminado | Reemplazo |
| --- | --- |
| `datatables_options` | Ninguno. La tabla se renderiza en el servidor. Personalícela mediante plantillas. |
| `search_builder` | El nuevo [constructor de filtros](user-guide/filters.md), habilitado por `searchable_fields`. |
| `responsive_table` | Ninguno. La tabla gestiona el desbordamiento de forma nativa. |
| `save_state` | Siempre activo. El estado de la lista (página, ordenación, filtros, búsqueda, columnas visibles) ahora vive en la URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (una lista de clases de filtro). |
| `BaseField.render_function_key` | `BaseField.list_template` (plantilla Jinja del lado del servidor). |

Si anteriormente escribía funciones de renderizado personalizadas en JavaScript o plugins de DataTables, trasládelos a anulaciones de `list_template`. Cada campo renderiza ahora su celda de lista directamente desde `templates/fields/list/*.html`.

### Acciones

Los manejadores de acciones por lotes reciben ahora un objeto `ActionSelection` en lugar de una lista de claves primarias. Esto permite el nuevo banner de «seleccionar todo lo que coincide», dirigido a todas las filas que coinciden con el filtro actual sin materializarlas del lado del cliente.

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* Métodos como `selection.rows()`, `selection.pks()` y `selection.count()` resuelven las filas objetivo de forma diferida. Esto aplica tanto si el usuario marcó las filas individualmente como si seleccionó todas las filas que coinciden.
* Propiedades como `selection.is_select_all`, `selection.filters` y `selection.q` le permiten delegar la operación como una única consulta masiva.
* La devolución de una cadena con el mensaje de éxito se reemplaza por los [mensajes flash](user-guide/flash-messages.md).
* Los manejadores de acciones de fila conservan su firma original `(request, pk)`.
* **Nuevas opciones de `@action`:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` y callables `form` por solicitud.

### Autenticación

El módulo `starlette_admin/auth.py` es ahora el paquete `starlette_admin.auth`. Las importaciones existentes desde `starlette_admin.auth` seguirán funcionando, pero el contrato del proveedor ha cambiado.

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* Los métodos `is_authenticated`, `get_admin_user` y `get_admin_config` se fusionan en un único método `authenticate(request) -> AdminUser | None`. Devolver `None` indica un estado no autenticado.
* Los métodos `login` y `logout` ya no reciben ni devuelven la `response` preparada. Devuelva `None` para la redirección predeterminada, o devuelva una `Response` personalizada para anular este comportamiento.
* `AdminConfig` ha sido eliminado. Gestione los títulos y logos por solicitud usando la forma callable de `logo_url` y `login_logo_url` en la instancia de `Admin`.
* Un [`OAuthProvider`](user-guide/auth.md#oauthprovider-flujo-de-redireccion-oauth2oidc) integrado gestiona los flujos de inicio de sesión OAuth2/OIDC desde el primer momento.
* El decorador `login_not_required` permanece sin cambios.

### Exportación e importación

Las exportaciones se han trasladado de los botones del lado del cliente de DataTables a endpoints de streaming del lado del servidor. La funcionalidad de importación es completamente nueva y `ExportType` ya no existe.

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` es ahora `exporters`. Acepta una lista de nombres de formato o instancias de `BaseExporter`. Los integrados admitidos incluyen `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` y `pdf`. Los formatos distintos de `csv` o `json` requieren `tablib`, y PDF requiere el extra `pdf`.
* `importers` acepta una lista de nombres de formato o instancias de `BaseImporter`. Los integrados admitidos incluyen `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` y `html`. Los formatos distintos de `csv`, `tsv` o `json` requieren `tablib`.
* `export_fields` (una lista de inclusión) se reemplaza por `exclude_fields_from_export` (una lista de exclusión). Esto coincide con la convención de nombres de los demás atributos `exclude_fields_from_*`.
* Los campos también aceptan `exclude_from_export` y `exclude_from_import` de forma individual.
* Configure límites globales usando `ExportConfig` e `ImportConfig` en la instancia de `Admin`. Consulte la documentación de [Exportación e importación](user-guide/export-import.md) para más detalles.

### Campos personalizados y anulaciones de plantillas

Las plantillas de campo han sido reorganizadas. Actualice sus rutas si anula plantillas integradas o distribuye campos personalizados:

| Antes | Después |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (función de renderizado del lado del cliente) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (ruta) | Mismo nombre de atributo, nuevo prefijo de ruta `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

Entre las nuevas capacidades por campo que puede explorar se incluyen `validators`, `filters`, `default`, hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard` y un diccionario `extra` para metadatos arbitrarios. Revise la documentación de [Campos personalizados](advanced/custom-fields.md) para más información.

### CustomView

La clase `CustomView` ya no acepta `template_path` ni `methods`. Cree páginas sencillas usando [widgets](user-guide/custom-views.md). Para páginas que requieren control total, herede de `CustomView` y declare sus rutas directamente.

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

El decorador `@route` también permite a cualquier vista exponer endpoints adicionales para necesidades como datos de gráficos en JSON o webhooks.

### Backends personalizados

Si implementó `BaseModelView` contra una fuente de datos personalizada, tenga en cuenta el contrato de acceso a datos actualizado:

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* El parámetro `where` de tipo cadena se divide en `q` (para los términos de búsqueda de texto completo) y `filters` (un árbol tipado de `FilterGroup` proporcionado por el constructor de filtros).
* El parámetro `order_by` (anteriormente una lista de cadenas con el formato `campo dirección`) es ahora `sorts`, que recibe una lista de tuplas `(field_name, direction)`.
* Cada backend incluye ahora un registro de filtros que asigna tipos de campo a implementaciones de filtros. Consulte la documentación de [Backend personalizado](integrations/custom-backend.md) para conocer el contrato completo y ver un ejemplo funcional.

### Cambios de comportamiento a revisar

* **Zonas horarias:** Los valores de fecha y hora se renderizan en la zona horaria local del usuario de forma predeterminada (consulte la nota sobre `timezone_config` en la sección El constructor de Admin).
* **Estado en la URL:** El estado de la lista vive ahora en la URL. Las URL del panel de administración marcadas como favoritas desde versiones anteriores mostrarán estados de lista predeterminados, porque los estados guardados de DataTables no se migran.
* **Validación de correo electrónico:** `EmailField` valida ahora en el servidor cuando `email-validator` está instalado.
* **Protección CSRF:** La protección CSRF está integrada y se basa en cookies. Si anteriormente envolvía el panel de administración con middleware CSRF personalizado, puede eliminarlo sin riesgo. Asegúrese de que su `secret_key` esté definida para que los tokens sobrevivan a los reinicios del servidor.
* **Tamaño de carga de FileField:** `FileField.max_size` tiene ahora como valor predeterminado 50 MB en lugar de ilimitado. Pase `max_size=None` para restaurar el comportamiento anterior sin límites, o defina un valor explícito para cambiar el límite.

### Eliminado sin reemplazo

* `AdminConfig` (consulte [Autenticación](#autenticacion)).
* `datatables_options`, `responsive_table` y `save_state` (consulte [Eliminación de DataTables](#eliminacion-de-datatables)).
* El backend Odmantic (consulte [Requisitos](#requisitos)).

## Obtener ayuda

Si encuentra un problema de migración no cubierto en esta guía, por favor [abra un issue](https://github.com/jowilf/starlette-admin/issues). Incluya una reproducción mínima del problema y especifique la versión desde la que está actualizando. Ejecutar con [`Admin(debug=True)`](user-guide/admin.md#depuracion) suele revelar la causa directamente, y los registros resultantes son una gran adición a su reporte.
