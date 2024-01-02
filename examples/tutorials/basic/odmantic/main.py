import uvicorn
from odmantic import AIOEngine, Model
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.odmantic import Admin, ModelView

engine = AIOEngine()


class Todo(Model):
    title: str
    done: bool


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)

# Create admin
admin = Admin(engine, title="Example: ODMantic")

# Add views
admin.add_view(ModelView(Todo, icon="fas fa-list"))

# Mount app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("main:app")
