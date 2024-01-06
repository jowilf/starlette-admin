from typing import Optional

from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette.applications import Starlette
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///basic.db", connect_args={"check_same_thread": False})


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool


SQLModel.metadata.create_all(engine)

app = Starlette()  # or app = FastAPI()

# Create an empty admin interface
admin = Admin(engine, title="Tutorials: Basic")

# Add view
admin.add_view(ModelView(Todo, icon="fas fa-list"))

# Mount admin to your app
admin.mount_to(app)
