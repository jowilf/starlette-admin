---
title: Plantillas
description: Sobrescriba las plantillas de Jinja2 en starlette-admin para personalizar
  por completo la estructura HTML de vistas o campos específicos.
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# Plantillas

Cada página del panel de administración es una plantilla de Jinja2 que usted puede sobrescribir. Cambie una sola página de lista, la celda de tabla de un campo o un widget del panel de control sin bifurcar el árbol de plantillas integradas.

## Cómo funciona el cargador de plantillas

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` construye un `ChoiceLoader` de Jinja2 que consulta primero su `templates_dir` y en segundo lugar el directorio del paquete integrado `starlette_admin/templates/`. Coloque un archivo bajo `my_templates/` en la misma ruta relativa que tiene dentro de `starlette_admin/templates/` y su archivo ocultará al integrado. Todas las demás plantillas siguen renderizándose desde el directorio integrado.

!!! note
    La cadena de cargadores también registra un `PrefixLoader` bajo la clave `@starlette-admin` que siempre resuelve a las plantillas integradas, independientemente de lo que las esté ocultando en `templates_dir`. Acceda a ellas con el formato de ruta `@starlette-admin/<name>.html`, omitiendo la barra final en el propio prefijo. Consulte [Sobrescribir la plantilla de una sola página](#sobrescribir-la-plantilla-de-una-sola-pagina) más abajo para saber para qué sirve esto.

## Mapa del directorio de plantillas

| Ruta | Se renderiza para |
| --- | --- |
| `base.html` | Estructura HTML externa (`<html>`, `<head>`, scripts) |
| `layout.html` | Elementos fijos de la barra lateral y la barra superior (extiende `base.html`) |
| `index.html` | Panel de control o página de inicio |
| `list.html` | Página de lista del modelo (tabla, barra de filtros, paginación) |
| `detail.html` | Vista de detalle (solo lectura) de un registro |
| `create.html` | Formulario de creación |
| `edit.html` | Formulario de edición |
| `login.html` | Página de inicio de sesión |
| `error.html` | Página de error HTTP (403, 404, etc.) |
| `actions.html` | Modal de acciones por lotes |
| `row-actions.html` | Menú desplegable de acciones de fila |
| `inline.html` | Conjunto de formularios en línea en la página de creación/edición |
| `inline_detail.html` | Tabla en línea en la página de detalle |
| `inline_row.html` | Fila individual dentro de un conjunto de formularios en línea |
| `_filter_bar.html` | Barra de chips de filtros activos sobre la lista |
| `_filter_builder.html` | Modal del constructor de filtros |
| `_pagination.html` | Controles de paginación |
| `_column_header.html` | Celda de encabezado de columna ordenable |
| `_form_footer.html` | Botones Guardar, Guardar y continuar o Añadir otro |
| `_form_group.html` | Fieldset de un grupo de [diseño de formulario](form-layout.md) en el formulario de creación/edición |
| `_form_group_fields.html` | Los campos de entrada renderizados dentro de un grupo de diseño de formulario |
| `fields/list/<type>.html` | Celda de columna de lista para un tipo de campo |
| `fields/detail/<type>.html` | Visualización en la página de detalle para un tipo de campo |
| `fields/form/<type>.html` | Widget de entrada de formulario para un tipo de campo |
| `widgets/<name>.html` | Plantilla de widget del panel de control |
| `modals/actions.html` | Modal de confirmación de acción |
| `modals/delete.html` | Modal de confirmación de eliminación |
| `modals/error.html` | Modal de error |
| `modals/import.html` | Modal de importación |
| `macros/views.html` | Macros de Jinja2 compartidas usadas en varias páginas |

!!! note
    El árbol integrado también incluye `modals/loading.html`, un modal genérico de estado de carga, y varias plantillas específicas de campos en `fields/list/`, `fields/detail/` y `fields/form/`. Compruebe los nombres de archivo exactos en `starlette_admin/templates/` para la versión que haya instalado antes de sobrescribir un archivo genérico `<type>.html`.

## Sobrescribir la plantilla de una sola página

```
my_templates/
└── list.html   ← oculta la list.html integrada

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Banner personalizado sobre la lista.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` resolvería de nuevo a su propio `my_templates/list.html`, porque `templates_dir` se consulta primero, y esa referencia circular provoca un error de recursión infinita. El prefijo `@starlette-admin/` apunta siempre a la copia integrada, de modo que cada `extends` e `include` dentro de una sobrescritura debe usarlo en lugar del nombre de archivo a secas.

## Bloques sobrescribibles

Cada página integrada extiende `layout.html`, que a su vez extiende `base.html`. Sobrescriba un único `{% block %}` en lugar de un archivo completo para cambiar un fragmento sin duplicar el resto de la página:

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Informe personalizado</a>
{% endblock %}

```

