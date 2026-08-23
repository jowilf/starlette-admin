---
title: Autenticación
description: Implemente la autenticación en starlette-admin mediante AuthProvider
  o intégrelo con OAuth para proteger su panel de control.
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# Autenticación

Usted protege la interfaz de administración implementando un único método:

```python
async def authenticate(request) -> AdminUser | None
```

Cada solicitud protegida del panel de administración pasa por este método. Cuando devuelve un `AdminUser`, la solicitud queda autenticada. Cuando devuelve `None`, la solicitud no está autenticada y entra en acción el flujo de inicio de sesión u OAuth que usted haya configurado.

En caso de éxito, el `AdminUser` devuelto se almacena en:

```python
request.state.admin_user
```

En caso de fallo, la solicitud se marca como anónima:

```python
request.state.is_anonymous = True
```

Las rutas públicas y parcialmente protegidas pueden entonces distinguir entre solicitudes autenticadas y no autenticadas sin iniciar un flujo de inicio de sesión.


## Elegir un proveedor de autenticación

| Proveedor | Cuándo usarlo | Qué debe implementar |
| --- | --- | --- |
| `AuthProvider` | Si desea la página de inicio de sesión integrada y usted mismo verifica las credenciales. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | Si desea un flujo de redirección OAuth2 u OIDC, como Auth0, Okta o Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Ambos heredan de `BaseAuthProvider` y comparten el mismo contrato. `authenticate()` se ejecuta en cada solicitud. Lo que devuelve se convierte en `request.state.admin_user`, y cuando devuelve `None`, el framework establece `request.state.is_anonymous = True`.

## `AuthProvider`: página de inicio de sesión integrada

Use este proveedor cuando desee que el framework genere y gestione el formulario de inicio de sesión mientras usted verifica las credenciales. El framework se encarga de la plantilla, del manejo de la solicitud POST y de la redirección.

Este es un ejemplo completo:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin

SECRET = "change-me-in-production"

# Demo user store: replace with a real lookup against your database
USERS = {"admin": {"name": "Administrator", "password": "password"}}


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return AdminUser(username=user["name"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


engine = create_engine("sqlite:///admin.sqlite")
app = Starlette(middleware=[Middleware(SessionMiddleware, secret_key=SECRET)])
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key=SECRET
)
admin.mount_to(app)
```

### Métodos obligatorios

Un `AuthProvider` implementa tres métodos. `SessionMiddleware` es obligatorio en este caso, porque mantiene el estado de sesión iniciada del usuario entre solicitudes.

#### `login()`

Este método procesa el envío del formulario. Recibe el `username`, la `password`, un booleano `remember_me` y la `request` actual.

* **En caso de éxito:** escriba un identificador, como el ID o el nombre del usuario, en `request.session`. Después, devuelva `None` para que el framework redirija a `next` o al índice del panel de administración, o devuelva una `Response` para redirigir a otro lugar.
* **En caso de fallo:** lance `LoginFailed("message")` para mostrar un error sobre el formulario, o lance `FormValidationError({"username": "..."})` para marcar un campo específico como no válido.

#### `authenticate()`

Este método se ejecuta en *cada* solicitud dirigida a una ruta protegida del panel de administración. Recibe el objeto `request`.

* Lea el identificador que guardó en `request.session` durante `login()`.
* Busque el usuario en su base de datos.
* Devuelva una instancia de `AdminUser` cuando el usuario exista y sea válido.
* Devuelva `None` cuando el usuario no exista o no haya iniciado sesión.

#### `logout()`

Este método procesa el cierre de sesión. Recibe el objeto `request`, y usted borra los datos del usuario de `request.session` para revocar el acceso. Devuelva `None` para la redirección predeterminada al índice del panel de administración, o devuelva una `Response` para redirigir a otro lugar.

## `OAuthProvider`: flujo de redirección OAuth2/OIDC


Use `OAuthProvider` cuando delegue la autenticación en un proveedor de identidad externo como Auth0, Okta, Google o Microsoft Entra ID.

`AuthProvider` gestiona un formulario de nombre de usuario y contraseña dentro del panel de administración. `OAuthProvider`, en cambio, utiliza un flujo basado en redirección:

1. Redirija al usuario al proveedor de identidad.
2. El proveedor autentica al usuario.
3. El proveedor redirige de vuelta a su aplicación.
4. Su aplicación intercambia la devolución de llamada por la identidad del usuario.
5. `authenticate()` restaura al usuario desde la sesión.

### Configuración de la URL de devolución de llamada (obligatoria)

Antes de implementar `OAuthProvider`, registre la URL de devolución de llamada de su aplicación en el panel de control de su proveedor de identidad. Por seguridad, los proveedores de OAuth solo redirigen a URL previamente aprobadas.

#### Ejemplo de URL de devolución de llamada

```text
https://your-domain.com/admin/oauth/callback
```

#### Desarrollo local

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Su URL de devolución de llamada exacta depende de su configuración. Se construye a partir del `route_name` que usted usa al montar `Admin`, más el `callback_path` del proveedor.

    La configuración predeterminada usa:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    lo que produce esta URL de devolución de llamada:

    ```text
    /admin/oauth/callback
    ```

    Una vez desplegada, se convierte en:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    Si cambia el prefijo de montaje o la ruta de devolución de llamada del proveedor, la URL cambia con ellos y usted debe actualizarla en la configuración de su proveedor de OAuth.

### Métodos obligatorios

Un `OAuthProvider` usa el mismo patrón basado en sesión que `AuthProvider`, pero divide el inicio de sesión en una redirección y una devolución de llamada.

#### `redirect_to_provider()`

Este método inicia el flujo de OAuth. Recibe la `request` y una `callback_url` generada, y debe devolver una `Response` que redirija el navegador del usuario a su proveedor de identidad.

#### `handle_callback()`

Este método se ejecuta cuando el navegador regresa del proveedor con un código de autorización. Recibe la `request`. Intercambie el código por un token de acceso, obtenga el perfil del usuario y almacene su identidad en `request.session`.

#### `authenticate()`

Al igual que con `AuthProvider`, este método lee lo que `handle_callback()` haya almacenado en la sesión. Devuelva un `AdminUser` cuando la sesión contenga datos de usuario válidos, o `None` cuando no los contenga.

#### `logout()`

Borre los datos de la sesión. Para cerrar también la sesión del usuario en el proveedor de identidad (cierre de sesión iniciado por el RP en OIDC), sobrescriba este método y devuelva una `Response` de redirección que apunte al endpoint de cierre de sesión del proveedor en lugar de devolver `None`.

Este es un ejemplo completo:

```python
import os

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin.auth import AdminUser, OAuthProvider

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)


