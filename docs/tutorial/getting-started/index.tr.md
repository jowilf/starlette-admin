# Başlarken

## Çalıştırma

Boş bir yönetici arayüzünü uygulamanızda çalıştırmak için ilk adım:

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

## Görünüm Ekleme

### ModelView - Model Görünümü

`ModelView`ler, herhangi bir modeli yönetmek için özelleştirilmiş yönetici sayfaları eklemenizi sağlar.

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

Bu sayede tam donanımlı CRUD görünümlerine sahip olursunuz:

- Arama, sıralama, filtreleme ve kayıtları silme desteği ile bir *liste görünümü*.
- Yeni kayıtlar eklemek için *oluşturma görünümü*.
- Varolan kayıtları güncellemek için *düzenleme görünümü*.
- Varolan kayıtları görüntülemek için *detay görünümü*.

### CustomView - Özel Görünüm

[CustomView][starlette_admin.views.CustomView] ile kendi görünümlerinizi (herhangi bir modele bağlı olmayan) ekleyebilirsiniz. Mesela, analitik verileri gösteren özel bir ana sayfa.

```python
from starlette_admin import CustomView

admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))

```

Derleme işleminin tam kontrolünü elde etmek için `render` metodunu <abbr title="override">geçersiz kılın</abbr>.

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

### Link - Bağlantı

[Link][starlette_admin.views.Link] kullanarak menüye isteğe bağlı bağlantılar ekleyin.

```python
from starlette_admin.views import Link

admin.add_view(Link(label="Home Page", icon="fa fa-link", url="/"))
```

### DropDown - Menü

[DropDown][starlette_admin.views.DropDown] ile menü yapısında görünümleri gruplayın.

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

## Uygulamanıza Admin'i Bağlayın

Son adım, yönetici arayüzlerini uygulamanıza bağlamaktır:

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

Yönetici arayüzüne tarayıcınız üzerinden [http://localhost:8000/admin](http://localhost:8000/admin) adresine giderek erişebilirsiniz.
