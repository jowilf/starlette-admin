from contextlib import asynccontextmanager

from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.views import Link as AdminLink
from starlette_admin import DropDown
from .dependencies import create_db_and_tables
import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

admin = Admin()


async def setup_db():
    models = await create_db_and_tables()

    for model in models:
        admin.add_view(ModelView(model, name=model.__name__, icon="database"))


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[setup_db],
)
admin.mount_to(app)
