from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqla import ModelView as SQLAModelView
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.fields import BaseField


class PlainBase(DeclarativeBase):
    pass


class PlainProject(PlainBase):
    __tablename__ = "plain_project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Project(SQLModel, table=True):
    id: int | None = Field(None, primary_key=True)
    name: str = Field(title="Project name")
    code: str


def test_pydantic_field_title_is_used_as_label():
    view = ModelView(Project)
    fields = {
        field.name: field for field in view.fields if isinstance(field, BaseField)
    }
    assert fields["name"].label == "Project name"


def test_field_without_pydantic_title_keeps_default_label():
    view = ModelView(Project)
    fields = {
        field.name: field for field in view.fields if isinstance(field, BaseField)
    }
    assert fields["code"].label == "Code"


def test_plain_sqlalchemy_model_keeps_default_label():
    view = SQLAModelView(PlainProject)
    fields = {
        field.name: field for field in view.fields if isinstance(field, BaseField)
    }
    assert fields["name"].label == "Name"
