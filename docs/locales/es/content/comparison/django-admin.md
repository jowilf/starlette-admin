---
title: Migración desde Django Admin
description: Una guía completa de migración que relaciona los conceptos de Django
  Admin con sus equivalentes en starlette-admin para construir interfaces administrativas
  declarativas.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Migración desde Django Admin

Si conoce Django Admin, starlette-admin le resultará familiar. Ambos generan una interfaz de administración a partir de una configuración declarativa por modelo, y ambos admiten edición en línea, acciones por lotes y permisos por solicitud.

Las diferencias son estructurales. starlette-admin se ejecuta sobre cualquier aplicación ASGI en lugar de requerir Django, funciona con varios ORM y le permite integrar su propia autenticación en lugar de imponer un modelo de usuario integrado.

Esta guía relaciona cada concepto principal de `ModelAdmin` con su equivalente en starlette-admin, con código lado a lado.

## Modelo mental

| Concepto de Django Admin | Equivalente en starlette-admin |
| --- | --- |
| `AdminSite` | Instancia de [`Admin`](../api/admin.md) montada en su aplicación |
| `ModelAdmin` | Subclase de [`ModelView`](../user-guide/views.md) |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` en `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie o Tortoise ORM mediante `starlette_admin.contrib.*` |
| `__str__` en el modelo | `__admin_repr__(self, request)`, que es asíncrono y tiene en cuenta la solicitud |
| Campos de formulario inferidos de los campos del modelo | [Campos](../user-guide/fields.md) inferidos por el convertidor del backend, personalizables campo por campo |

## Registrar un modelo

=== "Django Admin"

    ```python
    from django.contrib import admin
    from .models import Post


    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import Admin, ModelView


    class PostView(ModelView):
        fields = ["id", "title", "content", "published", "created_at"]
        exclude_fields_from_list = ["content"]
        searchable_fields = ["title", "content"]


    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)  # app is your FastAPI or Starlette instance
    ```

Destacan dos diferencias estructurales:

