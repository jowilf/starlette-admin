import enum
from typing import Any, List

import pytest
from requests import Request
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, EnumField, IntegerField, action
from starlette_admin.exceptions import ActionFailed

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Status(str, enum.Enum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class Article(DummyBaseModel):
    status: Status


class ArticleView(DummyModelView):
    model = Article
    fields = [IntegerField("id"), EnumField("status", enum=Status)]
    actions = [
        "make_published",
        "delete",
        "always_failed",
        "forbidden",
    ]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "forbidden":
            return False
        return await super().is_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
        return "{} articles were successfully marked as published".format(len(pks))

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(self, request: Request, pks: List[Any]) -> str:
        raise ActionFailed("Sorry, We can't proceed this action now.")

    @action(
        name="forbidden",
        text="Forbidden action",
    )
    async def forbidden_action(self, request: Request, pks: List[Any]) -> str:
        raise NotImplementedError


@pytest.fixture
def client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView)
    admin.mount_to(app)

    ArticleView.db = {
        1: Article(id=1, status=Status.Draft),
        2: Article(id=2, status=Status.Withdrawn),
        3: Article(id=3, status=Status.Draft),
    }
    return TestClient(app, base_url="http://testserver")


def test_all_actions_is_available_by_default():
    class DefaultActionArticleView(ArticleView):
        actions = None

    assert sorted(DefaultActionArticleView().actions) == sorted(
        ["make_published", "delete", "always_failed", "forbidden"]
    )


@pytest.mark.parametrize(
    "action, expected_count",
    [
        ("make_published", 1),
        ("delete", 1),
        ("always_failed", 1),
        ("forbidden", 0),
    ],
)
def test_actions_is_available_in_ui(client: TestClient, action, expected_count):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    assert response.text.count(f'data-name="{action}"') == expected_count


def test_action_execution(client: TestClient):
    response = client.post(
        "/admin/api/article/action", params={"name": "make_published", "pks": [2, 3]}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "2 articles were successfully marked as published"
    assert ArticleView.db[1].status == Status.Draft
    assert ArticleView.db[2].status == Status.Published
    assert ArticleView.db[3].status == Status.Published


def test_failed_action(client: TestClient):
    response = client.post(
        "/admin/api/article/action", params={"name": "always_failed", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Sorry, We can't proceed this action now."


def test_forbidden_action(client: TestClient):
    response = client.post(
        "/admin/api/article/action", params={"name": "forbidden", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


def test_invalid_action(client: TestClient):
    response = client.post(
        "/admin/api/article/action", params={"name": "invalid", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Invalid action"


def test_invalid_action_list():
    class InvalidArticleView(ArticleView):
        actions = ["invalid"]

    with pytest.raises(ValueError, match="Unknown action with name `invalid`"):
        InvalidArticleView()
