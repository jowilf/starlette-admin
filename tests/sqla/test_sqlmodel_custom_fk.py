"""
Test SQLModel with custom foreign key naming (not following {relation}_id convention).
This test ensures that the FK population fix works for any FK naming pattern.
"""

from datetime import datetime
from typing import List, Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import Engine
from sqlmodel import Field, Relationship, Session, SQLModel, select
from starlette.applications import Starlette
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from tests.sqla.utils import get_test_engine

pytestmark = pytest.mark.asyncio


# Test models with custom FK naming
class Organization(SQLModel, table=True):
    """Organization with custom table name"""

    __tablename__ = "org"

    id: Optional[int] = Field(None, primary_key=True)
    name: str

    members: List["Member"] = Relationship(back_populates="organization")


class Member(SQLModel, table=True):
    """Member with custom FK name (owner_id instead of organization_id)"""

    id: Optional[int] = Field(None, primary_key=True)
    name: str
    joined_date: datetime

    # Custom FK naming: owner_id (NOT organization_id)
    owner_id: int = Field(foreign_key="org.id")
    organization: Optional[Organization] = Relationship(back_populates="members")


class Project(SQLModel, table=True):
    """Project with optional FK - can be cleared to None"""

    id: Optional[int] = Field(None, primary_key=True)
    name: str

    # Optional FK - can be set to None
    org_ref: Optional[int] = Field(None, foreign_key="org.id")
    organization: Optional[Organization] = Relationship()


@pytest.fixture
def engine() -> Engine:
    _engine = get_test_engine()
    SQLModel.metadata.create_all(_engine)
    yield _engine
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(Organization))
    admin.add_view(ModelView(Member))
    admin.add_view(ModelView(Project))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


async def test_create_with_custom_fk_naming(client: AsyncClient, session: Session):
    """
    Test creating Member with custom FK naming (owner_id).
    This verifies that the FK population works for any FK naming pattern.
    """
    # Setup: Create an organization
    org = Organization(name="Acme Corp")
    session.add(org)
    session.commit()

    # Test: Create member with custom FK name
    response = await client.post(
        "/admin/member/create",
        data={
            "name": "Alice Johnson",
            "joined_date": datetime(2024, 1, 15).isoformat(),
            "organization": org.id,  # Relationship field
        },
        follow_redirects=False,
    )

    # Should succeed (303 redirect)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}"

    # Verify in database
    # In MySQL with REPEATABLE READ isolation, we need to end the current
    # transaction to see changes committed by the app session
    session.commit()
    stmt = select(Member).where(Member.name == "Alice Johnson")
    member = session.exec(stmt).one()
    assert member is not None
    assert member.owner_id == org.id  # FK column should be populated
    assert member.organization.name == "Acme Corp"  # Relationship should work


async def test_edit_with_custom_fk_naming(client: AsyncClient, session: Session):
    """
    Test editing Member with custom FK naming.
    """
    # Setup
    org1 = Organization(id=1, name="Acme Corp")
    org2 = Organization(id=2, name="Beta Inc")
    member = Member(
        id=1,
        name="Bob Smith",
        joined_date=datetime(2024, 1, 1),
        owner_id=1,
    )
    session.add_all([org1, org2, member])
    session.commit()

    # Test: Edit member to change organization
    response = await client.post(
        "/admin/member/edit/1",
        data={
            "name": "Bob Smith",
            "joined_date": datetime(2024, 1, 1).isoformat(),
            "organization": 2,  # Change to org2
        },
        follow_redirects=False,
    )

    # Should succeed
    assert response.status_code == 303

    # Verify FK updated
    session.expire(member)
    session.refresh(member)
    assert member.owner_id == 2
    assert member.organization.name == "Beta Inc"


async def test_create_with_optional_custom_fk(client: AsyncClient, session: Session):
    """
    Test that optional FK with custom naming also works.
    """
    # Create member without organization (optional FK)
    response = await client.post(
        "/admin/member/create",
        data={
            "name": "Charlie Brown",
            "joined_date": datetime(2024, 1, 20).isoformat(),
            # organization not provided (would be optional if FK was optional)
        },
        follow_redirects=False,
    )

    # This will fail because owner_id is required (int, not Optional[int])
    # But this is expected behavior - the FK is correctly being validated
    assert response.status_code == 422  # Validation error expected


async def test_nonexistent_relationship_id(client: AsyncClient, session: Session):
    """
    Test submitting a non-existent relationship ID triggers the else branch in
    _populate_fk_columns (find_by_pk returns None) and results in a 422.

    Note: clearing a relationship through the UI works correctly — select2 omits
    the field entirely, parse_form_data returns None, and _arrange_data sets the
    relationship to None without ever calling _populate_fk_columns.
    """
    project = Project(name="Alpha Project")
    session.add(project)
    session.commit()
    project_id = project.id

    # Submit a relationship ID that does not exist in the DB
    response = await client.post(
        f"/admin/project/edit/{project_id}",
        data={
            "name": "Alpha Project",
            "organization": "99999",  # non-existent ID -> find_by_pk returns None
        },
        follow_redirects=False,
    )

    # find_by_pk returns None -> else branch sets org_ref=None ->
    # Pydantic accepts Optional[int]=None -> saves with org_ref=None
    assert response.status_code == 303

    session.commit()
    session.expire(project)
    stmt = select(Project).where(Project.id == project_id)
    updated_project = session.exec(stmt).one()
    assert updated_project.org_ref is None
    assert updated_project.organization is None
