# Getting started

## Initialization

The first step is to initialize an empty admin interface for your app:

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

## Adding Views

### ModelView

Model views allow you to add a dedicated set of admin pages for managing any model.

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
This gives you a set of fully featured CRUD views for your model: 

- A *list view*, with support for searching, sorting, filtering, and deleting records.
- A *create view* for adding new records.
- An *edit view* for updating existing records.
- A read-only *details view*.

### CustomView

With [CustomView][starlette_admin.views.CustomView] you can add your own views (not tied to any particular model). For example,
a custom home page that displays some analytics data. 

```python
from starlette_admin import CustomView

admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))

```

To have a full control of the rendering, override the `render` methods

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

Use [Link][starlette_admin.views.Link] to add arbitrary hyperlinks to the menu

```python
from starlette_admin.views import Link

admin.add_view(Link(label="Home Page", icon="fa fa-link", url="/"))
```

### DropDown

Use [DropDown][starlette_admin.views.DropDown] to group views together in menu structure

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

## Mount admin to your app

The last step is to mount the admin interfaces to your app

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

You can now access your admin interfaces in your browser at [http://localhost:8000/admin](http://localhost:8000/admin)