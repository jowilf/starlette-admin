---
title: Configuración del panel de administración
description: Configure su instancia de starlette-admin, personalice el tema, el enrutamiento
  y los ajustes de seguridad generales.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Panel de administración

Usted pasa todos los ajustes a nivel de panel de administración como argumentos de palabra clave a la clase `Admin`: el título de la barra de navegación, la ubicación de montaje, la configuración de CSRF y autenticación, y el tema renderizado.

## Uso básico

Comience importando la clase `Admin` desde el paquete `contrib` que corresponda con su mapeador objeto-relacional (ORM):

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

A continuación se muestra una configuración mínima que usa SQLAlchemy:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` define el texto de la barra de navegación y la etiqueta HTML `<title>`.
* `base_url` define el prefijo de ruta donde se monta el panel de administración.
* `secret_key` firma las cookies de CSRF y de mensajes flash.
* `add_view` registra una vista, y `mount_to` construye las rutas y el middleware del panel de administración antes de montarlos en su aplicación.

Cada clase `Admin` acepta todas las opciones de configuración descritas a continuación, y algunas añaden comportamientos específicos del backend:

* `contrib.sqla.Admin(session_provider, ...)` recibe un `Engine`, `AsyncEngine`, `sessionmaker` o `async_sessionmaker` como primer argumento posicional e inserta `DBSessionMiddleware` por usted. `contrib.sqlmodel.Admin` es la misma clase, reexportada. Consulte [SQLAlchemy](../integrations/sqlalchemy.md) y [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` y `contrib.tortoise.Admin` no aceptan argumentos adicionales en el constructor, porque Beanie, MongoEngine y Tortoise ORM gestionan sus propias conexiones fuera del panel de administración. `mongoengine.Admin` también registra una ruta para servir archivos GridFS en `mount_to`. Consulte [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) y [Tortoise ORM](../integrations/tortoise.md).

## Referencia completa

El constructor de `Admin` acepta todos los parámetros siguientes como argumentos de palabra clave.

### Identidad e imagen de marca

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Texto de la barra de navegación y etiqueta `<title>`. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logotipo mostrado en la barra de navegación en lugar de `title`. Pase una URL simple, o un callable que la resuelva por cada solicitud, por ejemplo para una imagen de marca por inquilino. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logotipo mostrado en la página de inicio de sesión en lugar de `logo_url`. Usa `logo_url` como valor alternativo cuando no está definido. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Atributo href del `<link>` del favicon. |

`logo_url`, `login_logo_url` y `favicon_url` aceptan cada uno una cadena o un callable `(request) -> str | None`. Use un callable cuando la imagen de marca dependa de la solicitud, como en una aplicación multiinquilino o cuando sirva varios nombres de host:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Montaje

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | Prefijo de URL bajo el cual se monta el panel de administración. |
| `route_name` | `str` | `"admin"` | Nombre del montaje de Starlette. Cada enlace interno (`list`, `edit`, exportaciones, recursos estáticos) se genera llamando a `request.url_for(route_name + ":list", ...)`. |

Para ejecutar más de un `Admin` en la misma aplicación, asigne a cada instancia un `base_url` y un `route_name` distintos. De lo contrario, los enlaces generados por un panel pueden resolverse hacia otro. Consulte [Múltiples instancias de Admin](../advanced/multiple-admin.md).


### Plantillas, archivos estáticos y tema

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Directorio que se consulta en busca de plantillas sobrescritas antes de recurrir a las plantillas integradas. |
| `static_dir` | `str | None` | `None` | Directorio de archivos estáticos adicionales servidos junto con el CSS y el JS integrados. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Una subclase de tema que define las plantillas de diseño, el conjunto de iconos y los recursos estáticos. |

[Temas personalizados](../advanced/custom-themes.md) y [Plantillas](../advanced/templates.md) cubren estas opciones en detalle.

### La página de inicio

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (un `DefaultIndexView` creado a partir de sus vistas registradas) | La página renderizada en `base_url`. |

La página de inicio predeterminada es un banner de bienvenida más un panel por cada vista de modelo registrada, cada uno mostrando el número de registros. Para reemplazarla, pase su propio `CustomView`, típicamente una subclase de `DefaultIndexView` o cualquier `CustomView` con un widget. Consulte [Vistas personalizadas y widgets](custom-views.md).

### Autenticación, seguridad e integridad de los datos

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (el panel de administración es accesible públicamente) | Controla el acceso a cada ruta. Consulte [Autenticación](auth.md). |
| `secret_key` | `str | None` | `None` (se genera una clave aleatoria al iniciar, con un `UserWarning`) | Firma las cookies de CSRF y de mensajes flash. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Middleware adicional de Starlette, ejecutado además del middleware de CSRF, mensajes flash y autenticación que el panel añade por sí mismo. |
| `import_config` | `ImportConfig | None` | `None` (valores predeterminados de `ImportConfig()`) | Límites de tamaño de carga y de bombas ZIP para el endpoint de importación. |
| `export_config` | `ExportConfig | None` | `None` (valores predeterminados de `ExportConfig()`) | Límite de número de filas y de descarga de archivos desde URLs para el endpoint de exportación. |

La guía de [Seguridad](security.md) cubre estos cinco parámetros en profundidad.

### Región horaria e idioma

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (solo inglés, sin `LocaleMiddleware`) | Habilita las cadenas de interfaz traducidas. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (activado) | Convierte los valores de fecha y hora mostrados a la zona horaria del usuario. |

Para un recorrido completo, consulte [Internacionalización y zonas horarias](i18n.md).

### Depuración

| Parámetro | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Cuando es `True`, llama a `starlette_admin.logging.configure_logging()` antes del arranque, lo cual activa el registro en consola de nivel DEBUG con colores para el paquete `starlette_admin`. |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

El registro de depuración es útil durante el desarrollo. Cada solicitud registra el middleware que se ejecutó, la vista que resolvió la URL y el motivo por el que una comprobación de permisos pasó o falló.

!!! warning
    Mantenga `debug=False` en producción. El registro de nivel DEBUG es detallado y añade una sobrecarga significativa a cada solicitud.

Para un enfoque más ligero, llame usted mismo a `starlette_admin.logging.configure_logging(level=logging.INFO)` en lugar de pasar `debug=True`. Obtendrá el manejador sin toda la verbosidad de DEBUG.

## Registro de vistas y montaje

Después de crear la instancia de `Admin`, registre sus vistas y monte el panel de administración en su aplicación.

```python
admin.add_view(ModelView(Post))  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### Registro de vistas

Use `add_view` para añadir componentes a su panel de control. El método acepta tanto una instancia de vista como una clase de vista, y usted puede registrar vistas de modelo, páginas personalizadas, menús desplegables y enlaces externos.

### Montaje de la aplicación

Después de registrar todas sus vistas, llame a `mount_to(app)` exactamente una vez para adjuntar el panel de administración a su aplicación Starlette o FastAPI. Este paso finaliza la configuración de enrutamiento y seguridad.

!!! important "El orden de las operaciones importa"
    El montaje bloquea la configuración del panel de administración para que cada vista se enrute correctamente.

    * Acceder a `admin.app` antes del montaje genera un `RuntimeError`.
    * Registrar otra vista o llamar a `mount_to` de nuevo después del primer montaje también genera un `RuntimeError`.

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**Próximos pasos**

* **[Seguridad](security.md):** `secret_key`, CSRF y los límites de exportación e importación.
* **[Autenticación](auth.md):** Cómo conectar el `auth_provider`.
* **[Múltiples instancias de Admin](../advanced/multiple-admin.md):** Ejecutar más de un `Admin` en la misma aplicación.
