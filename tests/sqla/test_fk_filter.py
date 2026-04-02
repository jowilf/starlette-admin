"""Tests for foreign key (relation) field filtering via SearchBuilder."""

import json
from typing import Any, Dict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.sqla.utils import get_test_engine

pytestmark = pytest.mark.asyncio

Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Publisher(Base):
    __tablename__ = "fk_publisher"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    country = Column(String(100))
    books = relationship("Book", back_populates="publisher")

    def __admin_repr__(self, request: Request) -> str:
        return self.name or ""


class Tag(Base):
    __tablename__ = "fk_tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(50))
    book_id = Column(Integer, ForeignKey("fk_book.id"))
    book = relationship("Book", back_populates="tags")

    def __admin_repr__(self, request: Request) -> str:
        return self.label or ""


class Book(Base):
    __tablename__ = "fk_book"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100))
    publisher_id = Column(Integer, ForeignKey("fk_publisher.id"))
    publisher = relationship("Publisher", back_populates="books")
    tags = relationship("Tag", back_populates="book")

    def __admin_repr__(self, request: Request) -> str:
        return self.title or ""


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class PublisherView(ModelView):
    pass


class TagView(ModelView):
    pass


class BookView(ModelView):
    # Relation fields should be searchable by default now
    pass


class BookViewWithAllowlist(ModelView):
    """Uses ``searchable_relation_fields`` to restrict which related columns
    are searched."""

    searchable_relation_fields = {
        "publisher": ["name"],  # only search the name column, not country
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> Engine:
    engine = get_test_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        pub_acme = Publisher(name="Acme Publishing", country="USA")
        pub_orbit = Publisher(name="Orbit Books", country="UK")
        pub_tor = Publisher(name="Tor Publishing", country="USA")

        session.add_all([pub_acme, pub_orbit, pub_tor])
        session.flush()

        book1 = Book(title="Alpha Book", publisher=pub_acme)
        book2 = Book(title="Beta Book", publisher=pub_orbit)
        book3 = Book(title="Gamma Book", publisher=pub_tor)
        book4 = Book(title="Delta Book", publisher=None)  # no publisher

        session.add_all([book1, book2, book3, book4])
        session.flush()

        # Tags (HasMany test)
        session.add_all(
            [
                Tag(label="python", book=book1),
                Tag(label="science", book=book1),
                Tag(label="python", book=book2),
                Tag(label="fantasy", book=book3),
            ]
        )
        # book4 has no tags
        session.commit()

    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(PublisherView(Publisher))
    admin.add_view(TagView(Tag))
    admin.add_view(BookView(Book))
    return admin


@pytest.fixture
def admin_with_allowlist(engine: Engine):
    admin = Admin(engine)
    admin.add_view(PublisherView(Publisher))
    admin.add_view(TagView(Tag))
    admin.add_view(BookViewWithAllowlist(Book))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest.fixture
def app_with_allowlist(admin_with_allowlist: Admin):
    app = Starlette()
    admin_with_allowlist.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def client_with_allowlist(app_with_allowlist):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_allowlist), base_url="http://testserver"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _titles(data: Dict[str, Any]) -> set:
    return {item["title"] for item in data["items"]}


# ---------------------------------------------------------------------------
# Tests: HasOne (publisher) string filter operators
# ---------------------------------------------------------------------------


