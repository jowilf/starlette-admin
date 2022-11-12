from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView

from .config import ENGINE_URI
from .models import Author, Base, Book, Dump
from .storage import configure_storage

engine = create_engine(ENGINE_URI, connect_args={"check_same_thread": False}, echo=True)


def init_database() -> None:
    Base.metadata.create_all(engine)


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[configure_storage, init_database],
)

# Create admin
admin = Admin(engine, title="Example: SQLAlchemy-file")

# Add views
admin.add_view(ModelView(Author, icon="fa fa-users"))
admin.add_view(ModelView(Book, icon="fa fa-book"))
admin.add_view(ModelView(Dump, icon="fa fa-dumpster"))

# Mount admin
admin.mount_to(app)
