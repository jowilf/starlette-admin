"""Unit tests for the Tortoise contrib's view construction and converter
error paths. No database connection is required: everything here inspects
model metadata available at class-definition time.
"""

import pytest
from starlette_admin.contrib.tortoise import ModelView
from starlette_admin.contrib.tortoise.converters import ModelConverter
from starlette_admin.contrib.tortoise.exceptions import (
    InvalidModelError,
    NotSupportedField,
)
from starlette_admin.fields import IntegerField, StringField
from tortoise import fields
from tortoise.models import Model


class Item(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50)
    payload = fields.BinaryField(null=True)


class Node(Model):
    """A model whose relations are never resolved: this module is never
    passed to `Tortoise.init()` or `Tortoise.init_models()`.
    """

    id = fields.IntField(primary_key=True)
    parent = fields.ForeignKeyField("models.Node", related_name="children")


def test_invalid_model_raises():
    class NotAModel:
        pass

    with pytest.raises(InvalidModelError, match="not a Tortoise ORM model"):
        ModelView(NotAModel)


def test_uninitialized_relations_raise():
    with pytest.raises(InvalidModelError, match="not initialized"):
        ModelView(Node)


def test_pk_field_falls_back_to_string_field():
    class ItemView(ModelView):
        fields = ["name"]

    view = ItemView(Item)
    assert view.pk_attr == "id"
    assert view.pk_field == StringField("id")


def test_declared_pk_field_is_reused():
    class ItemView(ModelView):
        fields = ["id", "name"]

    view = ItemView(Item)
    assert isinstance(view.pk_field, IntegerField)


def test_base_field_instances_pass_through():
    class ItemView(ModelView):
        fields = [StringField("name", label="Custom")]

    view = ItemView(Item)
    assert view.fields[0].label == "Custom"


def test_unknown_field_name_raises():
    class ItemView(ModelView):
        fields = ["nope"]

    with pytest.raises(ValueError, match="Can't find field with key: nope"):
        ItemView(Item)


def test_unsupported_field_type_raises():
    with pytest.raises(NotSupportedField, match="BinaryField is not supported"):
        ModelConverter().convert_fields_list(fields=["payload"], model=Item)