### `base.html`

| Bloque | Contenido |
| --- | --- |
| `favicon` | La etiqueta `<link>` del favicon |
| `title` | La etiqueta `<title>` |
| `head_meta` | Las etiquetas `<meta>` dentro del elemento `<head>` |
| `head_css` | Etiquetas `<link>` de hojas de estilo |
| `head` | Un punto de inserción de formato libre dentro del elemento `<head>` |
| `body` | Todo el contenido de `<body>` (este bloque es sobrescrito por `layout.html`) |
| `modal` | Un punto de inserción a nivel de página para modals |
| `script` | Las etiquetas `<script>` situadas justo antes de la etiqueta de cierre `</body>` |
| `tail` | Un punto de inserción vacío al final de `<body>`, después de `script` |

### `layout.html`

| Bloque | Contenido |
| --- | --- |
| `sidebar` | Todo el elemento `<aside>` de la barra lateral (incluye la marca de navegación, el menú y el pie) |
| `brand` | La imagen del logotipo (o el valor alternativo de `app_title`) dentro del enlace de marca de la barra lateral |
| `sidebar_menu` | La lista de enlaces de vistas dentro de la barra lateral |
| `sidebar_footer` | La zona inferior de la barra lateral |
| `user_menu_trigger` | El avatar y el nombre de usuario mostrados en el botón del menú de usuario. Se define una vez y se reutiliza tanto en la barra lateral móvil como en la barra de navegación de escritorio mediante `self.user_menu_trigger()`, de modo que sobrescribirlo actualiza ambos |
| `user_menu_items` | Los elementos del menú desplegable situados en el menú de usuario |
| `navbar` | La barra de navegación superior |
| `navbar_extra` | Contenido adicional colocado en la barra de navegación junto al menú de usuario |
| `header` | La zona de encabezado de la página posicionada sobre `content` (incluye el título y las rutas de navegación) |
| `flash_messages` | La zona designada para renderizar mensajes flash |
| `content_before` | Un punto de inserción inmediatamente anterior a `content` |
| `content` | El contenido principal de la página (es el bloque que rellenan `list.html`, `detail.html`, etc.) |
| `content_after` | Un punto de inserción inmediatamente posterior a `content` |
| `page_footer` | La zona de pie situada bajo el contenido de la página |

### `list.html`

| Bloque | Contenido |
| --- | --- |
| `header` | El encabezado de la página (incluye el título y las rutas de navegación) |
| `page_title` | El encabezado `<h1>` dentro del encabezado de página |
| `breadcrumbs` | La ruta de navegación dentro del encabezado |
| `modal` | Los modals de eliminación, acción e importación |
| `content` | El cuerpo completo de la página de lista |
| `list_search` | La zona del campo de búsqueda |
| `list_toolbar` | La fila de herramientas que contiene los botones de filtros, exportación, importación y creación |
| `list_toolbar_extra` | Un punto de inserción adicional al final de la barra de herramientas |
| `list_before_table` | Un punto de inserción anterior a la tabla |
| `list_table` | El propio elemento `<table>` |
| `list_header` | La fila `<thead>` que contiene la casilla de verificación y las celdas de encabezado de columna |
| `list_row` | Una única `<tr>` en la tabla de resultados (bloque con ámbito; tiene acceso a `row`, `row_pk` y `row_clickable`) |
| `list_row_actions_before` | La celda de acciones de fila cuando `row_actions_position` es `BEFORE_COLUMNS` (bloque con ámbito) |
| `list_row_actions_after` | La celda de acciones de fila cuando `row_actions_position` es `AFTER_COLUMNS` (bloque con ámbito) |
| `list_empty` | El marcador de posición «No data» (bloque con ámbito renderizado para estados vacíos) |
| `list_after_table` | Un punto de inserción posterior a la tabla |
| `list_footer` | El pie de paginación y de rango |
| `head_css` | Adiciones de hojas de estilo específicas de la página |
| `script` | Adiciones de scripts específicos de la página |

### `detail.html`

