import os

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin

from . import Base, engine
from .config import DATABASE_FILE
from .models import Article, ArticleAdmin
from .seed import fill_db


def init_database() -> None:
    first_run = not os.path.exists(DATABASE_FILE)
    Base.metadata.create_all(engine)
    if first_run:
        fill_db()


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[init_database],
)

# Create admin
admin = Admin(engine, title="Example: SQLAlchemy")

# Add views
admin.add_view(ArticleAdmin(Article))

# Mount admin
admin.mount_to(app)
