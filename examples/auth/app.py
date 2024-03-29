import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette_admin.contrib.sqla import Admin

from . import Base, engine
from .config import DATABASE_FILE, SECRET
from .model import Article
from .provider import MyAuthProvider
from .seed import fill_db
from .view import ArticleView


def init_database() -> None:
    first_run = not os.path.exists(DATABASE_FILE)
    Base.metadata.create_all(engine)
    if first_run:
        fill_db()


app = Starlette(
    routes=[
        Mount(
            "/static", app=StaticFiles(directory="examples/auth/static"), name="static"
        ),
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        ),
    ],
    on_startup=[init_database],
)

# Create admin
admin = Admin(
    engine,
    title="Example: Auth",
    base_url="/admin",
    statics_dir="examples/auth/static",
    login_logo_url="/admin/statics/logo.svg",  # base_url + '/statics/' + path_to_the_file
    auth_provider=MyAuthProvider(allow_paths=["/statics/logo.svg"]),
    middlewares=[Middleware(SessionMiddleware, secret_key=SECRET)],
)

# Add views
admin.add_view(ArticleView(Article))

# Mount admin
admin.mount_to(app)
