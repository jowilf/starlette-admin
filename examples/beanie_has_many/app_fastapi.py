from devtools import debug  # noqa

from starlette.responses import RedirectResponse
from fastapi import FastAPI

import mongoengine
from motor.motor_asyncio import AsyncIOMotorClient
from gridfs import GridFS
from beanie import init_beanie

from starlette_admin.contrib.beanie import Admin

from .config import CONFIG
from .models import BeanieView, Window, House


# used by beanie
client = AsyncIOMotorClient(CONFIG.mongo_uri)

# used by gridfs
db = mongoengine.connect(
    db=CONFIG.mongo_db, host=CONFIG.mongo_uri, alias=CONFIG.mongo_db
)
fs = GridFS(database=db[CONFIG.mongo_db], collection=CONFIG.mongo_col_gridfs)


async def init() -> None:
    # init beanie
    await init_beanie(
        database=client[CONFIG.mongo_db],
        document_models=[Window, House],
    )  # type: ignore

    # Add admin
    admin = Admin(
        title="Example: beanie has many",
        fs=fs,
        debug=True,
    )

    # Add views
    admin.add_view(BeanieView(Window, icon="fa fa-users"))
    admin.add_view(BeanieView(House, icon="fa fa-users"))

    admin.mount_to(app)


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize services on startup."""
    await init()


@app.get("/")
async def index():
    return RedirectResponse(url="/admin", status_code=302)
