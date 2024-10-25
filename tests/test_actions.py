import enum
from typing import Any

import pytest
from requests import Request
from starlette.applications import Starlette
from starlette.responses import RedirectResponse, Response
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, EnumField, IntegerField, action
from starlette_admin.actions import row_action
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
        "invalid_redirect",
        "redirect",
    ]
    row_actions = [
        "view",
        "edit",
        "delete",
        "always_failed",
        "forbidden",
        "invalid_redirect",
        "redirect",
        "make_published",
    ]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "forbidden":
            return False
        return await super().is_action_allowed(request, name)

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "forbidden":
            return False
        return await super().is_row_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> str:
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
        return f"{len(pks)} articles were successfully marked as published"

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        article = await self.find_by_pk(request, pk)
        article.status = Status.Published
        return "The article was successfully marked as published"

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(self, request: Request, pks: list[Any]) -> str:
        raise ActionFailed("Sorry, We can't proceed this action now.")

    @row_action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_row_action(self, request: Request, pk: Any) -> str:
        raise ActionFailed("Sorry, We can't proceed this action now.")

    @action(
        name="forbidden",
        text="Forbidden action",
    )
    async def forbidden_action(self, request: Request, pks: list[Any]) -> str:
        raise NotImplementedError

    @row_action(
        name="forbidden",
        text="Forbidden row action",
    )
    async def forbidden_row_action(self, request: Request, pk: Any) -> str:
        raise NotImplementedError

    @action(
        name="invalid_redirect",
        text="Invalid Redirection",
    )
    async def invalid_redirect_action(
        self, request: Request, pks: list[Any]
    ) -> Response:
        # Missing `custom_response=True`
        return RedirectResponse("https://example.com/")

    @row_action(
        name="invalid_redirect",
        text="Invalid Redirection",
    )
    async def invalid_redirect_row_action(self, request: Request, pk: Any) -> Response:
        # Missing `custom_response=True`
        return RedirectResponse("https://example.com/")

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
    )
    async def redirect_action(self, request: Request, pks: list[Any]) -> Response:
        return RedirectResponse("https://example.com/")

    @row_action(
        name="redirect",
        text="Redirect",
        custom_response=True,
    )
    async def redirect_row_action(self, request: Request, pks: list[Any]) -> Response:
        return RedirectResponse("https://example.com/")


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


def test_all_actions_are_available_by_default():
    class DefaultActionArticleView(ArticleView):
        actions = None

    assert sorted(DefaultActionArticleView().actions) == sorted(
        [
            "make_published",
            "delete",
            "always_failed",
            "forbidden",
            "invalid_redirect",
            "redirect",
        ]
    )


def test_all_row_actions_are_available_by_default():
    class DefaultActionArticleView(ArticleView):
        row_actions = None

    assert sorted(DefaultActionArticleView().row_actions) == sorted(
        [
            "always_failed",
            "delete",
            "edit",
            "forbidden",
            "invalid_redirect",
            "make_published",
            "redirect",
            "view",
        ]
    )


@pytest.mark.parametrize(
    "action, expected_count",
    [
        ("make_published", 1),
        ("delete", 1),
        ("always_failed", 1),
        ("forbidden", 0),
        ("redirect", 1),
    ],
)
def test_actions_are_available_in_ui(client: TestClient, action, expected_count):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    assert response.text.count(f'data-name="{action}"') == expected_count


@pytest.mark.parametrize(
    "row_action, expected_count",
    [
        ("edit", 1),
        ("view", 1),
        ("make_published", 1),
        ("delete", 1),
        ("always_failed", 1),
        ("forbidden", 0),
        ("redirect", 1),
    ],
)
def test_row_actions_are_available_in_api_meta_data(
    client: TestClient, row_action, expected_count
):
    response = client.get("/admin/api/article")
    assert response.status_code == 200
    assert (
        response.json()["items"][0]["_meta"]["rowActions"].count(
            f'data-name="{row_action}"'
        )
        == expected_count
    )


def test_action_execution(client: TestClient):
    response = client.get(
        "/admin/api/article/action", params={"name": "make_published", "pks": [2, 3]}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "2 articles were successfully marked as published"
    for id, status in [
        (1, Status.Draft),
        (2, Status.Published),
        (3, Status.Published),
    ]:
        assert ArticleView.db[id].status == status


def test_row_action_execution(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action", params={"name": "make_published", "pk": 2}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "The article was successfully marked as published"
    assert ArticleView.db[2].status == Status.Published


def test_failed_action(client: TestClient):
    response = client.get(
        "/admin/api/article/action", params={"name": "always_failed", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Sorry, We can't proceed this action now."


def test_failed_row_action(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action", params={"name": "always_failed", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Sorry, We can't proceed this action now."


def test_forbidden_action(client: TestClient):
    response = client.get(
        "/admin/api/article/action", params={"name": "forbidden", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


def test_forbidden_row_action(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action", params={"name": "forbidden", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


def test_invalid_action(client: TestClient):
    response = client.get(
        "/admin/api/article/action", params={"name": "invalid", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Invalid action"


def test_invalid_row_action(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action", params={"name": "invalid", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Invalid row action"


def test_delete_row_action(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action", params={"name": "delete", "pk": 2}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Item was successfully deleted"
    assert ArticleView.db.get(2, None) is None


def test_custom_response_for_batch_actions(client: TestClient):
    response = client.get(
        "/admin/api/article/action",
        params={"name": "redirect", "pks": [2, 3]},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


def test_custom_response_for_row_actions(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action",
        params={"name": "redirect", "pk": 2},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


def test_invalid_custom_response_for_batch_actions(client: TestClient):
    response = client.get(
        "/admin/api/article/action",
        params={"name": "invalid_redirect", "pks": [2, 3]},
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Set custom_response to true, to be able to return custom response"
    )


def test_invalid_custom_response_for_row_actions(client: TestClient):
    response = client.get(
        "/admin/api/article/row-action",
        params={"name": "invalid_redirect", "pk": 2},
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Set custom_response to true, to be able to return custom response"
    )


def test_invalid_action_list():
    class InvalidArticleView(ArticleView):
        actions = ["invalid"]

    with pytest.raises(ValueError, match="Unknown action with name `invalid`"):
        InvalidArticleView()


def test_invalid_row_action_list():
    class InvalidArticleView(ArticleView):
        row_actions = ["invalid"]

    with pytest.raises(ValueError, match="Unknown row action with name `invalid`"):
        InvalidArticleView()


@pytest.mark.parametrize(
    "url, params",
    [
        ("/admin/api/article/action", {"pks": [2, 3]}),
        ("/admin/api/article/row-action", {"pk": 2}),
    ],
)
def test_actions_when_model_is_not_accessible(url, params):
    class InaccessibleArticleView(ArticleView):
        def is_accessible(self, request: Request) -> bool:
            return False

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(InaccessibleArticleView)
    admin.mount_to(app)
    client = TestClient(app, base_url="http://testserver")

    response = client.get(url, params={"name": "make_published", **params})
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"
