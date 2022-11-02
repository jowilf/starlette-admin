from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import DropDown
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.views import Link

from .config import ENGINE_URI
from .models import Base, Post, Tag, Tree, User
from .views import PostView, TagView, UserView

engine = create_engine(ENGINE_URI, connect_args={"check_same_thread": False}, echo=True)


def init_database():
    Base.metadata.create_all(engine)


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
admin.add_view(UserView(User, icon="fa fa-users"))
admin.add_view(PostView(Post, icon="fa fa-blog", label="Blog Posts"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
admin.add_view(ModelView(Tree, icon="fa fa-tree"))
# DropDown
admin.add_view(
    DropDown(
        "Useful Links",
        icon="fa fa-link",
        views=[
            Link("Back Home", url="/"),
            Link("External", url="https://www.example.com/", target="_blank"),
        ],
    )
)

# Mount admin to app
admin.mount_to(app)
