# Empezando

## Inicialización

El primer paso es inicializar una interfaz de administración vacía para su aplicación:

=== "SQLAlchemy"
    ```python
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqla import Admin

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    admin = Admin(engine)
    ```
=== "SQLModel"
    ```python
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqlmodel import Admin

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    admin = Admin(engine)
    ```
=== "MongoEngine"
    ```python
    from starlette_admin.contrib.mongoengine import Admin

    admin = Admin()
    ```
=== "ODMantic"
    ```python
    from odmantic import AIOEngine
    from starlette_admin.contrib.odmantic import Admin

    engine = AIOEngine()

    admin = Admin(engine)
    ```

## Agregando Vistas

### ModelView(Vista de modelo)

Las vistas de modelo permiten agregar un conjunto dedicado de páginas de administración para gestionar cualquier modelo.

=== "SQLAlchemy"
    ```python hl_lines="2 10-11"
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqla import Admin, ModelView

    from .models import User, Post

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    ```
=== "SQLModel"
    ```python hl_lines="2 10-11"
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqlmodel import Admin, ModelView

    from .models import User, Post

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    ```
=== "MongoEngine"
    ```python hl_lines="1 7-8"
    from starlette_admin.contrib.mongoengine import Admin, ModelView

    from .models import Post, User

    admin = Admin()

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    ```
=== "ODMantic"
    ```python hl_lines="2 10-11"
    from odmantic import AIOEngine
    from starlette_admin.contrib.odmantic import Admin, ModelView

    from .models import Post, User

    engine = AIOEngine()

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    ```
Esto permite tener un conjunto de vistas CRUD completamente funcionales para el modelo:

- Una *vista de lista*, con soporte para búsqueda, ordenación, filtrado y eliminación de registros.
- Una *vista de creación* para agregar nuevos registros.
- Una *vista de edición* para actualizar registros existentes.
- Una *vista de detalles* solo de lectura.

### CustomView(Vista personalizada)

Con [CustomView][starlette_admin.views.CustomView] se pueden agregar vistas personalizadas (no vinculadas a ningún modelo en particular). Por ejemplo, una página de inicio personalizada que muestre algunos datos de análisis.

```python
from starlette_admin import CustomView

admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))

```

Para tener un control completo del proceso de renderizado, se puede sobrescribir el método `render`

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView


class HomeView(CustomView):
    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        return templates.TemplateResponse(
            "home.html", {"request": request, "latest_posts": ..., "top_users": ...}
        )


admin.add_view(HomeView(label="Home", icon="fa fa-home", path="/home"))
```


### Link

Se puede utilizar [Link][starlette_admin.views.Link] para agregar hipervínculos arbitrarios al menú de la interfaz de administración.

```python
from starlette_admin.views import Link

admin.add_view(Link(label="Home Page", icon="fa fa-link", url="/"))
```

### DropDown

Se puede utilizar [DropDown][starlette_admin.views.DropDown] para agrupar vistas juntas en la estructura del menú.

```python
from starlette_admin import CustomView, DropDown
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.views import Link

from .models import User

admin.add_view(
    DropDown(
        "Resources",
        icon="fa fa-list",
        views=[
            ModelView(User),
            Link(label="Home Page", url="/"),
            CustomView(label="Dashboard", path="/dashboard", template_path="dashboard.html"),
        ],
    )
)

```

## Monte el admin en su aplicación

El último paso es montar las interfaces de administración en su aplicación.

=== "SQLAlchemy"
    ```python hl_lines="2 9 16"
    from sqlalchemy import create_engine
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    from .models import Post, User

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    app = Starlette() # FastAPI()

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    admin.mount_to(app)

    ```
=== "SQLModel"
    ```python hl_lines="2 9 16"
    from sqlalchemy import create_engine
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqlmodel import Admin, ModelView

    from .models import Post, User

    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})

    app = Starlette()  # FastAPI()

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    admin.mount_to(app)

    ```
=== "MongoEngine"
    ```python hl_lines="1 6 13"
    from starlette.applications import Starlette
    from starlette_admin.contrib.mongoengine import Admin, ModelView

    from .models import Post, User

    app = Starlette()  # FastAPI()

    admin = Admin()

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    admin.mount_to(app)
    ```
=== "ODMantic"
    ```python hl_lines="2 9 16"
    from odmantic import AIOEngine
    from starlette.applications import Starlette
    from starlette_admin.contrib.odmantic import Admin, ModelView

    from .models import Post, User

    engine = AIOEngine()

    app = Starlette()  # FastAPI()

    admin = Admin(engine)

    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Post))

    admin.mount_to(app)
    ```

Ahora puede acceder a sus interfaces de administración en su navegador en [http://localhost:8000/admin](http://localhost:8000/admin)
