---
title: Migración desde Django Admin
description: Una guía de migración completa que mapea los conceptos de Django Admin
  a sus equivalentes en starlette-admin para construir interfaces administrativas
  declarativas.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Migración desde Django Admin

Si usted conoce Django Admin, starlette-admin le resultará familiar. Ambos generan una interfaz de administración a partir de una configuración declarativa por modelo, y ambos admiten edición en línea, acciones por lotes y permisos por petición.

Las diferencias son estructurales. starlette-admin se ejecuta sobre cualquier aplicación ASGI en lugar de requerir Django, funciona con varios ORM y le permite incorporar su propia autenticación en lugar de imponer un modelo de usuario integrado.

Esta guía mapea cada concepto principal de `ModelAdmin` a su equivalente en starlette-admin, con código lado a lado.

## Modelo mental

| Concepto de Django Admin | Equivalente en starlette-admin |
| --- | --- |
| `AdminSite` | Instancia de [`Admin`](../api/admin.md) montada en su aplicación |
| `ModelAdmin` | Subclase de [`ModelView`](../user-guide/views.md) |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` en `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie o Tortoise ORM a través de `starlette_admin.contrib.*` |
| `__str__` en el modelo | `__admin_repr__(self, request)`, que es asíncrono y consciente de la petición |
| Campos de formulario inferidos de los campos del modelo | [Fields](../user-guide/fields.md) inferidos por el conversor del backend, personalizables campo por campo |

## Registro de un modelo

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

Dos diferencias estructurales destacan:

1. **Una sola lista de campos controla todas las páginas.** `fields` es la única fuente de verdad. Después, usted utiliza [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` y `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) para las variaciones por página.
2. **La instancia de `Admin` es propietaria del motor de base de datos.** Usted no pasa una sesión a cada vista.

