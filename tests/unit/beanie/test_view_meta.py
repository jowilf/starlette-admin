from enum import Enum
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from beanie import Document, Link, PydanticObjectId
from beanie.odm.settings.document import DocumentSettings
from bson import DBRef
from starlette_admin.contrib.beanie.fields import BeanieObjectIdField
from starlette_admin.contrib.beanie.view import (
    InlineModelView,
    ModelView,
    _get_link_target,
)
from starlette_admin.fields import StringField, TagsField

# Shared documents for inline tests


class _Post(Document):
    title: str

    class Settings:
        collection = "unit_test_posts"


class _TagNoLink(Document):
    label: str

    class Settings:
        collection = "unit_test_tags_nolink"


class _TagWithLink(Document):
    post: Link[_Post]
    label: str

    class Settings:
        collection = "unit_test_tags_withlink"


class _TagTwoLinks(Document):
    post1: Link[_Post]
    post2: Link[_Post]
    label: str

    class Settings:
        collection = "unit_test_tags_twolinks"


# _get_link_target


def test_get_link_target_direct_link():
    """Lines 314-315: returns T when annotation is Link[T] directly."""
    assert _get_link_target(Link[_Post]) is _Post


def test_get_link_target_non_link():
    """Line 321: returns None for a plain non-link annotation."""
    assert _get_link_target(str) is None


# InlineModelView error paths


def test_inline_detect_fk_parent_view_no_document():
    """Line 361: ValueError when parent_view has no document attribute."""

    class _NakedParent:
        pass

    class _Inline(InlineModelView):
        document = _TagWithLink
        fk_attr = ""

    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        _Inline(parent_view=_NakedParent())


def test_inline_detect_fk_no_link_to_parent():
    """Lines 378-383: ValueError when no Link field points to the parent document."""

    class _PostView(ModelView):
        pass

    class _Inline(InlineModelView):
        document = _TagNoLink
        fk_attr = ""

    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        _Inline(parent_view=_PostView(_Post))


def test_inline_detect_fk_multiple_links_to_parent():
    """Lines 384-388: ValueError when multiple Link fields point to the parent document."""

    class _PostView(ModelView):
        pass

    class _Inline(InlineModelView):
        document = _TagTwoLinks
        fk_attr = ""

    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        _Inline(parent_view=_PostView(_Post))


# InlineModelView runtime paths


async def test_inline_find_by_parent_uses_link_dbref_query():
    """Line 400: find_by_parent queries {fk}.$id when fk_attr is a Link field."""

    class _PostView(ModelView):
        pass

    class _Inline(InlineModelView):
        document = _TagWithLink
        fk_attr = "post"

    inline = _Inline(parent_view=_PostView(_Post))
    parent = MagicMock()
    parent.id = "abc123"
    expected = [MagicMock()]

    with patch.object(
        _TagWithLink,
        "find",
        return_value=MagicMock(to_list=AsyncMock(return_value=expected)),
    ) as mock_find:
        result = await inline.find_by_parent(MagicMock(), parent)

    mock_find.assert_called_once_with({"post.$id": "abc123"})
    assert result == expected


async def test_inline_build_fk_value_raises_when_parent_view_none():
    """Line 405: build_fk_value raises RuntimeError when parent_view is None."""

    class _Inline(InlineModelView):
        document = _TagWithLink
        fk_attr = "post"

    inline = _Inline(parent_view=None)

    with pytest.raises(RuntimeError, match="wired to a parent view"):
        await inline.build_fk_value(MagicMock(), MagicMock())


def test_fields_customisation():
    class MyModel(Document):
        tags: list[str]
        name: str

    class MyModelView(ModelView):
        fields = ["id", "name", TagsField("tags")]
        exclude_fields_from_create = ["tags"]
        exclude_fields_from_detail = ["id"]
        exclude_fields_from_edit = ["name"]

    assert MyModelView(MyModel).fields == [
        BeanieObjectIdField(
            "id",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True,
        ),
        StringField("name", exclude_from_edit=True, required=True),
        TagsField("tags", exclude_from_create=True),
    ]


# ModelView.get_pk_value with Link object


async def test_get_pk_value_with_link_object():
    """get_pk_value returns the PK from Link.ref when obj is a Link."""

    class _Doc(Document):
        title: str

        class Settings:
            collection = "unit_get_pk_link"

    class _DocView(ModelView):
        pass

    view = _DocView(_Doc)
    ref = MagicMock()
    ref.id = "abc123"
    link = Link(DBRef(collection="unit_get_pk_link", id="abc123"), _Doc)
    link.ref = ref

    result = await view.get_pk_value(MagicMock(), link)
    assert result == "abc123"


async def test_edit_skips_replace_when_unchanged():
    class _PlainColor(Enum):
        RED = "red"

    class _Item(Document):
        name: str
        color: _PlainColor = _PlainColor.RED
        post: Link[_Post] | None = None
        tags: list[Link[_TagWithLink]] = []

    _Item._document_settings = DocumentSettings(name="_Item")
    oid = PydanticObjectId()
    doc = _Item(
        id=oid,
        name="same",
        color=_PlainColor.RED,
        post=Link(DBRef("_Post", oid), _Post),
        tags=[Link(DBRef("_TagWithLink", oid), _TagWithLink)],
    )
    view = ModelView(_Item)
    view.validate = AsyncMock()
    view._emit_before_edit = AsyncMock()
    view._emit_after_edit = AsyncMock()

    with (
        patch.object(_Item, "get", new=AsyncMock(return_value=doc)),
        patch.object(_Item, "replace", new_callable=AsyncMock) as mock_replace,
    ):
        updated = await view.edit(
            MagicMock(),
            oid,
            {"name": "same", "color": "red", "post": str(oid), "tags": [str(oid)]},
        )
    mock_replace.assert_not_awaited()
    assert updated.name == "same"

    with (
        patch.object(_Item, "get", new=AsyncMock(return_value=doc)),
        patch.object(_Item, "replace", new=AsyncMock(return_value=doc)) as mock_replace,
    ):
        await view.edit(
            MagicMock(),
            oid,
            {"name": "changed", "color": "red", "post": str(oid), "tags": [str(oid)]},
        )
    mock_replace.assert_awaited_once()