class Auth0Provider(OAuthProvider):
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        client = oauth.create_client("auth0")
        return await client.authorize_redirect(request, callback_url)

    async def handle_callback(self, request: Request) -> None:
        client = oauth.create_client("auth0")
        token = await client.authorize_access_token(request)
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            return AdminUser(username=user["name"], photo_url=user.get("picture"))
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()
        client = oauth.create_client("auth0")
        metadata = await client.load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = str(
                URL(end_session_endpoint).include_query_params(
                    post_logout_redirect_uri="https://www.google.com/",
                    client_id=AUTH0_CLIENT_ID,
                )
            )
            return RedirectResponse(logout_url, status_code=HTTP_303_SEE_OTHER)
        return None


SECRET_KEY = "change-me"
engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
# required because Auth0Provider's handle_callback/authenticate methods use request.session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = Admin(
    engine, title="My Admin", auth_provider=Auth0Provider(), secret_key=SECRET_KEY
)
admin.mount_to(app)
```

## Registrar el proveedor

Después de implementar un proveedor de autenticación, adjúntelo a la instancia de `Admin`.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

Esa única línea es toda la integración. `Admin` monta el `AuthMiddleware` del proveedor delante de cada ruta del panel de administración y añade las rutas del proveedor (inicio de sesión, cierre de sesión y la devolución de llamada para `OAuthProvider`) dentro del prefijo del panel de administración.

## Comprobaciones de permisos

La autenticación responde a la pregunta «¿Quién es esta persona?». Los permisos responden a la pregunta «¿Qué puede hacer?». Los permisos pertenecen a la vista. El acceso basado en roles consta de tres pasos:

1. Herede de `AdminUser`, una dataclass sencilla, para añadir una lista `roles`.
2. Devuelva esa subclase desde el método `authenticate()` de su proveedor, rellenada a partir de su almacén de usuarios.
3. Lea `request.state.admin_user.roles` en los hooks de permisos de la vista.

```python
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette_admin import action, row_action
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField
from starlette_admin.types import RequestAction

# Demo user store: replace with a real lookup against your database
USERS = {
    "admin": {
        "name": "Administrator",
        "password": "password",
        "roles": ["read", "create", "edit", "delete", "read_body", "publish"],
    },
    "editor": {
        "name": "Editor",
        "password": "password",
        "roles": ["read", "create", "edit", "read_body", "publish"],
    },
    "viewer": {"name": "Viewer", "password": "password", "roles": ["read"]},
}


