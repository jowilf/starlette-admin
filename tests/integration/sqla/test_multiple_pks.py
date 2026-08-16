import pytest
import pytest_asyncio
from httpx2 import AsyncClient
from sqlalchemy import Boolean, Integer, String, and_, select, true
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.contrib.sqla.fields import MultiplePKField

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "record"

    id1: Mapped[str] = mapped_column(String(20), primary_key=True)
    id2: Mapped[int] = mapped_column(Integer, primary_key=True)
    id3: Mapped[bool] = mapped_column(Boolean, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


@pytest.fixture
def engine() -> Engine:
    _engine = get_test_engine()
    Base.metadata.create_all(_engine)
    with Session(_engine) as session:
        session.add(Record(id1="first,record", id2=1, id3=False, name="1st record"))
        session.add(Record(id1="third,record", id2=3, id3=True, name="3rd record"))
        session.commit()
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(Record))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with csrf_async_client(app) as c:
        yield c


async def test_pk_field(session: Session):
    view = ModelView(Record)

    assert isinstance(view.pk_field, MultiplePKField)
    assert view.pk_field.name == "id1,id2,id3"


async def test_load_creation_form(client: AsyncClient, session: Session):
    response = await client.get("/admin/record/create")
    assert response.status_code == 200


async def test_find_by_pks(client: AsyncClient, session: Session):
    response = await client.get(
        "/admin/_api/record/relation-lookup",
        params={"pks": ["first.,record,1,False", "third.,record,3,True"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert {"1st record", "3rd record"} == {x["name"] for x in data["items"]}


async def test_create(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/record/create",
        data={
            "id1": "second.record",
            "id2": 2,
            "id3": "on",
            "name": "2nd record",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    stmt = select(Record).where(
        and_(
            Record.id1 == "second.record",
            Record.id2 == 2,
            Record.id3 == true(),
        )
    )
    record = session.execute(stmt).scalar_one()
    assert record is not None
    assert record.name == "2nd record"


async def test_load_edit_form(client: AsyncClient, session: Session):
    response = await client.get("/admin/record/edit?pk=first.,record,1,False")
    assert response.status_code == 200


async def test_edit_view(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/record/edit?pk=first.,record,1,False",
        data={
            "id1": "edited,record",
            "id2": 4,
            "id3": "on",
            "name": "Edited Record",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    stmt = select(Record).where(
        and_(
            Record.id1 == "edited,record",
            Record.id2 == 4,
            Record.id3 == true(),
        )
    )
    record = session.execute(stmt).scalar_one()
    assert record is not None
    assert record.name == "Edited Record"
