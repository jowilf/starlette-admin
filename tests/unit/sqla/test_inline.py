"""Unit tests for `starlette_admin.contrib.sqla` `InlineModelView` helpers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import IntegerField, StringField
from starlette_admin.contrib.sqla.view import InlineModelView, ModelView


class Base(DeclarativeBase):
    pass


class _Other(Base):
    __tablename__ = "test_inline_other"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class _Parent(Base):
    __tablename__ = "test_inline_parent"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    other_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("test_inline_other.id")
    )
    children: Mapped[list["_Child"]] = relationship("_Child", back_populates="parent")
    other: Mapped["_Other"] = relationship("_Other", uselist=False)


class _Child(Base):
    __tablename__ = "test_inline_child"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_inline_parent.id"))
    parent: Mapped["_Parent"] = relationship("_Parent", back_populates="children")


class _Orphan(Base):
    __tablename__ = "test_inline_orphan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(Integer)


class _ParentView(ModelView):
    fields = [IntegerField("id"), StringField("name")]


class _ChildInline(InlineModelView):
    model = _Child
    fk_attr = ""
    fields = [IntegerField("id"), IntegerField("parent_id")]


class _AutoChildInline(InlineModelView):
    model = _Child
    fk_attr = ""
    fields = [IntegerField("id"), IntegerField("parent_id")]


class _ChildInlineExplicit(InlineModelView):
    model = _Child
    fk_attr = "parent_id"
    fields = [IntegerField("id"), IntegerField("parent_id")]


class _OrphanInline(InlineModelView):
    model = _Orphan
    fk_attr = ""
    fields = [IntegerField("id"), IntegerField("parent_id")]


def test_detect_fk_requires_parent_view():
    inline = _ChildInline()
    with pytest.raises(RuntimeError, match="Cannot auto-detect fk_attr"):
        inline._get_fk_attr()


def test_detect_fk_skips_unrelated_relationships():
    inline = _AutoChildInline()
    inline.parent_view = _ParentView(_Parent)
    assert inline._get_fk_attr() == "parent_id"


def test_detect_fk_fails_when_no_relationship():
    inline = _OrphanInline()
    inline.parent_view = _ParentView(_Parent)
    with pytest.raises(ValueError, match="cannot auto-detect fk_attr"):
        inline._get_fk_attr()


@pytest.mark.asyncio
async def test_find_by_parent_uses_async_session():
    inline = _ChildInlineExplicit()
    inline.parent_view = _ParentView(_Parent)
    parent = _Parent(id=1, name="P")
    child = _Child(id=1, parent_id=1)

    request = MagicMock()
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    unique=MagicMock(
                        return_value=MagicMock(all=MagicMock(return_value=[child]))
                    )
                )
            )
        )
    )
    request.state.session = session

    rows = await inline.find_by_parent(request, parent)
    session.execute.assert_awaited_once()
    assert rows == [child]