# Step 1: AdminUser is a plain dataclass, so subclassing it to add `roles` is
# the intended pattern rather than a workaround.
@dataclass
class MyAdminUser(AdminUser):
    roles: list[str] = field(default_factory=list)


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    # Step 2: authenticate() looks up the roles for the signed-in user and
    # returns them on a MyAdminUser instead of a plain AdminUser.
    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return MyAdminUser(username=user["name"], roles=user["roles"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# Step 3: Every hook below reads request.state.admin_user.roles, which is
# populated only because authenticate() returned a MyAdminUser.
class ArticleView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return "read" in request.state.admin_user.roles  # Hides the view entirely

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.admin_user.roles

    def can_access_field(
        self, request: Request, field: BaseField, action: RequestAction | None = None
    ) -> bool:
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field, action)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "publish":
            return "publish" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)
```

Registre `MyAuthProvider` como cualquier otro proveedor, con `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. Cada hook anterior tiene entonces acceso a `request.state.admin_user.roles`.

`is_accessible()`, disponible en cada `BaseView`, oculta la vista completa, incluida su entrada en la barra lateral. `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import` y `can_view_detail` controlan las operaciones individuales en una `ModelView`. `can_access_field` oculta campos específicos, e `is_action_allowed` e `is_row_action_allowed` restringen las acciones por lotes y las acciones de fila. Cuando una acción de fila depende del registro en lugar del usuario, por ejemplo para ocultar `publish` en un artículo ya publicado, sobrescriba en su lugar `is_row_action_allowed_for_obj(request, name, obj)`. Este método recibe el objeto subyacente de la fila y recurre a `is_row_action_allowed` como alternativa.

Para la referencia completa de la API, consulte [Views](views.md) y [Actions](actions.md). Una versión funcional completa con `can_export`, `can_import` y una acción de fila se encuentra en [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Algunas rutas permanecen públicas incluso en un panel de administración bloqueado, como un formulario de autorregistro o una comprobación de estado. Decore el endpoint y `AuthMiddleware` dejará pasar la solicitud sin comprobar un resultado válido de `authenticate()`:

```python
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import CustomView, route
from starlette_admin.auth import login_not_required


class AccountsView(CustomView):
    menu_label = "Accounts"
    path = "/accounts"

    @route("/register", methods=["GET", "POST"], name="register")
    @login_not_required
    async def register(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                request=request, name="register.html", context={}
            )
        form = await request.form()
        # Create the user account before granting access to the panel
        await create_user(email=form["email"], password=form["password"])
        return RedirectResponse(request.url_for("admin:login"), status_code=302)
```

Tanto `@route` como `@login_not_required` etiquetan la función con un atributo y la devuelven sin cambios, por lo que el orden en que los apile no importa.

## `allow_routes`

`allow_routes` le ofrece la misma exención a nivel de nombre de ruta en lugar de a nivel de función. Úselo cuando no sea propietario de la definición del endpoint, o cuando desee tener la lista de exenciones en un solo lugar:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

La cadena es el nombre de la ruta: ya sea el nombre del método, o el valor que usted pasó al parámetro `name=` en `@route`, como `name="register"` en el ejemplo anterior. `AuthMiddleware` siempre permite `"login"` y `"static"`, además de las rutas personalizadas que usted indique.

## `AdminUser`

Todo lo que `authenticate()` devuelva rellena `request.state.admin_user`. La barra superior lee dos campos de este:

| Atributo | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (traducible) | El nombre que se muestra en el menú de usuario de la barra superior. |
| `photo_url` | `str | None` | `None` | La URL de la imagen de avatar. Muestra un icono de marcador de posición cuando no se establece. |

`AdminUser` es una `@dataclass` sencilla, por lo que heredar de ella para incluir roles, un ID de inquilino o cualquier otra cosa que sus hooks de permisos necesiten es el patrón previsto. El ejemplo de `MyAdminUser` anterior lo muestra en la práctica.

---

**¿Qué sigue?**

* [Security](security.md): CSRF, claves secretas y lo que el framework protege automáticamente.
* [Views](views.md): `can_create`, `can_edit`, `can_delete` y la lista completa de hooks de permisos.
* [Actions](actions.md): `is_action_allowed` e `is_row_action_allowed` para las acciones por lotes y las acciones de fila.
