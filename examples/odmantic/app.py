from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.odmantic import Admin, ModelView

from odmantic import AIOEngine

from .models import Author, Book
from .views import AuthorView

engine = AIOEngine()
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)

# Create admin
admin = Admin(engine, title="Example: ODMantic")

# Add views
admin.add_view(AuthorView(Author, icon="fa fa-users"))
admin.add_view(ModelView(Book, icon="fa fa-book"))
admin.mount_to(app)
