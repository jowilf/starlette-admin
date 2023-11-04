import datetime
import enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Integer,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.fields import (
    ColorField,
    DateTimeField,
    EmailField,
    EnumField,
    IntegerField,
    JSONField,
    PasswordField,
    PhoneField,
    SimpleMDEField,
    StringField,
    TextAreaField,
    TinyMCEEditorField,
    URLField,
)

Base = declarative_base()


class ExampleEnum(str, enum.Enum):
    OPTION_1 = "Option 1"
    OPTION_2 = "Option 2"
    OPTION_3 = "Option 3"


class Field(Base):
    __tablename__ = "field"

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    date_updated = Column(DateTime, default=datetime.datetime.utcnow)
    tinymce = Column(Text, nullable=False)
    simplemde = Column(Text, nullable=False)
    text = Column(Text, nullable=False)
    textarea = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    color = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    enum_1 = Column(Enum(ExampleEnum), nullable=False)
    enum_2 = Column(Text, nullable=False)
    json = Column(JSON, nullable=False)


class FieldView(ModelView):
    fields = [
        IntegerField(
            name="id",
            label="ID",
            read_only=True,
        ),
        DateTimeField(
            name="date_created",
            label="Date Created",
            read_only=True,
            exclude_from_create=True,
            exclude_from_edit=True,
        ),
        DateTimeField(
            name="date_updated",
            label="Date Updated",
            read_only=True,
            exclude_from_create=True,
            exclude_from_edit=True,
        ),
        TinyMCEEditorField(
            name="tinymce",
            label="TinyMCEEditorField",
        ),
        SimpleMDEField(
            name="simplemde",
            label="SimpleMDEField",
        ),
        StringField(
            name="text",
            label="StringField",
        ),
        TextAreaField(
            name="textarea",
            label="TextAreaField",
        ),
        URLField(
            name="url",
            label="URLField",
        ),
        EmailField(
            name="email",
            label="EmailField",
        ),
        PhoneField(
            name="phone",
            label="PhoneField",
        ),
        ColorField(
            name="color",
            label="ColorField",
        ),
        PasswordField(
            name="password",
            label="PasswordField",
        ),
        EnumField(
            name="enum_1",
            label="EnumField",
            enum=ExampleEnum,
        ),
        EnumField(
            name="enum_2",
            label="EnumField",
            choices=[
                ("OPTION_4", "Option 4"),
                ("OPTION_5", "Option 5"),
                ("OPTION_6", "Option 6"),
            ],
        ),
        JSONField(
            name="json",
            label="JSONField",
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
