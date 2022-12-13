# Autorización de autenticación

De forma predeterminada, *Starlette Admin* no impone ninguna autenticación a su aplicación, pero proporciona una [AuthProvider][starlette_admin.auth.AuthProvider] opcional que puede usar.

## Autenticación

Para habilitar la autenticación en su interfaz de administración, herede la clase [AuthProvider][starlette_admin.auth.AuthProvider] y configure `auth_provider` al declarar su aplicación de administración

La clase [AuthProvider][starlette_admin.auth.AuthProvider] tiene tres métodos que debe anular:

* [is_authenticated][starlette_admin.auth.AuthProvider.is_authenticated]: se llamará para validar cada solicitud entrante.
* [login][starlette_admin.auth.AuthProvider.login]: se llamará en la página de inicio de sesión para validar el nombre de usuario/contraseña.
* [logout][starlette_admin.auth.AuthProvider.logout]: se llamará para el cierre de sesión

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import BaseAdmin as Admin
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

users = {
    "admin": ["admin"],
    "john": ["post:list", "post:detail"],
    "terry": ["post:list", "post:create", "post:edit"],
    "doe": [""],
}


class MyAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )
        if username in users and password == "password":
            response.set_cookie(key="session", value=username)
            return response
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if "session" in request.cookies:
            user_roles = users.get(request.cookies.get("session"), None)
            if user_roles is not None:
                """Save user roles in request state, can be use later,
                to restrict user actions in admin interface"""
                request.state.user_roles = user_roles
                return True
        return False

    async def logout(self, request: Request, response: Response):
        response.delete_cookie("session")
        return response


admin = Admin(auth_provider=MyAuthProvider())

```

??? Nota
    Consulte [aplicación de demostración](https://github.com/jowilf/starlette-admin-demo) para ver un ejemplo completo con starlette SessionMiddleware

## Autorización

### Para todas las vistas

Cada [view][starlette_admin.views.BaseView] implementa el método [is_accessible][starlette_admin.views.BaseView.is_accessible] que se puede usar para restringir el acceso al usuario actual.

```python
from starlette_admin import CustomView
from starlette.requests import Request

class ReportView(CustomView):

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
```
!!! importante
    Cuando la vista es inaccesible, no aparece en la estructura del menú

### Para [ModelView][starlette_admin.views.BaseModelView]
En [ModelView][starlette_admin.views.BaseModelView], hay cuatro métodos adicionales que puede anular
para restringir el acceso al usuario actual.

* `can_view_details`: Permiso para ver los detalles completos de los items
* `can_create`: Permiso para crear nuevos elementos
* `can_edit`: Permiso para editar elementos
* `can_delete`: Permiso para eliminar elementos

```python
from starlette_admin.contrib.sqla import ModelView
from starlette.requests import Request

class PostView(ModelView):

    def is_accessible(self, request: Request) -> bool:
        return (
            "admin" in request.state.user_roles
            or "post:list" in request.state.user_roles
        )

    def can_view_details(self, request: Request) -> bool:
        return "post:detail" in request.state.user_roles

    def can_create(self, request: Request) -> bool:
        return "post:create" in request.state.user_roles

    def can_edit(self, request: Request) -> bool:
        return "post:edit" in request.state.user_roles

    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.user_roles
```
