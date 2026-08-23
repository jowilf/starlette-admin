---
title: Múltiples instancias de administración
description: Monte múltiples paneles de control de administración aislados en una
  sola aplicación FastAPI para diferentes roles de usuario o dominios.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Múltiples instancias de administración

Cada instancia de `Admin` que construya es una subaplicación Starlette autocontenida. Monte tantas como necesite, cada una con su propio `base_url`, `route_name`, proveedor de autenticación y vistas.

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Order, Post, User

engine = create_engine("sqlite:///app.sqlite")
app = Starlette()

STAFF = {"staff": "staffpass"}
SUPERADMINS = {"root": "rootpass"}


class StaffAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if STAFF.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in STAFF else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


class SuperAdminAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if SUPERADMINS.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in SUPERADMINS else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


staff_admin = Admin(
    engine,
    title="Staff Admin",
    base_url="/staff",
    route_name="staff_admin",
    auth_provider=StaffAuth(),
    secret_key="staff-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="staff-secret-change-me")],
)
staff_admin.add_view(ModelView(Order))
staff_admin.add_view(ModelView(Post))
staff_admin.mount_to(app)

root_admin = Admin(
    engine,
    title="Super Admin",
    base_url="/root",
    route_name="root_admin",
    auth_provider=SuperAdminAuth(),
    secret_key="root-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="root-secret-change-me")],
)
root_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(User))
root_admin.mount_to(app)

```

En este ejemplo, `/staff` muestra una página de inicio de sesión respaldada por `StaffAuth`, y `/root` muestra otra distinta respaldada por `SuperAdminAuth`. Iniciar sesión en uno no otorga acceso al otro: cada `SessionMiddleware` firma su cookie con su propia `secret_key`, por lo que cada instancia de `Admin` solo lee los datos de sesión que escribió su propio proveedor de autenticación.

## `base_url` y `route_name`

`base_url` y `route_name` son parámetros del constructor de las clases `Admin` y `BaseAdmin` en `starlette_admin/base.py`. Sus valores predeterminados son `/admin` y `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** establece el prefijo de ruta donde se monta el panel de administración. Se pasa directamente a la llamada interna `app.mount(self.base_url, app=admin_app, name=self.route_name)`, por lo que debe ser único para cada instancia; de lo contrario, un montaje oculta al otro.
* **`route_name`** es el nombre bajo el cual Starlette registra el montaje. Cada URL que genera la administración, ya sea para listas, detalles, ediciones, exportaciones y recursos estáticos, proviene de `request.url_for(route_name + ":list", ...)`, y cada plantilla de página lee `request.app.state.ROUTE_NAME` para obtener el prefijo correcto al construir enlaces.

`mount_to` construye una subaplicación Starlette nueva para cada instancia de administración, de modo que el middleware, las rutas y las variables globales de las plantillas permanecen aisladas. `Admin` no es un singleton a nivel de proceso: construya tantas instancias independientes como necesite su aplicación.

!!! warning
    Asigne a cada `Admin` un `route_name` distinto. El router de Starlette resuelve `url_for("admin:list", ...)` haciendo coincidir el **nombre** del montaje, de modo que dos administraciones que compartan un mismo `route_name` dejan la aplicación padre con dos montajes bajo el mismo nombre, y `url_for` resuelve al que Starlette encuentre primero. En consecuencia, cada enlace interno de la segunda administración, incluidos los enlaces de edición, los recursos estáticos y los endpoints de exportación, apunta silenciosamente al `base_url` de la primera.

## Compartir vistas frente a definir vistas separadas

`add_view` recibe una instancia de vista y la muta durante la configuración. Para una `BaseModelView`, esa configuración vincula callbacks internos a la administración con la que se registra, incluyendo la forma en que los campos `HasOne` y `HasMany` resuelven los enlaces a registros relacionados.

Si registra la misma **instancia** de vista en dos administraciones, la segunda llamada a `add_view` sobrescribe esos callbacks, por lo que los enlaces de relación en las páginas de la primera administración se resuelven contra las vistas y URLs de la segunda.

Para evitarlo, asigne a cada administración una instancia nueva de la **clase** `ModelView`. La clase no contiene estado específico de la administración; solo lo contienen las instancias:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

Cuando ambas administraciones necesitan comportamientos diferentes, como reglas de visibilidad distintas o permisos `can_delete`, escriba una subclase para cada una en lugar de modificar una instancia compartida en tiempo de ejecución:

```python
class StaffOrderView(ModelView):
    fields_default_sort = ["-created_at"]

    def can_delete(self, request: Request) -> bool:
        return False


class RootOrderView(ModelView):
    fields_default_sort = ["-created_at"]


staff_admin.add_view(StaffOrderView(Order))
root_admin.add_view(RootOrderView(Order))

```

---

## ¿Qué sigue?

* **[Autenticación](../user-guide/auth.md):** el contrato completo de `AuthProvider` y `OAuthProvider`.
* **[Puntos de extensión](extension-points.md):** todas las demás superficies conectables disponibles en la clase `Admin`.
* **[Inicio rápido](../getting-started/quickstart.md):** la configuración fundamental de una sola administración sobre la cual se basa esta guía.