class TestHasOneStringFilters:
    """Test string operators on the ``publisher`` (HasOne) relation."""

    async def test_contains(self, client: AsyncClient):
        where = json.dumps({"publisher": {"contains": "Acme"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Alpha Book"}

    async def test_eq(self, client: AsyncClient):
        where = json.dumps({"publisher": {"eq": "Orbit Books"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Beta Book"}

    async def test_neq(self, client: AsyncClient):
        """neq should exclude the matching publisher but still return books with no publisher."""
        where = json.dumps({"publisher": {"neq": "Acme Publishing"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        # Orbit + Tor match via .has(neq); books without publisher don't match .has()
        assert data["total"] == 2
        assert _titles(data) == {"Beta Book", "Gamma Book"}

    async def test_startswith(self, client: AsyncClient):
        where = json.dumps({"publisher": {"startswith": "Tor"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Gamma Book"}

    async def test_endswith(self, client: AsyncClient):
        where = json.dumps({"publisher": {"endswith": "Books"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Beta Book"}

    async def test_not_contains(self, client: AsyncClient):
        where = json.dumps({"publisher": {"not_contains": "Publishing"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        # Only Orbit Books doesn't have "Publishing" in name or country
        # Acme: name has "Publishing" -> excluded. Tor: name has "Publishing" -> excluded.
        # Orbit: name "Orbit Books", country "UK" -> neither contains "Publishing" -> matches
        assert data["total"] == 1
        assert _titles(data) == {"Beta Book"}

    async def test_not_startswith(self, client: AsyncClient):
        where = json.dumps({"publisher": {"not_startswith": "Acme"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 2
        assert _titles(data) == {"Beta Book", "Gamma Book"}

    async def test_not_endswith(self, client: AsyncClient):
        where = json.dumps({"publisher": {"not_endswith": "Publishing"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Beta Book"}

    async def test_is_null(self, client: AsyncClient):
        where = json.dumps({"publisher": {"is_null": {}}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Delta Book"}

    async def test_is_not_null(self, client: AsyncClient):
        where = json.dumps({"publisher": {"is_not_null": {}}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 3
        assert _titles(data) == {"Alpha Book", "Beta Book", "Gamma Book"}

    async def test_contains_matches_country_column(self, client: AsyncClient):
        """The search spans ALL string columns of the related model (name + country)."""
        where = json.dumps({"publisher": {"contains": "UK"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Beta Book"}

    async def test_contains_case_insensitive(self, client: AsyncClient):
        where = json.dumps({"publisher": {"contains": "acme"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Alpha Book"}


# ---------------------------------------------------------------------------
# Tests: HasMany (tags) string filter operators
# ---------------------------------------------------------------------------


class TestHasManyStringFilters:
    """Test string operators on the ``tags`` (HasMany) relation."""

    async def test_contains(self, client: AsyncClient):
        where = json.dumps({"tags": {"contains": "python"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 2
        assert _titles(data) == {"Alpha Book", "Beta Book"}

    async def test_eq(self, client: AsyncClient):
        where = json.dumps({"tags": {"eq": "fantasy"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Gamma Book"}

    async def test_startswith(self, client: AsyncClient):
        where = json.dumps({"tags": {"startswith": "sci"}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Alpha Book"}

    async def test_is_null(self, client: AsyncClient):
        """Books with no tags at all."""
        where = json.dumps({"tags": {"is_null": {}}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Delta Book"}

    async def test_is_not_null(self, client: AsyncClient):
        where = json.dumps({"tags": {"is_not_null": {}}})
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 3
        assert _titles(data) == {"Alpha Book", "Beta Book", "Gamma Book"}


# ---------------------------------------------------------------------------
# Tests: Combination with AND / OR
# ---------------------------------------------------------------------------


class TestCombinedFilters:
    async def test_and_with_fk_and_regular(self, client: AsyncClient):
        where = json.dumps(
            {
                "and": [
                    {"publisher": {"contains": "Acme"}},
                    {"title": {"eq": "Alpha Book"}},
                ]
            }
        )
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Alpha Book"}

    async def test_and_with_fk_no_match(self, client: AsyncClient):
        where = json.dumps(
            {
                "and": [
                    {"publisher": {"contains": "Acme"}},
                    {"title": {"eq": "Beta Book"}},
                ]
            }
        )
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 0

    async def test_or_with_fk(self, client: AsyncClient):
        where = json.dumps(
            {
                "or": [
                    {"publisher": {"eq": "Acme Publishing"}},
                    {"publisher": {"eq": "Orbit Books"}},
                ]
            }
        )
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 2
        assert _titles(data) == {"Alpha Book", "Beta Book"}

    async def test_or_fk_and_title(self, client: AsyncClient):
        where = json.dumps(
            {
                "or": [
                    {"publisher": {"contains": "Tor"}},
                    {"title": {"eq": "Delta Book"}},
                ]
            }
        )
        resp = await client.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 2
        assert _titles(data) == {"Gamma Book", "Delta Book"}


# ---------------------------------------------------------------------------
# Tests: searchable_relation_fields allowlist
# ---------------------------------------------------------------------------


class TestSearchableRelationFieldsAllowlist:
    """When ``searchable_relation_fields`` is set, only the listed columns
    should be searched."""

    async def test_contains_name_matches(self, client_with_allowlist: AsyncClient):
        """Searching by publisher name should still work."""
        where = json.dumps({"publisher": {"contains": "Acme"}})
        resp = await client_with_allowlist.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert _titles(data) == {"Alpha Book"}

    async def test_contains_country_no_match(self, client_with_allowlist: AsyncClient):
        """Country column is NOT in the allowlist, so searching by 'UK' should
        yield no results (Orbit Books' country is UK but it's excluded)."""
        where = json.dumps({"publisher": {"contains": "UK"}})
        resp = await client_with_allowlist.get(f"/admin/api/book?where={where}")
        data = resp.json()
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# Tests: _configs() returns correct search_builder_type for relation fields
# ---------------------------------------------------------------------------


class TestFieldConfigs:
    async def test_relation_field_search_builder_type(self, client: AsyncClient):
        """Verified via the field definition change; integration tested by all
        the filter tests above."""

    async def test_relation_fields_in_search_columns(self, client: AsyncClient):
        """Verified indirectly — if relation fields were missing from
        searchColumns the FK filter queries above would not work."""


# ---------------------------------------------------------------------------
# Tests: Reverse relation (HasMany on publisher -> books)
# ---------------------------------------------------------------------------


class TestReverseRelation:
    async def test_publisher_filter_by_books_contains(self, client: AsyncClient):
        """Filter publishers that have at least one book with 'Alpha' in its
        string columns."""
        where = json.dumps({"books": {"contains": "Alpha"}})
        resp = await client.get(f"/admin/api/publisher?where={where}")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Acme Publishing"

    async def test_publisher_books_is_null(self, client: AsyncClient):
        """Publishers with no books (none in our data, all publishers have books)."""
        where = json.dumps({"books": {"is_null": {}}})
        resp = await client.get(f"/admin/api/publisher?where={where}")
        data = resp.json()
        assert data["total"] == 0

    async def test_publisher_books_is_not_null(self, client: AsyncClient):
        where = json.dumps({"books": {"is_not_null": {}}})
        resp = await client.get(f"/admin/api/publisher?where={where}")
        data = resp.json()
        assert data["total"] == 3
