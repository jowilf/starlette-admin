from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from sqlmodel import SQLModel

from .config import ENGINE_URI
from .models import Comment, Dump, Post, User
from .views import CommentView, DumpView, PostView

engine = create_engine(ENGINE_URI, connect_args={"check_same_thread": False}, echo=True)


def init_database() -> None:
    SQLModel.metadata.create_all(engine)


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
admin = Admin(engine, title="Example: SQLModel")

# Add views
admin.add_view(ModelView(User, icon="fa fa-users"))
admin.add_view(PostView(Post, label="Blog Posts", icon="fa fa-blog"))
admin.add_view(CommentView(Comment, icon="fa fa-comments"))
admin.add_view(DumpView(Dump, icon="fa fa-dumpster"))

# Mount to admin to app
admin.mount_to(app)
