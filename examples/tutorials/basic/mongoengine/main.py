import mongoengine as db
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Todo(db.Document):
    title = db.StringField()
    done = db.BooleanField()


app = Starlette(
    on_startup=[lambda: connect("basic")],
    on_shutdown=[disconnect],
)

# Create an empty admin interface
admin = Admin(title="Tutorials: Basic")

# Add view
admin.add_view(ModelView(Todo, icon="fas fa-list"))

# Mount admin to your app
admin.mount_to(app)
