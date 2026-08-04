import uuid
from datetime import date, datetime
from enum import StrEnum

import mongoengine as me
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    IntegerField,
    StringField,
)
from starlette_admin.contrib.mongoengine.fields import ObjectIdField
from starlette_admin.contrib.mongoengine.view import ModelView


class Status(StrEnum):
    NEW = "new"
    DONE = "done"


class DefaultDocument(me.Document):
    string_scalar = me.StringField(default="hello")
    int_scalar = me.IntField(default=42)
    bool_scalar = me.BooleanField(default=True)
    float_scalar = me.FloatField(default=3.14)
    enum_scalar = me.EnumField(Status, default=Status.NEW)
    date_scalar = me.DateField(default=date(2025, 1, 1))
    datetime_scalar = me.DateTimeField(default=datetime(2025, 1, 1, 12, 0))
    dict_scalar = me.DictField(default=dict)
    no_default = me.StringField()
    callable_default = me.StringField(default=lambda: "from-callable")
    datetime_callable = me.DateTimeField(default=datetime.now)
    uuid_callable = me.StringField(default=lambda: str(uuid.uuid4()))


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


def test_no_default_is_none():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["no_default"] == StringField("no_default")
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


def test_primary_key_default_is_skipped():
    from starlette_admin.contrib.mongoengine.converters import ModelConverter

    class PkDocument(me.Document):
        custom_id = me.ObjectIdField(primary_key=True, default="should-be-ignored")

    field = PkDocument._fields["custom_id"]
    assert ModelConverter._extract_default(field) is None


def test_id_field_has_no_default():
    view = ModelView(DefaultDocument)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["id"] == ObjectIdField(
        "id", exclude_from_create=True, exclude_from_edit=True
    )
