from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.mongoengine import Admin, ModelView

from mongoengine import connect, disconnect

from .models import File, Image, Post, Todo, User

app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[lambda: connect("example")],
    on_shutdown=[lambda: disconnect()],
)

# Create admin
admin = Admin(title="Example: MongoEngine")

# Add views
admin.add_view(ModelView(User, icon="fa fa-users"))
admin.add_view(ModelView(Todo, icon="fa fa-list"))
admin.add_view(ModelView(Post, icon="fa fa-blog", label="Blog Posts"))
admin.add_view(ModelView(File, icon="fa fa-file"))
admin.add_view(ModelView(Image, icon="fa fa-file-image"))

# Mount admin to app
admin.mount_to(app)