1. **Una sola lista de campos controla todas las páginas.** `fields` es la única fuente de verdad. Después, utilice [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` y `exclude_fields_from_edit`](../user-guide/views.md#seleccion-y-personalizacion-de-campos) para las variaciones por página.
2. **La instancia de `Admin` posee el motor de base de datos.** No necesita pasar una sesión a cada vista.

## Opciones de la página de lista

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `list_display` | `fields` menos [`exclude_fields_from_list`](../user-guide/views.md#seleccion-y-personalizacion-de-campos) | Una sola lista de campos controla todas las páginas. |
| `list_display` con un callable o `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield), o `getter=` en cualquier campo | Por ejemplo, `ComputedField("full_name", getter=lambda request, obj: ...)`. Utilice `getter=` en un campo con tipo, como un campo de fecha o de imagen, para conservar el renderizado de ese tipo. |
| Reformatear una columna real para mostrarla | [`formatter=`](../user-guide/fields.md#calcular-formatear-y-analizar-valores) en el campo | Un `dict[RequestAction, callable]`, de modo que la lista, el detalle y la exportación pueden formatear de forma distinta. Django necesita un callable además de `admin_order_field` para mantener el ordenamiento; aquí la columna sigue siendo ordenable. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#busqueda-y-ordenacion) | Alimenta tanto la búsqueda de texto completo como el creador de filtros. |
| `list_filter` | `searchable_fields` combinado con `filters=` por campo | Los usuarios obtienen un creador visual con grupos `AND`/`OR` anidados en lugar de una barra lateral fija. Consulte [Filtros](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#busqueda-y-ordenacion) | Por ejemplo, `fields_default_sort = [("created_at", True)]` ordena en sentido descendente. |
| `admin_order_field` / capacidad de ordenamiento | [`sortable_fields`](../user-guide/views.md#busqueda-y-ordenacion) | Todos los campos son ordenables de forma predeterminada. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Los usuarios seleccionan una celda y la editan in situ. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#paginacion-y-controles-de-interfaz) | Controla los límites de paginación. |
| `date_hierarchy` | Filtros de fecha, como `between` e `in the past` | No existe una barra de exploración jerárquica dedicada; el creador de filtros cubre este caso. |
| `empty_value_display` | Una entrada `formatter=`, o `null_template` | Los formateadores reciben valores `None`, por lo que pueden sustituirlos por un marcador de posición. `null_template` reemplaza el marcado renderizado. |

## Formularios

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Controla la visibilidad de los campos del formulario. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Componga libremente con `FieldsetWidget`, `TabsWidget`, `GridWidget` y `RowWidget`. |
| `readonly_fields` | `read_only=True` en el campo | También puede excluir el campo de las vistas de creación y edición. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | Mismo comportamiento de slugificación en vivo. |
| `autocomplete_fields`, `raw_id_fields` | Comportamiento predeterminado de [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-y-hasmany) | Los widgets de relación son entradas Select2 con búsqueda del lado del servidor de forma predeterminada. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-y-hasmany) | Se representa como un componente de selección múltiple con búsqueda. |
| `formfield_overrides` | Entradas explícitas en la lista `fields` | Reemplace directamente el campo detectado automáticamente: `fields = ["id", TextAreaField("bio")]` |
| Validación personalizada de formularios | `validators=` en el campo o `FormValidationError` en los hooks | Consulte [Validadores](../api/validators.md). |
| `to_python()` del campo del formulario / coerción personalizada | [`parser=`](../user-guide/fields.md#calcular-formatear-y-analizar-valores) en el campo | Sustituye el análisis predeterminado del formulario o de la importación del campo según `RequestAction`. |
| Texto de ayuda del campo del modelo | `help_text=` | Disponible en cualquier definición de campo. |

### Ejemplo de fieldsets

=== "Django Admin"

    ```python
    class PostAdmin(admin.ModelAdmin):
        fieldsets = [
            ("Content", {"fields": ["title", "body"]}),
            ("Publication", {"fields": ["published", "created_at"]}),
        ]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import FieldsetWidget


    class PostView(ModelView):
        fields = ["id", "title", "body", "published", "created_at"]
        form_layout = [
            FieldsetWidget(legend="Content", children=["title", "body"]),
            FieldsetWidget(legend="Publication", children=["published", "created_at"]),
        ]
    ```

`form_layout` va más allá de los fieldsets: puede crear pestañas, cuadrículas responsivas y diseños anidados. Consulte [Diseño del formulario](../advanced/form-layout.md).

## Inlines

=== "Django Admin"

    ```python
    class CommentInline(admin.TabularInline):
        model = Comment
        extra = 1


    class ArticleAdmin(admin.ModelAdmin):
        inlines = [CommentInline]
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

starlette-admin detecta la clave externa cuando no es ambigua, y admite claves externas compuestas. Consulte [Formularios en línea](../user-guide/inline-forms.md) para configuraciones avanzadas.

## Acciones

=== "Django Admin"

    ```python
    @admin.action(description="Mark selected articles as published")
    def make_published(modeladmin, request, queryset):
        queryset.update(published=True)


    class ArticleAdmin(admin.ModelAdmin):
        actions = [make_published]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class ArticleView(ModelView):
        actions = ["make_published", "delete"]

        @action(
            name="make_published",
            text="Mark selected articles as published",
            confirmation="Publish the selected articles?",
        )
        async def make_published(
            self, request: Request, selection: ActionSelection
        ) -> None:
            for article in await selection.rows():
                article.published = True
            flash(request, "Articles published")
    ```

Donde Django Admin pasa un `QuerySet`, el manejador de starlette-admin recibe un objeto [`ActionSelection`](../user-guide/actions.md). Este objeto resuelve filas, claves primarias y filtros activos de manera diferida, y se comporta igual cuando un usuario selecciona todos los registros coincidentes.

Las acciones también pueden representar un formulario HTML personalizado dentro del diálogo de confirmación, lo que en Django Admin implica construir una página intermedia. Para operaciones por fila, utilice [`@row_action` y `@link_row_action`](../user-guide/actions.md#acciones-de-fila), que no tienen equivalente en Django Admin.

## Permisos y autenticación

Django Admin delega en `django.contrib.auth`. starlette-admin divide el problema en dos: un [`AuthProvider`](../user-guide/auth.md) responde «quién es este usuario», y los [métodos por vista](../user-guide/views.md#seguridad-y-autorizacion) responden «qué puede hacer».

| Django Admin | starlette-admin |
| --- | --- |
| Inicio de sesión de `django.contrib.auth` | `AuthProvider` (página de inicio de sesión integrada) o `OAuthProvider` (flujo de redirección OIDC) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` en la vista |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` por usuario | `can_access_field(request, field)` |
| Sin equivalente | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

La siguiente vista restringe la eliminación a los usuarios con el rol `admin`:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Cada método `can_*` recibe la solicitud, de modo que sus decisiones de autorización pueden leer el usuario actual, los encabezados HTTP o cualquier otro dato de la solicitud.

## Hooks de guardado y señales

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#hooks-del-ciclo-de-vida) en la vista | Nativo asíncrono, y recibe los datos del formulario analizados junto con la instancia del modelo. |
| `delete_model` | `before_delete` | Gestiona la lógica previa a la eliminación. |
| `post_save` y otras señales | [Eventos](../advanced/events.md) | Por ejemplo, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` difunde a todas las vistas. |
| Historial de cambios de `LogEntry` | Constrúyalo con el sistema de eventos | Suscríbase a `AFTER_CREATE`, `AFTER_EDIT` y `AFTER_DELETE` para llenar su propia tabla de auditoría. |
| `messages.success(request, ...)` | `flash(request, ...)` | Consulte [Mensajes flash](../user-guide/flash-messages.md). |

## Configuración global del sitio

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Logotipo personalizado mediante una sobrescritura de plantilla | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` con [widgets](../user-guide/custom-views.md) para un panel de control completo |
| Sobrescrituras de plantillas en `templates/admin/` | `Admin(templates_dir="...")`; consulte [Plantillas](../advanced/templates.md) |
| Varias instancias de `AdminSite` | Varias instancias de `Admin` montadas en diferentes rutas de la aplicación |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` o `get_detail_query` para el backend de SQLAlchemy |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`; consulte [i18n y zonas horarias](../user-guide/i18n.md) |

## Lo que gana al migrar

* **Asíncrono de extremo a extremo:** Los manejadores, los hooks del ciclo de vida y las devoluciones de llamada de los widgets pueden ser corrutinas que se ejecutan en su bucle de eventos existente, junto a sus endpoints de FastAPI.
* **Flexibilidad de base de datos:** La misma configuración de administración aplica tanto si utiliza SQLAlchemy, SQLModel, MongoDB mediante MongoEngine o Beanie, como Tortoise ORM.
* **Exportación e importación integradas:** CSV, JSON y PDF, además de Excel y otros formatos mediante `tablib`. Exporte registros directamente o importe datos masivos mediante un asistente que muestra primero una vista previa, aplica validación a nivel de fila y admite upserts opcionales de clave primaria. Consulte [Exportación e importación](../user-guide/export-import.md).
* **Widgets de panel de control:** Las tarjetas de estadísticas, ApexCharts y las cuadrículas de diseño se combinan en páginas de índice y vistas personalizadas, de modo que no necesita un paquete de temas externo para crear un panel de control. Consulte [Vistas personalizadas y widgets](../user-guide/custom-views.md).
* **Interfaz de usuario moderna:** Tabler (Bootstrap 5) le ofrece modo oscuro, alternadores de visibilidad de columnas y resaltado de búsqueda de forma predeterminada.

## Lo que debe implementar por su cuenta

* **Autenticación:** No hay un modelo de usuario ni una base de datos de permisos incluidos. Implemente `AuthProvider.authenticate()` contra el almacén de datos que su aplicación ya utiliza.
* **Registro de auditoría:** starlette-admin no genera una tabla `LogEntry`. Conecte el [sistema de eventos](../advanced/events.md) a su propia tabla de auditoría.
* **Configuración de interfaz a nivel de modelo:** Las comodidades de Django como `choices` y `verbose_name` a nivel de modelo, y los validadores, no se transfieren. En su lugar, declárelos en el campo de starlette-admin, con `EnumField`, `label=` y `validators=`.
