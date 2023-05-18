import enum
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pytest
from odmantic import EmbeddedModel, Model, Reference
from pydantic import AnyUrl, EmailStr
from pydantic.color import Color
from starlette_admin import (
    BooleanField,
    CollectionField,
    ColorField,
    DateTimeField,
    DecimalField,
    EmailField,
    EnumField,
    FloatField,
    HasOne,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    TagsField,
    URLField,
)
from starlette_admin.contrib.odmantic import ModelView
from starlette_admin.contrib.odmantic.exceptions import NotSupportedAnnotation


class Status(str, enum.Enum):
    NEW = "new"
    ONGOING = "ongoing"
    DONE = "done"


class Document(Model):
    int: Optional[int]
    float: float
    bool: Optional[bool]
    datetime: datetime
    decimal: Decimal
    email: EmailStr
    url: AnyUrl
    enum: Optional[Status]
    enums: List[Status]
    list_str: Optional[List[str]]
    json_: Dict[str, Any]
    color: Color


class Address(EmbeddedModel):
    city: str
    state: str


class Hobby(EmbeddedModel):
    name: str
    reason: str


class User(Model):
    name: str
    address: Address
    hobbies: List[Hobby]
    document: Document = Reference()


def test_view_meta_info():
    model_view = ModelView(
        User, identity="other-id", label="Other label", name="Other name"
    )
    assert model_view.identity == "other-id"
    assert model_view.label == "Other label"
    assert model_view.name == "Other name"


def test_view_meta_info_with_class_level_config():
    class CustomView(ModelView):
        identity = "custom-id"
        label = "Custom label"
        name = "Custom name"

    model_view = CustomView(User)
    assert model_view.identity == "custom-id"
    assert model_view.label == "Custom label"
    assert model_view.name == "Custom name"


def test_view_meta_info_with_overridden_class_level_config():
    class CustomView(ModelView):
        identity = "custom-id"
        label = "Custom label"
        name = "Custom name"

    model_view = CustomView(
        User, identity="other-id", label="Other label", name="Other name"
    )
    assert model_view.identity == "other-id"
    assert model_view.label == "Other label"
    assert model_view.name == "Other name"


def test_fields_conversion():
    assert ModelView(User).fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        StringField("name", required=True),
        CollectionField(
            "address",
            fields=[
                StringField("city", required=True),
                StringField("state", required=True),
            ],
            required=True,
        ),
        ListField(
            CollectionField(
                "hobbies",
                fields=[
                    StringField("name", required=True),
                    StringField("reason", required=True),
                ],
                required=True,
            ),
            required=True,
        ),
        HasOne("document", identity="document", required=True),
    ]

    assert ModelView(Document).fields == [
        StringField("id", exclude_from_create=True, exclude_from_edit=True),
        IntegerField("int"),
        FloatField("float", required=True),
        BooleanField("bool"),
        DateTimeField("datetime", required=True),
        DecimalField("decimal", required=True),
        EmailField("email", required=True),
        URLField("url", required=True),
        EnumField("enum", enum=Status),
        EnumField("enums", enum=Status, multiple=True, required=True),
        ListField(StringField("list_str")),
        JSONField("json_", required=True),
        ColorField("color", required=True),
    ]


def test_not_supported_annotation():
    with pytest.raises(
        NotSupportedAnnotation, match=re.escape("Cannot automatically convert 'tuple_'")
    ):

        class MyModel(Model):
            tuple_: Tuple[str, ...]

        ModelView(MyModel)


def test_fields_customisation():
    class MyModel(Model):
        tags: List[str]
        name: str

    class MyModelView(ModelView):
        fields = ["id", MyModel.name, TagsField("tags")]
        exclude_fields_from_create = ["tags"]
        exclude_fields_from_detail = ["id"]
        exclude_fields_from_edit = [MyModel.name]

    assert MyModelView(MyModel).fields == [
        StringField(
            "id",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True,
        ),
        StringField("name", exclude_from_edit=True, required=True),
        TagsField("tags", exclude_from_create=True),
    ]


def test_invalid_field_list():
    with pytest.raises(ValueError, match="Can't find attribute with key 1"):

        class InvalidUserView(ModelView):
            fields = [1]

        InvalidUserView(User)


def test_invalid_exclude_list():
    with pytest.raises(ValueError, match="Expected str or FieldProxy, got int"):

        class InvalidUserView(ModelView):
            exclude_fields_from_create = [1]

        InvalidUserView(User)


def test_invalid_fields_default_sort_list():
    with pytest.raises(
        ValueError,
        match=re.escape("Invalid argument, Expected Tuple[str | FieldProxy, bool]"),
    ):

        class InvalidDocumentView(ModelView):
            fields_default_sort = [Document.id, (Document.bool, True), (1,)]

        InvalidDocumentView(Document)


if __name__ == "__main__":
    print(User.__odm_fields__)
