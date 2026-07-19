import uuid
from datetime import date, datetime
from enum import StrEnum

from beanie import Document, Link
from pydantic import BaseModel, Field
from starlette_admin import (
    BooleanField,
    CollectionField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    HasOne,
    IntegerField,
    StringField,
)
from starlette_admin.contrib.beanie.view import ModelView


class Status(StrEnum):
    NEW = "new"
    DONE = "done"


class Address(BaseModel):
    city: str = "Paris"


class Author(Document):
    name: str

    class Settings:
        collection = "unit_test_defaults_authors"


class DefaultDocument(Document):
    string_scalar: str = "hello"
    int_scalar: int = 42
    bool_scalar: bool = True
    float_scalar: float = 3.14
    enum_scalar: Status = Status.NEW
    date_scalar: date = date(2025, 1, 1)
    datetime_scalar: datetime = datetime(2025, 1, 1, 12, 0)
    dict_scalar: dict = Field(default_factory=dict)
    list_scalar: list[str] = Field(default_factory=lambda: ["a", "b"])
    no_default: str
    callable_default: str = Field(default_factory=lambda: "from-callable")
    datetime_callable: datetime = Field(default_factory=datetime.now)
    uuid_callable: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: Address = Field(default_factory=Address)
    author: Link[Author] | None = None

    class Settings:
        collection = "unit_test_defaults_documents"


def test_scalar_defaults_are_detected():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["string_scalar"] == StringField(
        "string_scalar", default="hello"
    )
    assert fields_by_name["int_scalar"] == IntegerField("int_scalar", default=42)
    assert fields_by_name["bool_scalar"] == BooleanField("bool_scalar", default=True)
    assert fields_by_name["float_scalar"] == FloatField("float_scalar", default=3.14)
    assert fields_by_name["enum_scalar"] == EnumField(
        "enum_scalar", enum=Status, default=Status.NEW
    )
    assert fields_by_name["date_scalar"] == DateField(
        "date_scalar", default=date(2025, 1, 1)
    )
    assert fields_by_name["datetime_scalar"] == DateTimeField(
        "datetime_scalar", default=datetime(2025, 1, 1, 12, 0)
    )
    assert fields_by_name["dict_scalar"].default() == {}
    assert fields_by_name["list_scalar"].default() == ["a", "b"]


def test_no_default_is_none():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["no_default"] == StringField("no_default", required=True)
    assert fields_by_name["no_default"].default is None


def test_callable_defaults_are_detected():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["callable_default"].default() == "from-callable"

    before = datetime.now()
    dt_value = fields_by_name["datetime_callable"].default()
    after = datetime.now()
    assert before <= dt_value <= after

    uuid_value = fields_by_name["uuid_callable"].default()
    assert isinstance(uuid.UUID(uuid_value), uuid.UUID)


def test_embedded_model_subfield_defaults_are_detected():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    address_field = fields_by_name["address"]
    assert isinstance(address_field, CollectionField)
    city_field = next(f for f in address_field.fields if f.name == "city")
    assert city_field.default == "Paris"


def test_id_field_has_no_default():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["id"].default is None


def test_link_field_default_is_none():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert isinstance(fields_by_name["author"], HasOne)
    assert fields_by_name["author"].default is None
