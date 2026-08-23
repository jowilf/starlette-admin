---
title: Comparación de starlette-admin, Django Admin y Flask-Admin
description: Una comparación lado a lado de starlette-admin, Django Admin y Flask-Admin
  que abarca stacks web, ORM compatibles, profundidad de funcionalidades y ventajas
  y desventajas.
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# Comparación de starlette-admin, Django Admin y Flask-Admin

Django Admin, Flask-Admin y starlette-admin resuelven el mismo problema: generan una interfaz de administración lista para producción a partir de sus modelos de datos, de modo que usted no tiene que escribir pantallas CRUD a mano. Se diferencian en los stacks web a los que se dirigen, los ORM que admiten y cuánto incluyen de forma integrada frente a lo que le dejan a usted.

Esta página compara los tres. Si ya conoce Django Admin o Flask-Admin y desea una traducción directa de la API, consulte la guía de migración correspondiente:

* [Migrar desde Django Admin](django-admin.md)
* [Migrar desde Flask-Admin](flask-admin.md)

## Posicionamiento de un vistazo

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Framework web** | Solo Django | Solo Flask | Starlette, FastAPI y cualquier aplicación ASGI que pueda montar sub-aplicaciones |
| **Modelo de ejecución** | Síncrono (WSGI primero) | Síncrono (WSGI) | Asíncrono primero (ASGI) |
| **Capa de datos** | Solo Django ORM | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM o un [backend personalizado](../integrations/custom-backend.md) |
| **Kit de herramientas de UI** | Plantillas de Django, tema clásico de administración | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), modo oscuro, [temas personalizados](../advanced/custom-themes.md) |
| **Incluido con el framework** | Sí, forma parte de Django | No, paquete separado | No, paquete separado |
| **Autenticación** | Integrada mediante `django.contrib.auth` | Tráigala usted mismo (`is_accessible`) | [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md) conectables, tráiga su propio almacén de usuarios |

## Cuándo encaja cada framework

### Django Admin

Django Admin encaja en aplicaciones nativas de Django. Es maduro y se integra con `django.contrib.auth`, por lo que obtiene usuarios, grupos, permisos por modelo e historial de cambios sin ninguna configuración. Solo funciona dentro de Django.

### Flask-Admin

Flask-Admin llevó la generación automática a Flask y popularizó el estilo de configuración `ModelView`. Es síncrono y está ligado a Flask, por lo que no funciona sobre un stack asíncrono.

### starlette-admin

starlette-admin se dirige al stack asíncrono de Python. Si su aplicación usa FastAPI o Starlette, monte la administración en su aplicación y esta se ejecutará en el mismo event loop. Funciona con capas de datos SQL y NoSQL, conserva el estilo de configuración `ModelView` de Flask-Admin y cubre la profundidad de funcionalidades que los usuarios de Django Admin esperan: inlines, acciones por lotes, permisos por solicitud e internacionalización.

## Matriz de funcionalidades

**Leyenda:**

* **Sí:** integrado
* **Parcial:** posible mediante paquetes de terceros o código personalizado
* **No:** no disponible