| Bloque | Contenido |
| --- | --- |
| `header` | El encabezado de la página (incluye el título, las rutas de navegación y las acciones) |
| `page_title` | El encabezado `<h1>` dentro del encabezado de página |
| `breadcrumbs` | La ruta de navegación dentro del encabezado |
| `modal` | Los modals de eliminación y acción |
| `content` | El cuerpo completo de la página de detalle |
| `detail_before` | Un punto de inserción anterior a la tarjeta de detalle |
| `detail_title` | La zona de título dentro de la tarjeta de detalle |
| `detail_actions` | Los botones de acción dentro de la tarjeta de detalle |
| `details_table` | La tabla principal de campos y valores |
| `detail_after` | Un punto de inserción posterior a la tarjeta de detalle |
| `head_css` | Adiciones de hojas de estilo específicas de la página |
| `script` | Adiciones de scripts específicos de la página |

### `create.html` / `edit.html`

| Bloque | Contenido |
| --- | --- |
| `header` | El encabezado de la página (incluye el título y las rutas de navegación) |
| `page_title` | El encabezado `<h1>` dentro del encabezado de página |
| `breadcrumbs` | La ruta de navegación dentro del encabezado |
| `content` | El cuerpo completo de la página del formulario |
| `form_before` | Un punto de inserción anterior a la tarjeta del formulario |
| `create_card_header` / `edit_card_header` | La zona de encabezado dentro de la tarjeta del formulario |
| `create_form` / `edit_form` | Los grupos del [diseño de formulario](form-layout.md) (cada uno renderizado mediante `_form_group.html`) y sus elementos de entrada de campo |
| `create_inlines` / `edit_inlines` | La zona del conjunto de formularios en línea |
| `form_footer` | Los botones Guardar, Guardar y continuar y Añadir otro |
| `form_after` | Un punto de inserción posterior a la tarjeta del formulario |
| `head_css` | Adiciones de hojas de estilo específicas de la página |
| `script` | Adiciones de scripts específicos de la página |

### `login.html`

| Bloque | Contenido |
| --- | --- |
| `header` / `sidebar` | Dejados vacíos (la página de inicio de sesión oculta los elementos fijos estándar de la aplicación) |
| `content` | El cuerpo completo de la página de inicio de sesión |
| `login_logo` | El logotipo mostrado sobre el formulario de inicio de sesión |
| `login_title` | El texto del título de la página de inicio de sesión |
| `login_form_before` | Un punto de inserción anterior a los campos del formulario |
| `login_fields` | Los campos de entrada de nombre de usuario y contraseña |
| `login_form_footer` | Un punto de inserción después de los campos pero dentro del formulario |
| `login_card_footer` | Un punto de inserción situado directamente debajo de la tarjeta de inicio de sesión |
| `script` | Adiciones de scripts específicos de la página |

### `index.html`

| Bloque | Contenido |
| --- | --- |
| `head_css` | Adiciones de hojas de estilo específicas del widget |
| `content` | La cuadrícula de widgets del panel de control |
| `script` | Adiciones de scripts específicos del widget |

### `error.html`

| Bloque | Contenido |
| --- | --- |
| `header` / `sidebar` | Dejados vacíos (la página de error oculta los elementos fijos estándar de la aplicación) |
| `content` | El mensaje de error y las acciones asociadas |
| `error_actions` | Botones de acción mostrados bajo el mensaje de error (como un botón «Volver») |

!!! tip
    Llame a `{{ super() }}` dentro de una sobrescritura para conservar el contenido del bloque integrado y añadir a él en lugar de reemplazarlo. El ejemplo de `list_toolbar_extra` anterior lo hace, y las plantillas integradas `index.html` y `create.html` usan el mismo patrón para el bloque `head_css`.

### Ejemplo: reemplazar el logotipo de la barra lateral por un SVG en línea

Pasar una URL a `Admin(logo_url=...)` es la forma más rápida de establecer un logotipo y cubre la mayoría de los casos, incluidos los archivos `.svg` externos. Sin embargo, la plantilla integrada renderiza esa URL dentro de una etiqueta `<img>`, por lo que el SVG no puede heredar propiedades CSS de la página que lo rodea.

Sobrescriba el bloque `brand` con **marcado `<svg>` en línea** cuando necesite que el logotipo responda al resto de la interfaz.

#### Implementación

