from datetime import date, datetime, time
from typing import Optional

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

from tests.sqla.utils import get_test_engine

pytestmark = pytest.mark.asyncio

Base = declarative_base()


class IDMixin:
    id = Column(Integer, primary_key=True)


class User(Base, IDMixin):
    __tablename__ = "user"

    name = Column(String(100))

    todos = relationship("Todo", back_populates="user", collection_class=set)


class Todo(Base, IDMixin):
    __tablename__ = "todo"

    todo = Column(String(255))
    completed = Column(Boolean)
    deadline = Column(DateTime)
    completed_date = Column(Date)
    completed_time = Column(Time)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="todos")


class UserIn(BaseModel):
    id: Optional[int] = Field(None, primary_key=True)
    name: str = Field(max_length=100)


class TodoIn(BaseModel):
    id: Optional[int] = Field(None, primary_key=True)
    todo: str = Field(min_length=10)
    completed: Optional[bool]
    deadline: datetime
    completed_date: Optional[date]
    completed_time: Optional[time]


@pytest.fixture
def engine() -> Engine:
    _engine = get_test_engine()
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(User, pydantic_model=UserIn))
    admin.add_view(ModelView(Todo, pydantic_model=TodoIn))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_create(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do something nice for someone I care about",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do something nice for someone I care about")
    todo = session.execute(stmt).scalar_one()
    assert todo is not None


async def test_create_validation_error(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do some",
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">ensure this value has at least 10'
        " characters</div>" in response.text
        or '<div class="invalid-feedback">String should have at least 10'  # pydantic v2
        " characters</div>" in response.text
    )
    assert (
        '<div class="invalid-feedback">none is not an allowed value</div>'
        in response.text
        or '<div class="invalid-feedback">Input should be a valid datetime</div>'  # pydantic v2
        in response.text
    )


async def test_edit(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.get("/admin/todo/edit/1")
    assert response.status_code == 200

    response = await client.post(
        "/admin/todo/edit/1",
        data={
            "todo": "End magic things",
            "deadline": datetime(2022, 2, 1).isoformat(),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "End magic things")
    todo = session.execute(stmt).scalar_one()
    assert todo is not None
    assert todo.id == 1
    assert todo.deadline == datetime(2022, 2, 1)


async def test_edit_validation_error(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.post(
        "/admin/todo/edit/1",
        data={
            "todo": "Do some",
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">ensure this value has at least 10'
        " characters</div>" in response.text
        or '<div class="invalid-feedback">String should have at least 10'  # pydantic v2
        " characters</div>" in response.text
    )
    assert (
        '<div class="invalid-feedback">none is not an allowed value</div>'
        in response.text
        or '<div class="invalid-feedback">Input should be a valid datetime</div>'  # pydantic v2
        in response.text
    )


async def test_delete(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.post(
        "/admin/api/todo/action", params={"name": "delete", "pks": [1]}
    )
    assert response.status_code == 200
    assert session.get(Todo, 1) is None


async def test_create_with_has_one_relationships(client: AsyncClient, session: Session):
    session.add(User(name="John Doe"))
    session.commit()

    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do something nice for someone I care about",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
            "user": 1,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do something nice for someone I care about")
    todo = session.execute(stmt).scalar_one()
    assert todo.user.name == "John Doe"


async def test_edit_with_has_one_relationships(client: AsyncClient, session: Session):
    session.add(
        Todo(
            todo="Do some magic",
            deadline=datetime(2022, 1, 1),
            user=User(id=1, name="John Doe"),
        )
    )
    session.add(User(id=2, name="Tommy Sharp"))
    session.commit()

    response = await client.post(
        "/admin/todo/edit/1",
        data={
            "todo": "Do some magic",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
            "user": 2,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do some magic")
    todo = session.execute(stmt).scalar_one()
    assert todo.user.name == "Tommy Sharp"


async def test_create_with_has_many_relationships(
    client: AsyncClient, session: Session
):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.add(Todo(todo="Do something nice", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.post(
        "/admin/user/create",
        data={"name": "John Doe", "todos": [1, 2]},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(User).where(User.name == "John Doe")
    user = session.execute(stmt).scalar_one()
    assert len(user.todos) == 2
    assert sorted([t.todo for t in user.todos]) == [
        "Do some magic",
        "Do something nice",
    ]