## Opciones de la página de lista

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `list_display` | `fields` menos [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | Una única lista de campos controla todas las páginas. |
| `list_display` con un callable o `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield), o `getter=` en cualquier campo | Por ejemplo, `ComputedField("full_name", getter=lambda request, obj: ...)`. Utilice `getter=` en un campo con tipo, como un campo de fecha o imagen, para conservar el renderizado de ese tipo. |
| Reformatear una columna real para mostrarla | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) en el campo | Un `dict[RequestAction, callable]`, de modo que list, detail y export pueden formatear de manera distinta. Django necesita un callable más `admin_order_field` para mantener el ordenamiento; aquí la columna sigue siendo ordenable. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Alimenta tanto la búsqueda de texto completo como el constructor de filtros. |
| `list_filter` | `searchable_fields` combinado con `filters=` por campo | Los usuarios obtienen un constructor visual con grupos anidados de `AND`/`OR` en lugar de una barra lateral fija. Consulte [Filters](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Por ejemplo, `fields_default_sort = [("created_at", True)]` ordena en orden descendente. |
| `admin_order_field` / ordenabilidad | [`sortable_fields`](../user-guide/views.md#search-and-sort) | Todos los campos son ordenables por defecto. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Los usuarios seleccionan una celda y la editan in situ. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Controla los límites de paginación. |
| `date_hierarchy` | Filtros de fecha, como `between` e `in the past` | No existe una barra dedicada de exploración jerárquica; el constructor de filtros cubre este caso. |
| `empty_value_display` | Una entrada `formatter=`, o `null_template` | Los formatters reciben valores `None`, por lo que pueden sustituirlos por un marcador de posición. `null_template` reemplaza el markup renderizado. |

## Formularios

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Controla la visibilidad de los campos del formulario. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Componga libremente con `FieldsetWidget`, `TabsWidget`, `GridWidget` y `RowWidget`. |
| `readonly_fields` | `read_only=True` en el campo | También puede excluir el campo de las vistas create y edit. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | El mismo comportamiento de slugificación en vivo. |
| `autocomplete_fields`, `raw_id_fields` | Comportamiento predeterminado de [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) | Los widgets de relación son entradas Select2 con búsqueda del lado del servidor desde el primer momento. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Se renderiza como un componente multi-selección con búsqueda. |
| `formfield_overrides` | Entradas explícitas en la lista `fields` | Reemplace directamente el campo detectado automáticamente: `fields = ["id", TextAreaField("bio")]` |
| Validación personalizada de formularios | `validators=` en el campo o `FormValidationError` en hooks | Consulte [Validators](../api/validators.md). |
| `to_python()` del campo del formulario / coerción personalizada | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) en el campo | Reemplaza el análisis predeterminado del formulario o de la importación por `RequestAction`. |
| Texto de ayuda del formulario del modelo | `help_text=` | Disponible en cualquier definición de campo. |

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

`form_layout` va más allá de los fieldsets: puede construir pestañas, cuadrículas responsivas y diseños anidados. Consulte [Form Layout](../advanced/form-layout.md).

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

starlette-admin detecta la clave foránea cuando no es ambigua, y admite claves foráneas compuestas. Consulte [Inline Forms](../user-guide/inline-forms.md) para configuraciones avanzadas.

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

Donde Django Admin pasa un `QuerySet`, el handler de starlette-admin recibe un objeto [`ActionSelection`](../user-guide/actions.md). Este resuelve filas, claves primarias y filtros activos de forma perezosa, y se comporta de la misma manera cuando el usuario selecciona todos los registros coincidentes.

Las acciones también pueden renderizar un formulario HTML personalizado dentro del diálogo de confirmación, lo que en Django Admin implica construir una página intermedia. Para operaciones por fila, utilice [`@row_action` y `@link_row_action`](../user-guide/actions.md#row-actions), que no tienen equivalente en Django Admin.

## Permisos y autenticación

Django Admin delega en `django.contrib.auth`. starlette-admin divide el problema en dos: un [`AuthProvider`](../user-guide/auth.md) responde "quién es este usuario", y los [métodos por vista](../user-guide/views.md#security-and-authorization) responden "qué puede hacer".

| Django Admin | starlette-admin |
| --- | --- |
| Login de `django.contrib.auth` | `AuthProvider` (página de inicio de sesión integrada) u `OAuthProvider` (flujo de redirección OIDC) |
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

Cada método `can_*` recibe la petición, de modo que sus decisiones de autorización pueden leer el usuario actual, las cabeceras HTTP o cualquier otro dato de la petición.

## Hooks de guardado y señales

| Django Admin | starlette-admin | Notas |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) en la vista | Asíncrono de forma nativa, y recibe los datos del formulario analizados junto con la instancia del modelo. |
| `delete_model` | `before_delete` | Gestiona la lógica previa a la eliminación. |
| `post_save` y otras señales | [Events](../advanced/events.md) | Por ejemplo, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` difunde a todas las vistas. |
| Historial de cambios de `LogEntry` | Constrúyalo con el sistema de eventos | Suscríbase a `AFTER_CREATE`, `AFTER_EDIT` y `AFTER_DELETE` para llenar su propia tabla de auditoría. |
| `messages.success(request, ...)` | `flash(request, ...)` | Consulte [Flash Messages](../user-guide/flash-messages.md). |

## Configuración global del sitio

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Logotipo personalizado mediante una sobrescritura de plantilla | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` con [widgets](../user-guide/custom-views.md) para un dashboard enriquecido |
| Sobrescrituras de plantillas en `templates/admin/` | `Admin(templates_dir="...")`, consulte [Templates](../advanced/templates.md) |
| Múltiples instancias de `AdminSite` | Múltiples instancias de `Admin` montadas en diferentes rutas de la aplicación |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` o `get_detail_query` para el backend de SQLAlchemy |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, consulte [i18n and Timezones](../user-guide/i18n.md) |

## Lo que gana al migrar

* **Asíncrono de extremo a extremo:** Los handlers, los lifecycle hooks y los callbacks de widgets pueden ser todos coroutines que se ejecutan en su event loop existente, junto a sus endpoints de FastAPI.
* **Flexibilidad de base de datos:** La misma configuración de administración aplica tanto si utiliza SQLAlchemy, SQLModel, MongoDB mediante MongoEngine o Beanie, como Tortoise ORM.
* **Exportación e importación integradas:** CSV, JSON y PDF, además de Excel y otros formatos a través de `tablib`. Exporte registros directamente, o importe datos masivos mediante un asistente con vista previa que aplica validación a nivel de fila y admite upserts opcionales de clave primaria. Consulte [Export and Import](../user-guide/export-import.md).
* **Widgets de dashboard:** Tarjetas de estadísticas, ApexCharts y cuadrículas de diseño se componen en páginas index y custom views, de modo que no necesita un paquete de temas externo para construir un dashboard. Consulte [Custom Views and Widgets](../user-guide/custom-views.md).
* **Interfaz de usuario moderna:** Tabler (Bootstrap 5) le ofrece modo oscuro, interruptores de visibilidad de columnas y resaltado de búsquedas por defecto.

## Lo que debe aportar usted

* **Autenticación:** No hay ningún modelo de usuario ni base de datos de permisos incluidos. Implemente `AuthProvider.authenticate()` contra el almacén de datos que su aplicación ya utiliza.
* **Registro de auditoría:** starlette-admin no genera una tabla `LogEntry`. Conecte el [sistema de eventos](../advanced/events.md) a su propia tabla de auditoría.
* **Configuración de UI a nivel de modelo:** Las comodidades de Django como `choices`, `verbose_name` y validators a nivel de modelo no se transfieren. Declárelos en el campo de starlette-admin en su lugar, con `EnumField`, `label=` y `validators=`.
