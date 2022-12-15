# Configuraciones de administrador

Hay múltiples opciones disponibles para personalizar su interfaz de administración

```python
admin = Admin(
    title="SQLModel Admin",
    base_url="/admin",
    route_name="admin",
    statics_dir="statics/admin",
    templates_dir="templates/admin",
    logo_url="`https`://preview.tabler.io/static/logo-white.svg",
    login_logo_url="`https`://preview.tabler.io/static/logo.svg",
    index_view=CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"),
    auth_provider=MyAuthProvider(login_path="/sign-in", logout_path="/sign-out"),
    middlewares=[],
    debug=False,
)
```


## Parámetros

* `title`: Título del administrador.
* `base_url`: URL base para la interfaz de administración.
* `route_name`: Nombre de administrador montado
* `logo_url`: URL del logotipo que se mostrará en lugar del título.
* `login_logo_url`: si se establece, se usará para la interfaz de inicio de sesión en lugar de logo_url.
* `statics_dir`: Directorio de plantillas para la personalización de archivos estáticos
* `templates_dir`: Directorio de plantillas para personalización
* `index_view`: CustomView(vista personalizada) para usar en la página de índice.
* `auth_provider`: Proveedor de Autenticación
* `middlewares`: Middlewares de Starlette
