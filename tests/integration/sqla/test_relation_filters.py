"""End-to-end tests for filtering the SQLAlchemy list page by relation fields
(`HasOne`/`HasMany`): the filter builder offers them (with a relation-lookup
record picker), the `filter` query param is applied, and active-filter pills
show the selected records' labels rather than their raw primary keys.
"""

import json
import re
import uuid
from typing import Any, ClassVar

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import (
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Uuid,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import HasOne
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.filters import RelationInFilter
from starlette_admin.contrib.sqla.view import ModelView
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRule,
    FilterValidationError,
)
from starlette_admin.types import RequestAction


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "relfilter_author"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    books: Mapped[list["Book"]] = relationship("Book", back_populates="author")

    async def __admin_repr__(self, request: Request) -> str:
        return f"Writer {self.name}"


class CompositeTag(Base):
    __tablename__ = "relfilter_composite_tag"
    ns: Mapped[str] = mapped_column(String(20), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, primary_key=True)


class Book(Base):
    __tablename__ = "relfilter_book"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    author_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("relfilter_author.id"), nullable=True
    )
    author: Mapped["Author | None"] = relationship("Author", back_populates="books")
    tag_ns: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tag_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tag: Mapped["CompositeTag | None"] = relationship("CompositeTag")

    __table_args__ = (
        ForeignKeyConstraint(
            ["tag_ns", "tag_active"],
            ["relfilter_composite_tag.ns", "relfilter_composite_tag.active"],
        ),
    )


class AuthorView(ModelView):
    fields = ["id", "name", "books"]


class RecordingAuthorView(AuthorView):
    """Records the request action each `find_by_pks` call runs under."""

    actions_seen: ClassVar[list[Any]] = []

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Any:
        type(self).actions_seen.append(request.state.action)
        return await super().find_by_pks(request, pks)


class BookView(ModelView):
    fields = ["id", "title", "author"]


def _list_total(html: str) -> int:
    m = re.search(r"Showing \d+ to \d+ of (\d+)", html)
    return int(m.group(1)) if m else 0


def _builder_fields(html: str) -> list[dict]:
    m = re.search(r"fields: (\[.*?\]),\s*initialFilter", html, re.S)
    assert m, "filter builder config not found"
    return json.loads(m.group(1))


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        alice = Author(id=1, name="Alice")
        bob = Author(id=2, name="Bob")
        tag = CompositeTag(ns="sci", active=True)
        session.add_all([alice, bob, tag])
        session.add_all(
            [
                Book(id=1, title="A1", author=alice, tag=tag),
                Book(id=2, title="A2", author=alice),
                Book(id=3, title="B1", author=bob),
                Book(id=4, title="Orphan", author=None),
            ]
        )
        session.commit()
    yield engine
    Base.metadata.drop_all(engine)


def _make_client(
    engine,
    book_view: type[ModelView],
    author_view: type[ModelView] = AuthorView,
) -> AsyncClient:
    app = Starlette()
    admin = Admin(engine)
    admin.add_view(author_view(Author))
    admin.add_view(book_view(Book))
    admin.mount_to(app)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest_asyncio.fixture
async def client(engine):
    async with _make_client(engine, BookView) as c:
        yield c


@pytest.mark.asyncio
async def test_builder_and_filtering_by_relations(client: AsyncClient):
    # Builder metadata for HasOne and HasMany
    res = await client.get("/admin/book/list")
    assert res.status_code == 200
    author_meta = {f["name"]: f for f in _builder_fields(res.text)}["author"]
    assert {f["name"] for f in author_meta["filters"]} == {
        "in",
        "not_in",
        "is_null",
        "is_not_null",
    }
    assert author_meta["relation"]["pk"] == "id"
    assert author_meta["relation"]["url"].endswith("/admin/_api/author/relation-lookup")

    res_author = await client.get("/admin/author/list")
    books_meta = {f["name"]: f for f in _builder_fields(res_author.text)}["books"]
    assert {f["name"] for f in books_meta["filters"]} == {
        "any_of",
        "none_of",
        "is_null",
        "is_not_null",
    }

    # Filtering books by author (HasOne) and authors by books (HasMany)
    for filter_str, expected in [
        ("author__in=1", 2),
        ("author__in=1,2", 3),
        ("author__not_in=1", 2),
        ("author__is_null", 1),
        ("author__in=1 AND (title__eq=A1 OR title__contains=2)", 2),
    ]:
        r = await client.get("/admin/book/list", params={"filter": filter_str})
        assert r.status_code == 200
        assert _list_total(r.text) == expected

    for filter_str, expected in [
        ("books__any_of=1", 1),
        ("books__any_of=1,3", 2),
        ("books__none_of=3", 1),
        ("books__none_of=1,3", 0),
    ]:
        r = await client.get("/admin/author/list", params={"filter": filter_str})
        assert r.status_code == 200
        assert _list_total(r.text) == expected

    # Active filter pills resolve labels under RELATION_LOOKUP, and empty values return 400
    r = await client.get("/admin/book/list", params={"filter": "author__in=1,2"})
    assert "Writer Alice" in r.text and "Writer Bob" in r.text
    assert (
        await client.get("/admin/book/list", params={"filter": "author__in="})
    ).status_code == 400