Cree un archivo `layout.html` en su directorio de plantillas. Todas las páginas del panel de administración heredan de `layout.html`, por lo que esta única sobrescritura se aplica a todo el sitio.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "Conserve la clase navbar-logo"
    Deje la clase CSS `navbar-logo` en su elemento `<svg>` personalizado. Proporciona a su gráfico en línea la alineación, el relleno y el dimensionamiento del framework sin necesidad de escribir CSS propio.

## Sobrescribir plantillas de campos

Cada contexto de campo usa tres subdirectorios:

| Directorio | Se usa en |
| --- | --- |
| `fields/list/<type>.html` | Celda de la tabla de lista (compacta, solo lectura) |
| `fields/detail/<type>.html` | Visualización en la página de detalle (completa, solo lectura) |
| `fields/form/<type>.html` | Entrada de los formularios de creación y edición |

Puede sobrescribir la celda de lista de los campos de texto sin tocar el formulario ni la visualización de detalle:

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Para apuntar una **instancia de campo** concreta a su plantilla en lugar de sobrescribir el tipo en todas partes, establezca `list_template`, `detail_template`, `form_template`, `null_template` o `empty_template` en el propio campo:

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (con el valor predeterminado `"fields/detail/_null.html"`) y `empty_template` (con el valor predeterminado `"fields/detail/_empty.html"`) son ranuras independientes. Las páginas de lista y de detalle los renderizan en lugar de `list_template` o `detail_template` siempre que el valor del campo sea `None` o una lista o tupla vacía:

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Sobrescribir plantillas de widgets

Los widgets siguen el mismo patrón de sobrescritura. Coloque sus archivos bajo el directorio `widgets/`:

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Variables de plantilla globales

