from datetime import date, datetime, time
from typing import Optional

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel import Field, Session, SQLModel
from starlette.applications import Starlette
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from tests.sqla.utils import get_test_engine

engine = get_test_engine()


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(None, primary_key=True)
    todo: str = Field(min_length=10)
    completed: Optional[bool]
    deadline: datetime
    completed_date: Optional[date]
    completed_time: Optional[time]


class TestSQLModel:
    def setup(self) -> None:
        SQLModel.metadata.create_all(engine)

    def teardown(self):
        SQLModel.metadata.drop_all(engine)

    @pytest.fixture
    def admin(self):
        admin = Admin(engine)
        admin.add_view(ModelView(Todo))
        return admin

    @pytest.fixture
    def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        async with AsyncClient(app=app, base_url="http://testserver") as c:
            yield c

    @pytest.mark.asyncio
    async def test_create(self, client: AsyncClient):
        with Session(engine) as session:
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
            assert session.get(Todo, 1) is not None

    @pytest.mark.asyncio
    async def test_validation_error(self, client: AsyncClient):
        with Session(engine) as session:
            response = await client.post(
                "/admin/todo/create",
                data={
                    "todo": "Do some",
                    "completed_date": date.today().isoformat(),
                    "completed_time": datetime.now().strftime("%H:%M:%S"),
                },
            )
            assert response.status_code == 200
            assert (
                '<div class="invalid-feedback">ensure this value has at least 10'
                " characters</div>" in response.text
            )
            assert (
                '<div class="invalid-feedback">none is not an allowed value</div>'
                in response.text
            )
            todo = Todo(todo="Do some magic", deadline=datetime.now())
            session.add(todo)
            session.commit()
            session.refresh(todo)

            response = await client.get(f"/admin/todo/edit/{todo.id}")
            assert response.status_code == 200

            response = await client.post(
                f"/admin/todo/edit/{todo.id}",
                data={
                    "todo": "Do some",
                    "completed_date": date.today().isoformat(),
                    "completed_time": datetime.now().strftime("%H:%M:%S"),
                },
            )
            assert response.status_code == 200
            assert (
                '<div class="invalid-feedback">ensure this value has at least 10'
                " characters</div>" in response.text
            )
            assert (
                '<div class="invalid-feedback">none is not an allowed value</div>'
                in response.text
            )