@pytest.mark.asyncio
async def test_relation_filter_edge_cases_and_composite_pk(engine):
    """Covers composite PK related clauses, unregistered/inaccessible foreign
    views, bare requests without ROUTE_NAME, and label resolution fallbacks."""
    RecordingAuthorView.actions_seen = []
    async with _make_client(engine, BookView, RecordingAuthorView) as c:
        res = await c.get("/admin/book/list", params={"filter": "author__in=1"})
        assert res.status_code == 200
        assert RecordingAuthorView.actions_seen == [RequestAction.RELATION_LOOKUP]

    # Composite PK relation clause (`len(pk_columns) > 1` and bool coercion)
    with Session(engine) as session:
        view = ModelView(Book)
        ctx = FilterApplyContext(
            query=None,
            field_name="tag",
            value=["sci,True"],
            view=view,
        )
        clause = RelationInFilter().apply(ctx)
        rows = session.execute(select(Book).where(clause)).scalars().all()
        assert [b.title for b in rows] == ["A1"]

    # Unmounted view / missing foreign view / inaccessible foreign view / failed find_by_pks
    bare_req = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
    )
    bare_req.state.action = RequestAction.LIST
    unmounted_view = BookView(Book)
    assert (
        unmounted_view._relation_filter_foreign_view(
            bare_req, HasOne("author", key=None)
        )
        is None
    )
    assert (
        unmounted_view._relation_filter_foreign_view(
            bare_req, HasOne("author", key="author")
        )
        is None
    )
    # Builder omits RELATION filters when foreign view cannot be resolved
    builder_ops = {
        f["name"]: {op["name"] for op in f["filters"]}
        for f in unmounted_view._filter_builder_fields(bare_req)
    }
    assert builder_ops["author"] == {"is_null", "is_not_null"}
    assert (
        await unmounted_view._resolve_relation_labels(
            bare_req, HasOne("author", key="author"), {"1"}
        )
        is None
    )

    # Mounted view with bare request (no ROUTE_NAME in app.state) -> lookup returns None
    app = Starlette()
    admin = Admin(engine)
    mounted_book_view = BookView(Book)
    admin.add_view(AuthorView(Author))
    admin.add_view(mounted_book_view)
    admin.mount_to(app)
    assert (
        mounted_book_view._relation_filter_foreign_view(
            bare_req, HasOne("author", key="unknown-view")
        )
        is None
    )
    assert (
        mounted_book_view._relation_filter_lookup(
            bare_req, HasOne("author", key="author")
        )
        is None
    )

    # Mounted view with inaccessible foreign view and failing find_by_pks
    class InaccessibleAuthorView(AuthorView):
        def is_accessible(self, request: Request) -> bool:
            return False

    class FailingAuthorView(AuthorView):
        async def find_by_pks(self, request: Request, pks: list[Any]) -> Any:
            raise RuntimeError("db error")

    for bad_author_cls in (InaccessibleAuthorView, FailingAuthorView):
        app2 = Starlette()
        admin2 = Admin(engine)
        bv = BookView(Book)
        admin2.add_view(bad_author_cls(Author))
        admin2.add_view(bv)
        admin2.mount_to(app2)
        fg = FilterGroup(
            rules=[
                FilterRule(field="author", filter="in", value=["1"]),
                FilterRule(field="title", filter="in", value=["A1"]),
            ]
        )
        assert await bv._relation_filter_labels(bare_req, fg) == {}
    async with _make_client(engine, BookView, InaccessibleAuthorView) as c:
        assert (
            await c.get("/admin/book/list", params={"filter": "author__in=1"})
        ).status_code == 400


class UuidOwner(Base):
    __tablename__ = "relfilter_uuid_owner"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


class UuidItem(Base):
    __tablename__ = "relfilter_uuid_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("relfilter_uuid_owner.id"), nullable=True
    )
    owner: Mapped["UuidOwner | None"] = relationship("UuidOwner")


@pytest.mark.asyncio
async def test_relation_filter_invalid_pks_return_400(engine):
    """Invalid PK strings on relation filters (e.g. `not-a-uuid`, `abc`,
    or wrong composite-PK arity) fail fast with HTTP 400 rather than 500."""
    owner_id = uuid.UUID("01a1766d-a785-7799-b758-cb78e3a272b1")
    with Session(engine) as session:
        owner = UuidOwner(id=owner_id, name="Zara")
        session.add(owner)
        session.add(UuidItem(id=1, title="Item 1", owner=owner))
        session.commit()

    app = Starlette()
    admin = Admin(engine)
    admin.add_view(AuthorView(Author))
    admin.add_view(ModelView(CompositeTag))

    class TagBookView(ModelView):
        fields = ["id", "title", "author", "tag"]

    admin.add_view(TagBookView(Book))
    admin.add_view(ModelView(UuidOwner))
    admin.add_view(ModelView(UuidItem))
    admin.mount_to(app)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        for url, bad_filter in [
            ("/admin/book/list", "author__in=not-an-int"),
            ("/admin/book/list", "author__not_in=1,not-an-int"),
            ("/admin/book/list", "tag__in=only-one-part"),
            ("/admin/uuid-item/list", "owner__in=not-a-uuid"),
        ]:
            res = await c.get(url, params={"filter": bad_filter})
            assert res.status_code == 400, (url, bad_filter, res.status_code)

        ok_uuid = await c.get(
            "/admin/uuid-item/list", params={"filter": f"owner__in={owner_id}"}
        )
        assert ok_uuid.status_code == 200
        assert _list_total(ok_uuid.text) == 1

        ok_comp = await c.get(
            "/admin/book/list", params={"filter": 'tag__in="sci,True"'}
        )
        assert ok_comp.status_code == 200
        assert _list_total(ok_comp.text) == 1

    # Direct filter apply() calls also raise FilterValidationError instead of raw ValueError
    view = ModelView(Book)
    with pytest.raises(FilterValidationError, match="Invalid primary key"):
        RelationInFilter().apply(
            FilterApplyContext(
                query=None, field_name="author", value=["not-an-int"], view=view
            )
        )
    with pytest.raises(FilterValidationError, match="Invalid composite primary key"):
        RelationInFilter().apply(
            FilterApplyContext(
                query=None, field_name="tag", value=["only-one-part"], view=view
            )
        )
