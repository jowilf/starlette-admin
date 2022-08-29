from enum import Enum

import mongoengine as me
import pytest
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    EnumField,
    FileField,
    HasMany,
    HasOne,
    ImageField,
    IntegerField,
    JSONField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.mongoengine import ModelView
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField


class Status(str, Enum):
    NEW = "new"
    ONGOING = "ongoing"
    DONE = "done"


class Attachment(me.Document):
    image = me.ImageField()
    file = me.FileField()


class MyDocument(me.Document):
    int = me.IntField()
    long = me.LongField()
    float = me.FloatField()
    bool = me.BooleanField()
    datetime = me.DateTimeField()
    cplx_datetime = me.ComplexDateTimeField()
    date = me.DateField()
    decimal = me.DecimalField()
    email = me.EmailField()
    emails = me.ListField(me.EmailField())
    enum = me.EnumField(Status)
    dict_field = me.DictField()
    map_field = me.MapField(me.StringField())
    list_enum = me.ListField(me.EnumField(Status))
    tags = me.ListField(me.StringField())
    json_array = me.ListField(me.DictField())
    attachment = me.ReferenceField(Attachment)


class User(me.Document):
    name = me.StringField(required=True)
    documents = me.ListField(me.ReferenceField(MyDocument))


class UserView(ModelView, document=User):
    pass


class AttachmentView(ModelView, document=Attachment):
    pass


class MyDocumentView(ModelView, document=MyDocument):
    pass


def test_fields_conversion():
    assert UserView.identity == "user"
    assert AttachmentView.identity == "attachment"
    assert MyDocumentView.identity == "my-document"
    assert UserView().fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        StringField("name", required=True),
        HasMany("documents", identity="my-document"),
    ]
    assert AttachmentView().fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        ImageField("image"),
        FileField("file"),
    ]
    assert MyDocumentView().fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        IntegerField("int"),
        IntegerField("long"),
        DecimalField("float"),
        BooleanField("bool"),
        DateTimeField("datetime"),
        DateTimeField("cplx_datetime"),
        DateField("date"),
        DecimalField("decimal"),
        EmailField("email"),
        EmailField("emails", is_array=True),
        EnumField.from_enum("enum", Status),
        JSONField("dict_field"),
        JSONField("map_field"),
        EnumField.from_enum("list_enum", Status, is_array=True),
        TagsField("tags"),
        JSONField("json_array"),
        HasOne("attachment", identity="attachment"),
    ]


def test_invalid_list_field():
    with pytest.raises(
        ValueError, match='ListField "invalid_list" must have field specified'
    ):

        class Doc(me.Document):
            invalid_list = me.ListField()

        class DocView(ModelView, document=Doc):
            pass


def test_not_supported_field():
    with pytest.raises(NotSupportedField, match="Field GeoPointField is not supported"):

        class Doc(me.Document):
            field = me.GeoPointField()

        class DocView(ModelView, document=Doc):
            pass


def test_fields_customisation():
    class CustomDocumentView(ModelView, document=MyDocument):
        fields = ["id", "int", MyDocument.long, DecimalField("float", required=True)]
        exclude_fields_from_create = ["long"]
        exclude_fields_from_detail = [MyDocument.int]
        exclude_fields_from_edit = ["float"]

    assert CustomDocumentView().fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        IntegerField("int", exclude_from_detail=True),
        IntegerField("long", exclude_from_create=True),
        DecimalField("float", required=True, exclude_from_edit=True),
    ]


def test_invalid_field_list():
    with pytest.raises(ValueError, match="Can't find column with key 1"):

        class CustomDocumentView(ModelView, document=MyDocument):
            fields = [1]


def test_invalid_exclude_list():
    with pytest.raises(
        ValueError, match="Expected str or monogoengine.BaseField, got int"
    ):

        class CustomDocumentView(ModelView, document=MyDocument):
            exclude_fields_from_create = [1]