Estas variables están disponibles en todas las plantillas sin necesidad de pasarlas. `Admin` las instala como globals de Jinja2 una sola vez durante la configuración:

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `views` | `list[BaseView]` | Todas las vistas registradas (se usa para renderizar la barra lateral) |
| `app_title` | `str` | El título del panel de administración (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True` si hay un proveedor de autenticación configurado |
| `__name__` | `str` | El prefijo de nombre de ruta del panel de administración (p. ej., `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL de un recurso estático integrado. El argumento `v` añade un parámetro de consulta `?v=` para invalidar la caché. |
| `logo_url` | `callable` | `logo_url(request)` → URL del logotipo de la barra lateral, o `None` si no está establecido |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL del logotipo de la página de inicio de sesión, o `None` si no está establecido |
| `favicon_url` | `callable` | `favicon_url(request)` → URL del favicon, o `None` si no está establecido |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL con `overrides` fusionados en su cadena de consulta (se usa para enlaces de orden, paginación o búsqueda). Pase `None` para eliminar una clave. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL de la página de detalle de un registro |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL de la página de edición de un registro |
| `export_url` | `callable` | `export_url(request, key, fmt)` → URL de descarga de la exportación que transporta el estado de filtro/orden/búsqueda de la página de lista actual |
| `import_url` | `callable` | `import_url(request, key)` → URL POST de importación |
| `get_locale` | `callable` | `get_locale()` → Cadena de la configuración regional activa (no requiere argumento `request`) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Nombre legible de una cadena de configuración regional |
| `i18n_config` | `I18nConfig` | El objeto de configuración i18n del panel de administración |
| `get_timezone` | `callable` | `get_timezone()` → Cadena de la zona horaria activa (no requiere argumento `request`) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Nombre legible de una cadena de zona horaria |
| `timezone_config` | `TimezoneConfig | None` | La configuración de zona horaria del panel de administración |
| `theme_settings` | `TablerSettings` | Configuración activa del tema Tabler (base, primary, radius, mode) expuesta por `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Renderiza el `<input>` oculto de CSRF |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone` y `get_timezone_display_name` no reciben ningún parámetro `request`. Leen la configuración regional y la zona horaria de `contextvars` que `LocaleMiddleware` rellena durante la solicitud, en lugar de hacerlo del objeto `Request`.

## Variables de contexto por página

Además de las variables globales anteriores, cada página pasa su propio diccionario de contexto a `TemplateResponse`.

### `list.html`

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `view` | `BaseModelView` | La vista actual |
| `title` | `str` | Título de la página |
| `fields` | `list[BaseField]` | Columnas visibles actualmente |
| `all_fields` | `list[BaseField]` | Todos los campos de lista (incluidos los ocultos) |
| `rows` | `list[dict]` | Datos de filas serializados |
| `total` | `int` | Total de registros coincidentes para la paginación |
| `total_pages` | `int` | Número total de páginas |
| `range_start` | `int` | Número del primer registro de esta página (basado en 1) |
| `range_end` | `int` | Número del último registro de esta página |
| `list_params` | `ListParams` | Estado de la URL analizado (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Se evalúa como `"and"` u `"or"` para el grupo de filtros activo de nivel superior |
| `filter_chips` | `list` | Descriptores de los chips de filtros activos |
| `filter_builder_fields` | `list` | Campos disponibles en la interfaz del constructor de filtros |
| `raw_filter` | `str | None` | Cadena de filtro JSON sin procesar procedente de la URL |
| `_actions` | `list` | Acciones por lotes disponibles |
| `row_actions` | `dict[Any, list]` | Acciones de fila disponibles por registro, indexadas por clave primaria |

### `detail.html`

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `view` | `BaseModelView` | La vista actual |
| `title` | `str` | Título de la página |
| `obj` | `dict` | Registro serializado |
| `raw_obj` | `Any` | El objeto del modelo sin procesar antes de la serialización |
| `inlines` | `list[dict]` | Contexto en línea (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Acciones de fila disponibles |

### `create.html` / `edit.html`

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `view` | `BaseModelView` | La vista actual |
| `title` | `str` | Título de la página |
| `obj` | `dict` | Valores de campo actuales (valores predeterminados en creación, valores existentes en edición) |
| `raw_obj` | `Any` | Objeto del modelo sin procesar (solo en edición, ausente en creación) |
| `errors` | `dict[str, list[str]]` | Errores de validación indexados por nombre de campo (solo presentes tras un envío fallido) |
| `inlines` | `list[dict]` | Contexto del conjunto de formularios en línea |

## Añadir sus propios globals y filtros

Para añadir sus propias variables y funciones a las plantillas, cree una subclase de `Admin` y sobrescriba `__init__`. Llame primero a `super().__init__()`, de modo que `self.templates` exista antes de añadirle contenido:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## Filtros de Jinja2 integrados

Cada instancia del panel de administración registra estos filtros durante `_setup_templates`:

| Filtro | Firma | Descripción |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | Devuelve `True` si el recurso es una `CustomView` |
| `is_link` | `view | is_link` | Devuelve `True` si el recurso es un `Link` |
| `is_model_view` | `view | is_model_view` | Devuelve `True` si el recurso es una `BaseModelView` |
| `is_dropdown` | `view | is_dropdown` | Devuelve `True` si el recurso es un `DropDown` |
| `tojson` | `value | tojson` | Serialización JSON segura para HTML (reemplaza el `tojson` predeterminado de Jinja2) |
| `file_icon` | `mime_type | file_icon` | Devuelve una clase de icono completa para un tipo MIME (p. ej., `application/pdf` → `fa-solid fa-fw fa-file-pdf`); sobrescriba `self.templates.env.filters["file_icon"]` para usar su propio conjunto de iconos |
| `to_view` | `key | to_view` | Busca una `BaseModelView` registrada por su cadena de clave; lanza una `HTTPException` 404 si no se encuentra |
| `is_iter` | `value | is_iter` | Devuelve `True` si el valor es una `list` o una `tuple` |
| `is_str` | `value | is_str` | Devuelve `True` si el valor es una `str` |
| `is_dict` | `value | is_dict` | Devuelve `True` si el valor es un `dict` |
| `ra` | `value | ra` | Convierte una cadena en un miembro del enum `RequestAction` |
| `safe_url` | `url | safe_url` | Devuelve la URL solo si supera la comprobación de URL segura; en caso contrario, devuelve `""` |
| `sanitize_html` | `html | sanitize_html` | Elimina las etiquetas no permitidas de una cadena HTML y devuelve un `Markup` |

---

## Qué sigue

* **[Diseños de formulario](form-layout.md):** Divida los formularios de creación y edición en grupos con título y opcionalmente plegables, y sobrescriba `_form_group.html` para cambiar su marcado.
* **[Temas personalizados](custom-themes.md):** Restyle el panel de administración sin tocar plantillas individuales.
* **[Campos personalizados](custom-fields.md):** Combine la clase Python de un campo con su propio `list_template` o `form_template`.
* **[Puntos de extensión](extension-points.md):** La lista completa de superficies conectables más allá de las plantillas.
