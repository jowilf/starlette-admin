---
title: Migración desde Flask-Admin
description: Una guía de migración directa de Flask-Admin a starlette-admin, que muestra
  cómo trasladar sus configuraciones de ModelView al ecosistema ASGI.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Migración desde Flask-Admin

starlette-admin comenzó como un port de los conceptos de Flask-Admin al ecosistema ASGI, por lo que la migración es directa. Usted sigue creando subclases de `ModelView`, las configura con atributos de clase y las registra en una instancia de `Admin`. La mayor parte del trabajo consiste en renombrar atributos y pasar del contexto de solicitud implícito de Flask al objeto `request` explícito de Starlette.

Esta guía mapea la API de Flask-Admin, atributo por atributo, a su equivalente en starlette-admin.

## Modelo mental

| Concepto de Flask-Admin | Equivalente en starlette-admin |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, luego `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; la instancia de `Admin` posee el engine y las sesiones de base de datos |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| backends de peewee / pymongo | Beanie, Tortoise ORM, SQLModel o un [backend personalizado](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Contexto de solicitud de Flask (`flask.request`) | Parámetro explícito `request: Request` en cada hook |
| Métodos síncronos | Métodos `async`; lo síncrono sigue funcionando donde se aceptan callables |

## Configuración

=== "Flask-Admin"

    ```python
    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    admin = Admin(app, name="My Admin", template_mode="bootstrap4")
    admin.add_view(ModelView(Post, db.session))
    ```

=== "starlette-admin"

    ```python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    app = Starlette()  # or FastAPI()
    admin = Admin(engine, title="My Admin", secret_key="change-me")
    admin.add_view(ModelView(Post))
    admin.mount_to(app)
    ```

No existe un interruptor `template_mode`. La interfaz usa [Tabler](https://tabler.io) (Bootstrap 5) e incluye modo oscuro. Para cambiar el aspecto, escriba un [`BaseTheme`](../advanced/custom-themes.md) personalizado o [sobrescriba las plantillas](../advanced/templates.md).

## Atributos de la página de lista

| Flask-Admin | starlette-admin | Notas |
| --- | --- | --- |
| `column_list` | `fields` | También controla las páginas de detalle y de formulario. Use los atributos `exclude_fields_from_*` para variaciones por página. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Por ejemplo, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Se aplica a la definición del campo. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#calcular-formatear-y-analizar-valores) en el campo | Por ejemplo, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / formateadores de exportación | El mismo diccionario `formatter=`, indexado por `RequestAction` | Un solo mapeo cubre el formato de lista, detalle y exportación. Las acciones sin entrada conservan el valor sin procesar. |
| `column_type_formatters` | `formatter=` por campo, o una subclase de campo personalizada | No existe un registro por tipo. Adjunte el formateador a cada campo, o [cree una subclase del campo](../advanced/custom-fields.md) y reutilícela. |
| Propiedades del modelo o callables en `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) o `getter=` en cualquier campo | Añade columnas virtuales, o redirige la búsqueda del valor de un campo existente, sin necesidad de una subclase. |
| Campos WTForms personalizados (coerción de valores) | [`parser=`](../user-guide/fields.md#calcular-formatear-y-analizar-valores) en el campo | Reemplaza el análisis predeterminado del formulario o de la importación del campo según `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#busqueda-y-ordenacion) |  |
| `column_filters` | `searchable_fields` combinado con `filters=` por campo | Reemplaza la lista plana de filtros por un [constructor visual](../user-guide/filters.md) que admite grupos anidados de `AND`/`OR`. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#busqueda-y-ordenacion) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#busqueda-y-ordenacion) | Por ejemplo, `[("created_at", True)]` ordena en orden descendente. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Los usuarios seleccionan una celda y la editan en su lugar. |
| `page_size` | [`page_size`](../user-guide/views.md#paginacion-y-controles-de-interfaz) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#paginacion-y-controles-de-interfaz) | El valor predeterminado es `[10, 25, 50, 100]`. Los usuarios eligen entre estas opciones. |
| `column_display_pk` | Incluya la clave primaria en `fields` |  |
| `column_details_list` | `fields` menos `exclude_fields_from_detail` | La página de detalle está integrada. No existe la opción `can_view_details`. |

## Atributos del formulario

| Flask-Admin | starlette-admin | Notas |
| --- | --- | --- |
| `form_columns` | `fields` menos `exclude_fields_from_create` y `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Controles de visibilidad separados por formulario. |
| `form_overrides` | Instancias de campo explícitas en `fields` | Por ejemplo, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Argumentos del constructor en el campo | Por ejemplo, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Por ejemplo, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Entradas adicionales en `fields` | Admite cualquier campo que no esté respaldado por una columna de base de datos, como un [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Atributos del campo | Establezca `read_only`, `disabled` o `placeholder` directamente en el campo. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Reemplaza las reglas planas por fieldsets, pestañas y cuadrículas responsivas. |
| `create_modal` / `edit_modal` | No disponible | Las vistas de creación y edición se muestran como páginas completas. |
| `on_form_prefill` | hook `before_edit` |  |

## Exportación e importación

=== "Flask-Admin"

    ```python
    class PostView(ModelView):
        can_export = True
        export_types = ["csv", "xlsx"]
        export_max_rows = 10000
    ```

=== "starlette-admin"

    ```python
    class PostView(ModelView):
        exporters = ["csv", "xlsx", "pdf"]
        importers = ["csv", "xlsx"]
        exclude_fields_from_export = ["internal_notes"]
    ```

La exportación en CSV y JSON está activada de forma predeterminada. Los límites de filas se aplican automáticamente, y el escape de fórmulas de hojas de cálculo es una opción configurable del exporter. La importación, que Flask-Admin no ofrece, incluye un paso de vista previa con validación por fila y actualizaciones opcionales de registros existentes por clave primaria. Consulte [Exportación e importación](../user-guide/export-import.md).

## Acciones

=== "Flask-Admin"

    ```python
    from flask_admin.actions import action


    class PostView(ModelView):
        @action("publish", "Publish", "Publish selected posts?")
        def action_publish(self, ids):
            query = Post.query.filter(Post.id.in_(ids))
            for post in query.all():
                post.published = True
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class PostView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Publish",
            confirmation="Publish selected posts?",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            for post in await selection.rows():
                post.published = True
            flash(request, "Posts published")
    ```

El handler recibe un objeto [`ActionSelection`](../user-guide/actions.md) en lugar de identificadores crudos. Resuelve las filas de forma diferida, expone los filtros activos y funciona de la misma manera cuando un usuario selecciona todos los registros coincidentes en varias páginas. Las acciones también pueden mostrar un formulario HTML personalizado dentro del diálogo de confirmación. Para operaciones por fila, [`@row_action` y `@link_row_action`](../user-guide/actions.md#acciones-de-fila) reemplazan los formateadores de columna personalizados.

## Permisos y control de acceso

Los indicadores de clase `can_*` de Flask-Admin se convierten en [métodos por solicitud](../user-guide/views.md#seguridad-y-autorizacion) en starlette-admin, de modo que las decisiones de autorización pueden depender del usuario autenticado.

| Flask-Admin | starlette-admin | Notas |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Oculta la vista del menú y bloquea el acceso directo. |
| `inaccessible_callback()` | Gestionado por el flujo de autenticación | Las solicitudes no autenticadas redirigen a la página de inicio de sesión. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` y `can_delete` siguen el mismo patrón. |
| `can_view_details` | `can_view_detail(request)` | La página de detalle existe de forma predeterminada. |
| `can_export` | `can_export(request)`, además de `can_import(request)` |  |
| Sin equivalente | `can_access_field(request, field)` | Controla la visibilidad de cada campo por usuario. |
| Sin equivalente | `is_action_allowed(request, name)` | Proporciona autorización por acción. |

Con Flask-Admin, usted integra Flask-Login por su cuenta. starlette-admin incluye un [`AuthProvider`](../user-guide/auth.md) con una página de inicio de sesión lista para usar, y usted implementa los métodos `login`, `logout` y `authenticate` contra su almacén de usuarios. Un `OAuthProvider` cubre los flujos de redirección OIDC. El usuario autenticado está disponible en todas partes como `request.state.admin_user`.

## Hooks del ciclo de vida del modelo

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#hooks-del-ciclo-de-vida) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, específicos del backend de SQLAlchemy |
| `handle_view_exception` | Lance `FormValidationError` o `ActionFailed` |

Más allá de los hooks por vista, el [sistema de eventos](../advanced/events.md) permite que un único handler observe todas las vistas. Flask-Admin no tiene equivalente.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Vistas personalizadas y la página de índice

| Flask-Admin | starlette-admin | Notas |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Componga páginas a partir de [widgets](../user-guide/custom-views.md) sin escribir plantillas crudas. |
| Renderizado de plantillas personalizadas | Subclase de `CustomView` | Le da control total sobre las rutas y las respuestas. |
| `AdminIndexView` | `Admin(index_view=...)` | Cree paneles de control con `StatWidget`, `ChartWidget`, `TableWidget` y widgets de diseño. |
| `MenuLink` | Vista [`Link`](../user-guide/views.md#link) | Por ejemplo, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Categorías en el menú | Vista [`DropDown`](../user-guide/views.md#organizacion-de-la-barra-lateral) | Agrupa vistas en la barra lateral. |
| `FileAdmin` | No disponible | Los campos de archivos e imágenes con [almacenamiento local o S3](../user-guide/file-storage.md) gestionan los adjuntos. No existe un explorador de archivos del servidor. |

## Modelos en línea

=== "Flask-Admin"

    ```python
    class ArticleView(ModelView):
        inline_models = [Comment]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import InlineModelView, ModelView


    class CommentInline(InlineModelView):
        model = Comment
        fields = ["author", "body"]


    class ArticleView(ModelView):
        inlines = [CommentInline]
    ```

Una clase explícita le da a cada modelo en línea toda la superficie de configuración de `ModelView`: selección de campos, validación y soporte de claves externas compuestas. Consulte [Formularios en línea](../user-guide/inline-forms.md).

## Internacionalización

Flask-Admin depende de Flask-Babel y del entorno de Flask circundante. starlette-admin usa un objeto de configuración en su lugar:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

El renderizado de fechas y horas conscientes de la zona horaria funciona de la misma manera, mediante `TimezoneConfig`. Consulte [Internacionalización y zonas horarias](../user-guide/i18n.md).

## Lo que gana al migrar

* **Una pila asíncrona.** Se ejecuta de forma nativa en FastAPI y Starlette, con soporte para SQLAlchemy asíncrono, Beanie y Tortoise ORM. Flask-Admin es síncrono.
* **Funciones de seguridad integradas.** La protección CSRF, la sanitización de nombres de archivo subidos, la verificación del contenido de imágenes y los límites de filas de exportación están activados tan pronto como usted instancia `Admin`, y puede habilitar el escape de fórmulas de hojas de cálculo en los exporters. Consulte [Seguridad](../user-guide/security.md).
* **Importación de datos.** Un paso de vista previa valida cada fila antes de escribir nada. Flask-Admin no tiene función de importación.
* **Un sistema de widgets para paneles de control.** Cree páginas de índice y vistas personalizadas en Python en lugar de escribir plantillas a mano.
* **Diseño moderno.** Una base de código mantenida activamente, con una interfaz pulida, modo oscuro integrado y type hints de primera clase.

## Lo que debe adaptar

* **Objetos de solicitud explícitos.** No hay contexto de solicitud implícito. Cada hook y método de permisos recibe el `request` como parámetro.
* **Handlers asíncronos.** Los hooks y las acciones son corrutinas, así que mantenga fuera de ellos las llamadas bloqueantes o traslade ese trabajo a un hilo.
* **Sin `FileAdmin`.** Si su flujo de trabajo depende de explorar el sistema de archivos del servidor, starlette-admin no lo cubre.
* **Sin modales de creación ni edición.** Los formularios se muestran como páginas completas en lugar de modales emergentes.
