from contextlib import asynccontextmanager

import uvicorn
from models import Base, Post, User
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin
from views import DashboardView, PostView, UserView

DATABASE_FILE = "07_dashboard.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


@asynccontextmanager
async def lifespan(_app: Starlette):
    Base.metadata.create_all(engine)
    from seed import seed_data

    seed_data(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
)

admin = Admin(
    engine,
    title="Example: Dashboard",
    index_view=DashboardView(),
    secret_key="dev-only-change-me",
)

admin.add_view(UserView(User, icon="fa fa-users"))
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
