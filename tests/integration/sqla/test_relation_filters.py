"""End-to-end tests for filtering the SQLAlchemy list page by relation fields
(`HasOne`/`HasMany`): the filter builder offers them (with a relation-lookup
record picker), the `filter` query param is applied, and active-filter pills
show the selected records' labels rather than their raw primary keys.
"""

import json
import re
from typing import Any, ClassVar

import pytest
import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import ForeignKey, Integer, String, create_engine, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import StringField
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView
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


class Book(Base):
    __tablename__ = "relfilter_book"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    author_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("relfilter_author.id"), nullable=True
    )
    author: Mapped["Author | None"] = relationship("Author", back_populates="books")

    @property
    def slug(self) -> str:
        return self.title.lower()

    @hybrid_property
    def title_lower(self) -> str:
        return self.title.lower()

    @title_lower.inplace.expression
    @classmethod
    def _title_lower_expression(cls) -> Any:
        return func.lower(cls.title)


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


class DerivedFieldsBookView(ModelView):
    fields = [
        "id",
        "title",
        StringField("slug", exclude_from_create=True, exclude_from_edit=True),
        StringField("title_lower", exclude_from_create=True, exclude_from_edit=True),
    ]


class TitleOnlyBookView(ModelView):
    fields = ["id", "title", "author"]
    filterable_fields = ["title"]


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
        session.add_all([alice, bob])
        session.add_all(
            [
                Book(id=1, title="A1", author=alice),
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
async def test_builder_offers_relation_fields(client: AsyncClient):
    response = await client.get("/admin/book/list")
    assert response.status_code == 200
    fields = {f["name"]: f for f in _builder_fields(response.text)}
    author = fields["author"]
    assert {f["name"] for f in author["filters"]} == {
        "in",
        "not_in",
        "is_null",
        "is_not_null",
    }
    assert author["relation"]["pk"] == "id"
    assert author["relation"]["url"].endswith("/admin/_api/author/relation-lookup")


@pytest.mark.asyncio
async def test_builder_offers_to_many_relation(client: AsyncClient):
    response = await client.get("/admin/author/list")
    fields = {f["name"]: f for f in _builder_fields(response.text)}
    assert {f["name"] for f in fields["books"]["filters"]} == {
        "any_of",
        "none_of",
        "is_null",
        "is_not_null",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filter_str", "expected"),
    [
        ("author__in=1", 2),
        ("author__in=1,2", 3),
        ("author__not_in=1", 2),  # Bob's book + the orphan
        ("author__is_null", 1),
        ("author__in=1 AND title__contains=2", 1),
    ],
)
async def test_filter_books_by_author(client: AsyncClient, filter_str, expected):
    response = await client.get("/admin/book/list", params={"filter": filter_str})
    assert response.status_code == 200
    assert _list_total(response.text) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filter_str", "expected"),
    [
        ("books__any_of=1", 1),
        ("books__any_of=1,3", 2),
        ("books__none_of=3", 1),
        ("books__none_of=1,3", 0),
    ],
)
async def test_filter_authors_by_books(client: AsyncClient, filter_str, expected):
    response = await client.get("/admin/author/list", params={"filter": filter_str})
    assert response.status_code == 200
    assert _list_total(response.text) == expected


@pytest.mark.asyncio
async def test_active_filter_pill_shows_record_label(client: AsyncClient):
    response = await client.get("/admin/book/list", params={"filter": "author__in=1,2"})
    assert response.status_code == 200
    assert "Writer Alice" in response.text
    assert "Writer Bob" in response.text


@pytest.mark.asyncio
async def test_invalid_relation_filter_value_rejected(client: AsyncClient):
    response = await client.get("/admin/book/list", params={"filter": "author__in="})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_filterable_fields_restricts_builder(engine):
    async with _make_client(engine, TitleOnlyBookView) as c:
        response = await c.get("/admin/book/list")
        names = {f["name"] for f in _builder_fields(response.text)}
        assert names == {"title"}
        response = await c.get("/admin/book/list", params={"filter": "author__in=1"})
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_pill_labels_resolved_under_relation_lookup_action(engine):
    """Pill labels are fetched like the record picker's own lookup, so the
    foreign view does not eager-load its relations for a LIST request."""
    RecordingAuthorView.actions_seen = []
    async with _make_client(engine, BookView, RecordingAuthorView) as c:
        response = await c.get("/admin/book/list", params={"filter": "author__in=1"})
    assert response.status_code == 200
    assert "Writer Alice" in response.text
    assert RecordingAuthorView.actions_seen == [RequestAction.RELATION_LOOKUP]


@pytest.mark.asyncio
async def test_property_backed_field_is_not_filterable(engine):
    """A field backed by a plain Python `property` cannot be queried, so it
    is not offered (and rejected); a `hybrid_property` still is."""
    async with _make_client(engine, DerivedFieldsBookView) as c:
        response = await c.get("/admin/book/list")
        names = {f["name"] for f in _builder_fields(response.text)}
        assert "slug" not in names
        assert {"title", "title_lower"} <= names

        response = await c.get(
            "/admin/book/list", params={"filter": "slug__contains=a"}
        )
        assert response.status_code == 400

        response = await c.get(
            "/admin/book/list", params={"filter": "title_lower__contains=a1"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1
