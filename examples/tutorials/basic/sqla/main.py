from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///basic.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    done: Mapped[bool]


Base.metadata.create_all(engine)

app = Starlette()  # or app = FastAPI()

# Create an empty admin interface
admin = Admin(engine, title="Tutorials: Basic")

# Add view
admin.add_view(ModelView(Todo, icon="fas fa-list"))

# Mount admin to your app
admin.mount_to(app)

with Session(engine) as session:
    session.add_all(
        [
            Todo(title="Buy groceries for the week", done=True),
            Todo(title="Complete 30 minutes of cardio", done=False),
            Todo(title="Write a blog post", done=True),
            Todo(title="Star the Starlette-Admin repo", done=False),
        ]
    )
    session.commit()
