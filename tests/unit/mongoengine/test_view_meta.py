import re
from enum import StrEnum
from unittest.mock import MagicMock

import mongoengine as me
import pytest
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    URLField,
)
from starlette_admin.contrib.mongoengine import ModelView
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField
from starlette_admin.contrib.mongoengine.fields import (
    FileField,
    ImageField,
    ObjectIdField,
)
from starlette_admin.contrib.mongoengine.view import InlineModelView
from starlette_admin.exceptions import FormValidationError


class Status(StrEnum):
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
    url = me.URLField()
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


def test_view_meta_info():
    model_view = ModelView(
        User, key="other-id", menu_label="Other label", display_name="Other name"
    )
    assert model_view.key == "other-id"
    assert model_view.menu_label == "Other label"
    assert model_view.display_name == "Other name"


def test_view_meta_info_with_class_level_config():
    class CustomView(ModelView):
        key = "custom-id"
        menu_label = "Custom label"
        display_name = "Custom name"

    model_view = CustomView(User)
    assert model_view.key == "custom-id"
    assert model_view.menu_label == "Custom label"
    assert model_view.display_name == "Custom name"


def test_view_meta_info_with_overridden_class_level_config():
    class CustomView(ModelView):
        key = "custom-id"
        menu_label = "Custom label"
        display_name = "Custom name"

    model_view = CustomView(
        User, key="other-id", menu_label="Other label", display_name="Other name"
    )
    assert model_view.key == "other-id"
    assert model_view.menu_label == "Other label"
    assert model_view.display_name == "Other name"


def test_fields_conversion():
    assert ModelView(User).fields == [
        ObjectIdField("id", exclude_from_create=True, exclude_from_edit=True),
        StringField("name", required=True),
        HasMany("documents", key="my-document", default=list),
    ]
    assert ModelView(Attachment).fields == [
        ObjectIdField("id", exclude_from_create=True, exclude_from_edit=True),
        ImageField("image"),
        FileField("file"),
    ]
    assert ModelView(MyDocument).fields == [
        ObjectIdField("id", exclude_from_create=True, exclude_from_edit=True),
        IntegerField("int"),
        IntegerField("long"),
        FloatField("float"),
        BooleanField("bool"),
        DateTimeField("datetime"),
        DateTimeField("cplx_datetime"),
        DateField("date"),
        DecimalField("decimal"),
        EmailField("email"),
        URLField("url"),
        EnumField("enum", enum=Status),
        JSONField("dict_field", default=dict),
        JSONField("map_field", default=dict),
        EnumField("list_enum", enum=Status, multiple=True),
        ListField(StringField("tags")),
        JSONField("json_array", default=dict),
        HasOne("attachment", key="attachment"),
    ]


def test_invalid_list_field():
    with pytest.raises(
        ValueError, match='ListField "invalid_list" must have field specified'
    ):

        class Doc(me.Document):
            invalid_list = me.ListField()

        ModelView(Doc)


def test_not_supported_field():
    with pytest.raises(
        NotSupportedField,
        match="Field GeoPointField can not be converted automatically",
    ):

        class Doc(me.Document):
            field = me.GeoPointField()

        ModelView(Doc)


def test_fields_customisation():
    class CustomDocumentView(ModelView):
        fields = ["id", "int", MyDocument.long, DecimalField("float", required=True)]
        exclude_fields_from_create = ["long"]
        exclude_fields_from_detail = [MyDocument.int]
        exclude_fields_from_edit = ["float"]

    assert CustomDocumentView(MyDocument).fields == [
        ObjectIdField("id", exclude_from_create=True, exclude_from_edit=True),
        IntegerField("int", exclude_from_detail=True),
        IntegerField("long", exclude_from_create=True),
        DecimalField("float", required=True, exclude_from_edit=True),
    ]


def test_invalid_field_list():
    with pytest.raises(ValueError, match="Can't find field with key 1"):

        class CustomDocumentView(ModelView):
            fields = [1]

        CustomDocumentView(MyDocument)


def test_invalid_exclude_list():
    with pytest.raises(
        ValueError, match=r"Expected str or monogoengine.BaseField, got int"
    ):

        class CustomDocumentView(ModelView):
            exclude_fields_from_create = [1]

        CustomDocumentView(MyDocument)


def test_invalid_fields_default_sort_list():
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Invalid argument, Expected Tuple[str | monogoengine.BaseField, bool]"
        ),
    ):

        class CustomDocumentView(ModelView):
            fields_default_sort = [MyDocument.id, (MyDocument.long, True), (1,)]

        CustomDocumentView(MyDocument)


# ── ModelView method coverage ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_all_with_limit_zero_returns_unbounded_slice():
    view = ModelView(User)
    view.document = MagicMock()
    view.document.objects.return_value.order_by.return_value = ["a", "b", "c", "d"]

    result = await view.find_all(MagicMock(), skip=1, limit=0, sorts=[("name", "asc")])

    assert result == ["b", "c", "d"]
    view.document.objects.assert_called_once()
    view.document.objects.return_value.order_by.assert_called_once_with("+name")


@pytest.mark.asyncio
async def test_handle_exception_non_validation_error_raises():
    view = ModelView(User)
    with pytest.raises(RuntimeError, match="boom"):
        await view.handle_exception(MagicMock(), RuntimeError("boom"))


@pytest.mark.asyncio
async def test_handle_exception_form_validation_error_reraises_unchanged():
    view = ModelView(User)
    exc = FormValidationError({"name": "required"})
    with pytest.raises(FormValidationError) as excinfo:
        await view.handle_exception(MagicMock(), exc)
    assert excinfo.value is exc


# InlineModelView auto-detect error paths


class MeParent(me.Document):
    title = me.StringField()

    meta = {"collection": "unit_test_me_parent"}


class MeChildNoRef(me.Document):
    body = me.StringField()

    meta = {"collection": "unit_test_me_child_noref"}


class MeChildTwoRefs(me.Document):
    parent1 = me.ReferenceField(MeParent)
    parent2 = me.ReferenceField(MeParent)
    body = me.StringField()

    meta = {"collection": "unit_test_me_child_tworefs"}


def test_inline_detect_fk_no_reference_field():
    """Lines 389-394: ValueError when no ReferenceField points to the parent document."""

    class _ParentView(ModelView):
        pass

    class _Inline(InlineModelView):
        document = MeChildNoRef
        fk_attr = ""

    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        _Inline(parent_view=_ParentView(MeParent))


def test_inline_detect_fk_multiple_reference_fields():
    """Lines 395-399: ValueError when multiple ReferenceFields point to the parent document."""

    class _ParentView(ModelView):
        pass

    class _Inline(InlineModelView):
        document = MeChildTwoRefs
        fk_attr = ""

    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        _Inline(parent_view=_ParentView(MeParent))
