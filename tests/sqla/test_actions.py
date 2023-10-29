from typing import Any, List, Optional

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.sqla.utils import get_test_engine

Base = declarative_base()


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)


class ArticleView(ModelView):
    def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        # simulate MultipleResultsFound error
        request.state.session.execute(
            select(Article).where(Article.title == "test")
        ).one()


@pytest.fixture
def engine(fake_image) -> Engine:
    engine = get_test_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Article(title="test"))
        session.add(Article(title="test"))
        session.commit()
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(engine: Engine) -> TestClient:
    admin = Admin(engine)
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    return TestClient(app, base_url="http://testserver")


def test_sqlalchemyerror_in_action(client: TestClient):
    response = client.post(
        "/admin/api/article/action", params={"name": "delete", "pks": [1, 2]}
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Multiple rows were found when exactly one was required"
    )


def test_sqlalchemyerror_in_row_action(client: TestClient):
    response = client.post(
        "/admin/api/article/row-action", params={"name": "delete", "pk": 2}
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Multiple rows were found when exactly one was required"
    )
