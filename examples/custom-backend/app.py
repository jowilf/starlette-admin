from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB

from .config import DATABASE_FILE
from .view import PostView

db = TinyDB(DATABASE_FILE)

app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)

admin = Admin()
admin.add_view(PostView(db))
admin.mount_to(app)