| Funcionalidad | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Vistas CRUD generadas automáticamente | **Sí** | **Sí** | **Sí** |
| Búsqueda de texto completo | **Sí** `search_fields` | **Sí** `column_searchable_list` | **Sí** [`searchable_fields`](../user-guide/filters.md) |
| Filtros por columna | **Sí** `list_filter` | **Sí** `column_filters` | **Sí** [Constructor visual de filtros](../user-guide/filters.md) con grupos `AND`/`OR` |
| Ordenamiento y orden predeterminado | **Sí** | **Sí** | **Sí** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#busqueda-y-ordenacion) |
| Edición en línea en la vista de lista | **Sí** `list_editable` | **Sí** `column_editable_list` | **Sí** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Formularios inline para modelos relacionados | **Sí** `TabularInline` / `StackedInline` | **Sí** `inline_models` | **Sí** [`InlineModelView`](../user-guide/inline-forms.md) |
| Acciones por lotes | **Sí** `actions` | **Sí** `@action` | **Sí** [`@action`](../user-guide/actions.md) con diálogos de confirmación y formularios personalizados |
| Acciones por fila | **Parcial** plantillas personalizadas | **Parcial** formateadores personalizados | **Sí** [`@row_action`, `@link_row_action`](../user-guide/actions.md#acciones-de-fila) |
| Exportación de datos | **Parcial** `django-import-export` | **Sí** CSV y otros | **Sí** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Importación de datos | **Parcial** `django-import-export` | **No** | **Sí** [CSV, JSON, Excel](../user-guide/export-import.md) con validación previa y upsert |
| Carga de archivos e imágenes | **Sí** `FileField` / `ImageField` | **Parcial** requiere configuración adicional | **Sí** [Almacenamiento local y S3](../user-guide/file-storage.md) |
| Widgets del panel de control | **Parcial** temas de terceros | **Parcial** vista de índice personalizada | **Sí** [Sistema de widgets integrado](../user-guide/custom-views.md) |
| Páginas independientes personalizadas | **Sí** URLs personalizadas de `AdminSite` | **Sí** `BaseView` + `@expose` | **Sí** [`CustomView`](../user-guide/custom-views.md) |
| Control del diseño del formulario | **Sí** `fieldsets` | **Sí** `form_rules` | **Sí** [`form_layout`](../advanced/form-layout.md) con pestañas y cuadrículas |
| Autenticación | **Sí** `django.contrib.auth` | **No** tráigala usted mismo | **Sí** [`AuthProvider`](../user-guide/auth.md) u `OAuthProvider` |
| Permisos por modelo | **Sí** framework de permisos | **Sí** sobrescribir indicadores `can_*` | **Sí** [métodos por solicitud](../user-guide/views.md#seguridad-y-autorizacion) |
| Permisos por campo | **Parcial** `get_readonly_fields` | **No** | **Sí** [`can_access_field`](../user-guide/views.md#seguridad-y-autorizacion) |
| Hooks de ciclo de vida | **Sí** `save_model`, signals | **Sí** `on_model_change` | **Sí** [Hooks de ciclo de vida](../user-guide/views.md#hooks-del-ciclo-de-vida) y [eventos](../advanced/events.md) |
| Protección CSRF | **Sí** middleware de Django | **Sí** mediante Flask-WTF | **Sí** [Integrado en `Admin`](../user-guide/security.md) |
| Historial de cambios / registro de auditoría | **Sí** `LogEntry` | **No** | **Parcial** construya el suyo propio con [eventos](../advanced/events.md) |
| Internacionalización | **Sí** | **Sí** mediante Flask-Babel | **Sí** [`I18nConfig`](../user-guide/i18n.md) |
| Múltiples instancias de administración | **Sí** múltiples `AdminSite`s | **Sí** | **Sí** [Montajes múltiples de `Admin`](../advanced/multiple-admin.md) |
| Soporte de ORM asíncrono | **Parcial** | **No** | **Sí** SQLAlchemy asíncrono, Beanie, Tortoise ORM |

## Ventajas y desventajas

* **Sistema de usuarios completo:** Django Admin incluye un sistema de usuarios completo. `django.contrib.auth` gestiona usuarios, grupos, permisos y contraseñas por usted. En starlette-admin, usted implementa `authenticate()` contra su propio almacén de datos, lo que implica más configuración al principio y más libertad arquitectónica después.
* **Historial de cambios automatizado:** Django Admin registra el historial de cambios en `LogEntry`. En starlette-admin, usted construye la pista de auditoría usted mismo suscribiéndose a los [eventos](../advanced/events.md) del ciclo de vida. Requiere unas pocas líneas de código, pero no es automático.
* **Ecosistema de terceros:** Django Admin cuenta con un gran ecosistema de paquetes de terceros para temas, widgets y flujos de trabajo de datos. starlette-admin cubre muchas de esas funcionalidades de forma nativa, pero es posible que una extensión específica de la que dependa aún no exista.
* **Gestión de archivos:** Flask-Admin incluye `FileAdmin`, un explorador del sistema de archivos del servidor. starlette-admin gestiona los archivos adjuntos a los campos del modelo mediante [disco local o S3](../user-guide/file-storage.md), y no dispone de un explorador de archivos del servidor de propósito general.

## Próximos pasos

* ¿Migra desde Django? Lea [Migrar desde Django Admin](django-admin.md).
* ¿Migra desde Flask-Admin? Lea [Migrar desde Flask-Admin](flask-admin.md).
* ¿Comienza desde cero? La [Guía de inicio rápido](../getting-started/quickstart.md) le proporciona una interfaz de administración funcional en minutos.
