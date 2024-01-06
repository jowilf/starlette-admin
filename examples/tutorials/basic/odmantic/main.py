from odmantic import AIOEngine, Model
from starlette.applications import Starlette
from starlette_admin.contrib.odmantic import Admin, ModelView

engine = AIOEngine()


class Todo(Model):
    title: str
    done: bool


app = Starlette()

# Create an empty admin interface
admin = Admin(engine, title="Tutorials: Basic")

# Add views
admin.add_view(ModelView(Todo, icon="fas fa-list"))

# Mount app
admin.mount_to(app)
