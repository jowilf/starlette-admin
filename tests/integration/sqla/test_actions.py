from typing import Any

import pytest
from sqlalchemy import Integer, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import CsrfTestClient


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)


class ArticleView(ModelView):
    def delete(self, request: Request, pks: list[Any]) -> int | None:
        # simulate MultipleResultsFound error
        request.state.session.execute(
            select(Article).where(Article.title == "test")
        ).one()


@pytest.fixture
def engine(fake_image, sqla_backend) -> Engine:
    engine = get_test_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Article(title="test"))
        session.add(Article(title="test"))
        session.commit()
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(engine: Engine) -> CsrfTestClient:
    admin = Admin(engine)
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    return CsrfTestClient(app, base_url="http://testserver")


def test_sqlalchemyerror_in_action(client: CsrfTestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "delete", "pks": [1, 2]}
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Multiple rows were found when exactly one was required"
    )


def test_sqlalchemyerror_in_row_action(client: CsrfTestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "delete", "pk": 2}
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Multiple rows were found when exactly one was required"
    )
