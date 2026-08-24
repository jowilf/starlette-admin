---
title: Guía de migración
description: Guía de actualización para migrar de versiones anteriores de starlette-admin
  a la última versión, incluyendo cambios incompatibles y nuevas funcionalidades.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Guía de migración

Esta página recopila las instrucciones de actualización entre las versiones de `starlette-admin`. Salte a la sección correspondiente a la versión desde la que está actualizando.

---

## De 0.17.x a 1.0.0

Esta versión refactoriza el funcionamiento interno de `starlette-admin` e introduce un amplio conjunto de nuevas funcionalidades. Aunque la API de alto nivel se mantiene prácticamente sin cambios, la actualización más significativa es la reescritura del renderizado de la página de lista. Hemos eliminado DataTables en favor de una tabla renderizada en el servidor. La mayoría de los demás cambios consisten en renombrados o modificaciones menores de firmas.

Esta guía cubre cada cambio incompatible en el orden en el que es más probable que los encuentre. Cada sección compara la API antigua junto con su reemplazo. Si su implementación se basa en lo básico o en personalizaciones ligeras (como una instancia de `Admin`, algunas subclases de `ModelView`, `fields` y `searchable_fields`), su migración probablemente se limitará a las secciones [Requisitos](#requirements) y [Constructor de Admin](#the-admin-constructor), más algunos renombrados.

Las personalizaciones de la página de lista antigua requieren mayor atención. Las opciones de DataTables y las funciones de renderizado en JavaScript no tienen equivalente directo y deben trasladarse a plantillas del lado del servidor (consulte [Eliminación de DataTables](#datatables-removal)).

!!! tip
    Actualice sus dependencias en un solo paso e inicie su aplicación. La mayoría de los atributos eliminados o renombrados generan errores claros al arrancar en lugar de fallar silenciosamente en tiempo de ejecución.

### Novedades

Además de los cambios incompatibles descritos a continuación, esta versión incluye:

* **Tablas de lista nativas:** DataTables ha sido eliminado en favor de una implementación integrada renderizada en el servidor. El estado de la tabla ahora está completamente controlado por la URL, lo que significa que todas las configuraciones de página, filtro y ordenación son inmediatamente compartibles y guardables como marcadores.
* **[Filtros](user-guide/filters.md):** Un constructor de filtros anidado con `AND`/`OR` sustituye a SearchBuilder de DataTables. Los filtros se derivan de los tipos de campo y son totalmente extensibles en Python puro. Puede escribir una clase de filtro sin necesidad de JavaScript.
* **[Importación y exportación del lado del servidor](user-guide/export-import.md):** Importe datos desde CSV, JSON, Excel y más, con informes de error por fila, junto con exportadores del lado del servidor (CSV, JSON, Excel, PDF, etc.) que sustituyen a los botones del lado del cliente de DataTables.
* **[Eventos](advanced/events.md):** Suscríbase a hooks del ciclo de vida como `before_create`, `after_edit_committed`, `after_login` y varios eventos de acciones.
* **[Temas](advanced/custom-themes.md) y [Plugins](advanced/plugins.md):** Empaquete y reutilice estéticas y comportamientos personalizados. Hay plantillas Cookiecutter disponibles para ayudarle a comenzar rápidamente.
* **[Widgets y dashboards](user-guide/custom-views.md):** Cree páginas de índice y vistas personalizadas usando `StatWidget`, `ChartWidget`, `TableWidget` y más.
* **[Diseño de formularios](advanced/form-layout.md):** Organice los formularios de creación/edición de forma lógica mediante filas, columnas, fieldsets y pestañas.
* **[Edición en línea](user-guide/inline-edit.md):** Edite un solo campo directamente desde la página de lista.
* **[Formularios en línea](user-guide/inline-forms.md):** Edite modelos relacionados dentro de un formulario principal usando `InlineModelView`.
* **Otras mejoras:** [Mensajes flash](user-guide/flash-messages.md), [inicio de sesión OAuth](user-guide/auth.md), un [backend para Tortoise ORM](integrations/tortoise.md), nuevos campos (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), `validators` a nivel de campo y funcionalidad de copiado al portapapeles en cualquier campo.
* **[Logging](user-guide/admin.md#debugging):** El paquete ahora registra internamente bajo el namespace `starlette_admin`, silencioso por defecto. Pase `Admin(debug=True)` o llame a `starlette_admin.logging.configure_logging()` para ver el enrutamiento de solicitudes, middleware y decisiones de permisos en la consola, lo cual resulta especialmente útil durante la migración.
* **Cobertura de pruebas ampliada:** La suite de pruebas es ahora considerablemente más grande, e incluye pruebas end-to-end con Playwright que validan flujos críticos en toda la interfaz de administración.
* **Paquete más ligero**: El tamaño del paquete publicado en PyPI se ha reducido en aproximadamente un 50 %.

### Requisitos {#requirements}

* **Soporte de Python:** Se requiere Python 3.11 o posterior. El soporte para Python 3.9 y 3.10 ha sido eliminado.
* **Dependencias principales:** `itsdangerous` es ahora una dependencia principal utilizada para firmar las cookies del admin (tokens CSRF y mensajes flash).
* **Nuevos extras opcionales:**

    | Extra | Habilita |
    | --- | --- |
    | `starlette-admin[email]` | Validación del lado del servidor de `EmailField` mediante `email-validator` |
    | `starlette-admin[pdf]` | Exportación a PDF mediante `reportlab` |
    | `starlette-admin[s3]` | Almacenamiento de archivos en S3 mediante `aiobotocore` |
    | `starlette-admin[tinymce]` | Saneamiento de HTML de `TinyMCEEditorField` mediante `nh3` |
    | `starlette-admin[i18n]` | Traducciones mediante `babel` (sin cambios) |

* **Backend Beanie:** Se requiere Beanie 2.0 o posterior.
* **Backend Odmantic:** Eliminado. Si depende de él, permanezca en `starlette-admin<=0.17.1` y demuestre su interés [abriendo un issue](https://github.com/jowilf/starlette-admin/issues); el soporte puede volver a añadirse si hay suficiente demanda.

### El constructor de Admin {#the-admin-constructor}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` ha sido renombrado a `static_dir`.
* **Establezca una `secret_key`.** Esta clave firma las cookies CSRF y de mensajes flash. Si se omite, se genera una clave aleatoria al arrancar (lo cual es aceptable para desarrollo). Sin embargo, los valores firmados quedarán invalidados en cada reinicio y entre múltiples workers. Pase siempre un secreto estable en producción.
* `logo_url`, `login_logo_url` y `favicon_url` ahora aceptan un callable `(request) -> str | None`. Esto reemplaza la personalización de marca por solicitud que antes proporcionaba `AdminConfig`.
* **Nuevos parámetros opcionales:** `theme`, `plugins`, `additional_loaders`, `import_config` y `export_config`.
* **Particularidades de SQLAlchemy:** El primer argumento ahora es `session_provider`. Acepta un `Engine` o `AsyncEngine`, y ahora también acepta un `sessionmaker` o `async_sessionmaker`. Las llamadas existentes a `Admin(engine)` seguirán funcionando.
* `timezone_config` tiene como valor predeterminado `TimezoneConfig()` en lugar de `None`. Los datetimes ahora se muestran en la zona horaria local del usuario que los visualiza de forma predeterminada. Pase `timezone_config=None` para conservar los valores originales.

### Identificadores de vista renombrados

La convención de nombres para las vistas ahora está unificada. Actualice los constructores y atributos de clase de sus `ModelView` en consecuencia:

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

### Eliminación de DataTables {#datatables-removal}

La página de lista ya no utiliza DataTables. Los atributos que anteriormente lo configuraban han sido eliminados por completo:

| Eliminado | Reemplazo |
| --- | --- |
| `datatables_options` | Ninguno. La tabla se renderiza en el servidor. Personalícela mediante plantillas. |
| `search_builder` | El nuevo [constructor de filtros](user-guide/filters.md), habilitado por `searchable_fields`. |
| `responsive_table` | Ninguno. La tabla gestiona el desbordamiento de forma nativa. |
| `save_state` | Siempre activo. El estado de la lista (página, ordenación, filtros, búsqueda, columnas visibles) ahora reside en la URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (una lista de clases de filtro). |
| `BaseField.render_function_key` | `BaseField.list_template` (plantilla Jinja del lado del servidor). |

Si previamente escribió funciones de renderizado en JavaScript personalizadas o plugins de DataTables, trasládelos a overrides de `list_template`. Cada campo ahora renderiza su celda de lista directamente desde `templates/fields/list/*.html`.

### Actions

Los manejadores de acciones por lotes ahora reciben un objeto `ActionSelection` en lugar de una lista de claves primarias. Esto da soporte al nuevo banner de «seleccionar todas las coincidencias», que afecta a cada fila que coincide con el filtro actual sin materializarlas en el lado del cliente.

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

* Métodos como `selection.rows()`, `selection.pks()` y `selection.count()` resuelven las filas objetivo de forma diferida (lazy). Esto aplica tanto si el usuario marcó filas individualmente como si seleccionó todas las coincidentes.
* Propiedades como `selection.is_select_all`, `selection.filters` y `selection.q` le permiten delegar la operación como una única consulta masiva.
* Devolver un string de mensaje de éxito se sustituye por los [mensajes flash](user-guide/flash-messages.md).
* Los manejadores de acciones por fila conservan su firma original `(request, pk)`.
* **Nuevas opciones de `@action`:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` y callables `form` por solicitud.

### Autenticación {#authentication}

El módulo `starlette_admin/auth.py` es ahora el paquete `starlette_admin.auth`. Las importaciones existentes desde `starlette_admin.auth` seguirán funcionando, pero el contrato del provider ha cambiado.

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
* Los métodos `login` y `logout` ya no reciben ni devuelven el objeto `response` preparado. Devuelva `None` para la redirección predeterminada, o devuelva un `Response` personalizado para modificar este comportamiento.
* `AdminConfig` ha sido eliminado. Gestione títulos y logos por solicitud usando la forma callable de `logo_url` y `login_logo_url` en la instancia de `Admin`.
* Un [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) integrado gestiona los flujos de inicio de sesión OAuth2/OIDC de forma inmediata.
* El decorator `login_not_required` permanece sin cambios.

### Exportación e importación

Las exportaciones se han trasladado de los botones del lado del cliente de DataTables a endpoints de streaming del lado del servidor. La funcionalidad de importación es totalmente nueva y `ExportType` ya no existe.

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

* `export_types` pasa a ser `exporters`. Acepta una lista de nombres de formato o instancias de `BaseExporter`. Los built-in compatibles incluyen `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` y `pdf`. Los formatos distintos de `csv` o `json` requieren `tablib`, y PDF requiere el extra `pdf`.
* `importers` acepta una lista de nombres de formato o instancias de `BaseImporter`. Los built-in compatibles incluyen `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` y `html`. Los formatos distintos de `csv`, `tsv` o `json` requieren `tablib`.
* `export_fields` (una lista de inclusión) se sustituye por `exclude_fields_from_export` (una lista de exclusión). Esto sigue la convención de nomenclatura de los demás atributos `exclude_fields_from_*`.
* Los campos también aceptan `exclude_from_export` y `exclude_from_import` de forma individual.
* Configure límites globales usando `ExportConfig` y `ImportConfig` en la instancia de `Admin`. Consulte la documentación de [Exportación e importación](user-guide/export-import.md) para más detalles.

### Campos personalizados y overrides de plantillas

Las plantillas de campos se han reorganizado. Actualice sus rutas si hace override de las plantillas integradas o distribuye campos personalizados:

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

Entre las nuevas capacidades por campo que puede explorar se incluyen `validators`, `filters`, `default`, hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard` y un diccionario `extra` para metadatos arbitrarios. Revise la documentación de [Campos personalizados](advanced/custom-fields.md) para obtener más información.

### CustomView

La clase `CustomView` ya no acepta `template_path` ni `methods`. Cree páginas sencillas usando [widgets](user-guide/custom-views.md). Para páginas que requieran control total, herede de `CustomView` y declare sus rutas directamente.

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

El decorator `@route` también permite que cualquier view exponga endpoints adicionales para necesidades como datos JSON de gráficos o webhooks.

### Backends personalizados

Si implementó `BaseModelView` sobre una fuente de datos personalizada, tenga en cuenta el contrato de acceso a datos actualizado:

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

* El parámetro `where` de tipo string se divide en `q` (para términos de búsqueda de texto completo) y `filters` (un árbol tipado de `FilterGroup` proporcionado por el constructor de filtros).
* El parámetro `order_by` (antes una lista de strings `"field direction"`) es ahora `sorts`, que toma una lista de tuplas `(field_name, direction)`.
* Cada backend incluye ahora un registro de filtros que asigna tipos de campo a implementaciones de filtros. Consulte la documentación de [Backend personalizado](integrations/custom-backend.md) para conocer el contrato completo y un ejemplo funcional.

### Cambios de comportamiento a revisar

* **Zonas horarias:** Los datetimes se renderizan en la zona horaria local de quien los visualiza de forma predeterminada (consulte la nota sobre `timezone_config` en la sección Constructor de Admin).
* **Estado en la URL:** El estado de la lista ahora reside en la URL. Las URLs del admin guardadas como marcadores desde versiones anteriores mostrarán estados de lista predeterminados, porque los estados guardados de DataTables no se migran.
* **Validación de correo electrónico:** `EmailField` ahora valida en el servidor cuando `email-validator` está instalado.
* **Protección CSRF:** La protección CSRF está integrada y basada en cookies. Si previamente envolvió el admin con un middleware CSRF personalizado, puede eliminarlo con seguridad. Asegúrese de que su `secret_key` esté configurada para que los tokens sobrevivan a los reinicios del servidor.
* **Tamaño de subida de FileField:** `FileField.max_size` ahora tiene como valor predeterminado 50 MB en lugar de ilimitado. Pase `max_size=None` para restaurar el comportamiento anterior sin límites, o establezca un valor explícito para cambiar el límite.

### Eliminado sin reemplazo

* `AdminConfig` (consulte [Autenticación](#authentication)).
* `datatables_options`, `responsive_table` y `save_state` (consulte [Eliminación de DataTables](#datatables-removal)).
* El backend Odmantic (consulte [Requisitos](#requirements)).

## Cómo obtener ayuda

Si encuentra un problema de migración no cubierto en esta guía, por favor [abra un issue](https://github.com/jowilf/starlette-admin/issues). Incluya una reproducción mínima del problema e indique la versión desde la que está actualizando. Ejecutar con [`Admin(debug=True)`](user-guide/admin.md#debugging) suele revelar la causa directamente, y los logs resultantes constituyen un excelente complemento para su reporte.
