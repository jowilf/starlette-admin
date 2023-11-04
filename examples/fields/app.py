from sqlalchemy import (
    Column,
    Integer,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.fields import IntegerField, SimpleMDEField, TinyMCEEditorField

Base = declarative_base()


class Field(Base):
    __tablename__ = "field"

    id = Column(Integer, primary_key=True)
    tinymce = Column(Text, nullable=False)
    simplemde = Column(Text, nullable=False)


class FieldView(ModelView):
    fields = [
        IntegerField(
            name="id",
            label="ID",
            read_only=True,
        ),
        TinyMCEEditorField(
            name="tinymce",
            label="TinyMCEEditorField",
        ),
        SimpleMDEField(
            name="simplemde",
            label="SimpleMDEField",
        ),
    ]


engine = create_engine(
    "sqlite:///db.sqlite3",
    connect_args={"check_same_thread": False},
    echo=True,
)


def init_database() -> None:
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
admin = Admin(engine, title="Example: Fields")

# Add views
admin.add_view(FieldView(model=Field))

# Mount admin
admin.mount_to(app)
