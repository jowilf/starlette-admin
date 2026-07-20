import enum
import re
from typing import Any

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, EnumField, IntegerField, StringField, action
from starlette_admin.actions import ActionSelection, row_action
from starlette_admin.exceptions import ActionFailed

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Status(enum.StrEnum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class Article(TinydbBaseModel):
    status: Status = Status.Draft


class ArticleView(TinydbModelView):
    fields = [IntegerField("id"), EnumField("status", enum=Status)]
    actions = [
        "make_published",
        "delete",
        "always_failed",
        "forbidden",
        "invalid_redirect",
        "redirect",
        "sync_all",
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
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> str:
        articles = await selection.rows()
        for article in articles:
            article.status = Status.Published
            type(self)._db.update(article.to_tinydb_doc(), doc_ids=[article.id])
        return f"{len(articles)} articles were successfully marked as published"

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
        type(self)._db.update(article.to_tinydb_doc(), doc_ids=[article.id])
        return "The article was successfully marked as published"

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(
        self, request: Request, selection: ActionSelection
    ) -> str:
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
    async def forbidden_action(
        self, request: Request, selection: ActionSelection
    ) -> str:
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
        self, request: Request, selection: ActionSelection
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
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        return RedirectResponse("https://example.com/")

    @row_action(
        name="redirect",
        text="Redirect",
        custom_response=True,
    )
    async def redirect_row_action(self, request: Request, pks: list[Any]) -> Response:
        return RedirectResponse("https://example.com/")

    sync_all_calls: list[list[Any]] = []

    @action(
        name="sync_all",
        text="Sync all",
        allow_empty_selection=True,
    )
    async def sync_all_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        type(self).sync_all_calls.append(await selection.pks())


@pytest.fixture
def client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)

    ArticleView._db.truncate()
    ArticleView._db.insert(Article(status=Status.Draft).to_tinydb_doc())
    ArticleView._db.insert(Article(status=Status.Withdrawn).to_tinydb_doc())
    ArticleView._db.insert(Article(status=Status.Draft).to_tinydb_doc())

    return CsrfTestClient(app, base_url="http://testserver")


def test_all_actions_are_available_by_default():
    class DefaultActionArticleView(ArticleView):
        actions = None

    assert sorted(DefaultActionArticleView(Article).actions) == sorted(
        [
            "make_published",
            "delete",
            "export",
            "always_failed",
            "forbidden",
            "invalid_redirect",
            "redirect",
            "sync_all",
        ]
    )


def test_all_row_actions_are_available_by_default():
    class DefaultActionArticleView(ArticleView):
        row_actions = None

    assert sorted(DefaultActionArticleView(Article).row_actions) == sorted(
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
        ("sync_all", 1),
    ],
)
def test_actions_are_available_in_ui(client: TestClient, action, expected_count):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    matches = re.findall(
        r'(data-is-row-action="true"\s*)?data-name="' + re.escape(action) + r'"',
        response.text,
    )
    assert sum(1 for is_row_action in matches if not is_row_action) == expected_count


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
def test_row_actions_are_available_in_ui(
    client: TestClient, row_action, expected_count
):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    row_html = re.search(r'<tr data-pk="1"[^>]*>(.*?)</tr>', response.text, re.DOTALL)
    assert row_html is not None
    assert row_html.group(1).count(f'data-name="{row_action}"') == expected_count


def test_action_modal_size_defaults_to_sm(client: TestClient):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    assert re.search(
        r'data-modal-size="sm"[^>]*data-name="make_published"', response.text
    )


def test_action_modal_size_is_configurable():
    class SizedArticleView(ArticleView):
        actions = ["sized"]
        row_actions = []

        @action(
            name="sized",
            text="Sized action",
            confirmation="Proceed?",
            modal_size="lg",
        )
        async def sized_action(
            self, request: Request, selection: ActionSelection
        ) -> None:
            pass

    app = Starlette()
    admin = BaseAdmin()
    admin.add_view(SizedArticleView(Article))
    admin.mount_to(app)
    sized_client = CsrfTestClient(app, base_url="http://testserver")

    response = sized_client.get("/admin/article/list")
    assert response.status_code == 200
    assert 'data-modal-size="lg"' in response.text
    assert re.search(r'data-modal-size="lg"[^>]*data-name="sized"', response.text)


def test_invalid_action_modal_size_raises_at_decoration_time():
    with pytest.raises(ValueError, match="modal_size"):

        @action(name="bad_size", text="Bad size", modal_size="huge")
        async def bad_size_action(
            self, request: Request, selection: ActionSelection
        ) -> None:
            pass


def test_invalid_row_action_modal_size_raises_at_decoration_time():
    with pytest.raises(ValueError, match="modal_size"):

        @row_action(name="bad_size", text="Bad size", modal_size="huge")
        async def bad_size_row_action(self, request: Request, pk: Any) -> None:
            pass


def test_is_row_action_allowed_for_obj(client: TestClient):
    # pk=1 is Draft, pk=2 is Withdrawn (client fixture's seed data).
    class RestrictedArticleView(ArticleView):
        async def is_row_action_allowed_for_obj(
            self, request: Request, name: str, obj: Article
        ) -> bool:
            if name == "make_published" and obj.status == Status.Withdrawn:
                return False
            return await super().is_row_action_allowed_for_obj(request, name, obj)

    app = Starlette()
    admin = BaseAdmin()
    admin.add_view(RestrictedArticleView(Article))
    admin.mount_to(app)
    restricted_client = CsrfTestClient(app, base_url="http://testserver")

    response = restricted_client.get("/admin/article/list")
    assert response.status_code == 200
    draft_row = re.search(r'<tr data-pk="1"[^>]*>(.*?)</tr>', response.text, re.DOTALL)
    withdrawn_row = re.search(
        r'<tr data-pk="2"[^>]*>(.*?)</tr>', response.text, re.DOTALL
    )
    assert draft_row.group(1).count('data-name="make_published"') == 1
    assert withdrawn_row.group(1).count('data-name="make_published"') == 0

    # Server-side enforcement matches the UI: the row action is rejected for
    # the withdrawn article even though `is_row_action_allowed` alone allows it.
    response = restricted_client.post(
        "/admin/_api/article/row-action", params={"name": "make_published", "pk": 2}
    )
    assert response.status_code == 400
    assert ArticleView._get(2).status == Status.Withdrawn

    # Untouched for a draft article.
    response = restricted_client.post(
        "/admin/_api/article/row-action", params={"name": "make_published", "pk": 1}
    )
    assert response.status_code == 200
    assert ArticleView._get(1).status == Status.Published


def test_global_action_runs_without_pks(client: TestClient):
    ArticleView.sync_all_calls.clear()
    response = client.post(
        "/admin/_api/article/action", params={"name": "sync_all", "pks": []}
    )
    assert response.status_code == 200
    assert ArticleView.sync_all_calls == [[]]


def test_non_global_action_rejects_empty_pks(client: TestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "make_published", "pks": []}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Please select at least one item"


def test_global_actions_dropdown_rendered_separately(client: TestClient):
    response = client.get("/admin/article/list")
    assert response.status_code == 200
    global_dropdown = re.search(
        r'<div class="dropdown" id="actions-dropdown-global">(.*?)</div>\s*</div>',
        response.text,
        re.DOTALL,
    )
    assert global_dropdown is not None
    assert 'data-name="sync_all"' in global_dropdown.group(1)
    assert 'data-name="make_published"' not in global_dropdown.group(1)


def test_action_execution(client: TestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "make_published", "pks": [2, 3]}
    )
    assert response.status_code == 200
    assert "redirect" in response.json()
    for pk, expected_status in [
        (1, Status.Draft),
        (2, Status.Published),
        (3, Status.Published),
    ]:
        assert ArticleView._get(pk).status == expected_status


def test_row_action_execution(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "make_published", "pk": 2}
    )
    assert response.status_code == 200
    assert "redirect" in response.json()
    assert ArticleView._get(2).status == Status.Published


def test_failed_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "always_failed", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Sorry, We can't proceed this action now."


def test_failed_row_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "always_failed", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Sorry, We can't proceed this action now."


def test_forbidden_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "forbidden", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


def test_forbidden_row_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "forbidden", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


def test_invalid_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/action", params={"name": "invalid", "pks": [2, 3]}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Invalid action"


def test_invalid_row_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "invalid", "pk": 2}
    )
    assert response.status_code == 400
    assert response.json()["msg"] == "Invalid row action"


def test_delete_row_action(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action", params={"name": "delete", "pk": 2}
    )
    assert response.status_code == 200
    assert "redirect" in response.json()
    assert ArticleView._get(2) is None


def test_custom_response_for_batch_actions(client: TestClient):
    response = client.post(
        "/admin/_api/article/action",
        params={"name": "redirect", "pks": [2, 3]},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


def test_custom_response_for_row_actions(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action",
        params={"name": "redirect", "pk": 2},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


def test_invalid_custom_response_for_batch_actions(client: TestClient):
    response = client.post(
        "/admin/_api/article/action",
        params={"name": "invalid_redirect", "pks": [2, 3]},
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Set custom_response=True on this action to return a custom response"
    )


def test_invalid_custom_response_for_row_actions(client: TestClient):
    response = client.post(
        "/admin/_api/article/row-action",
        params={"name": "invalid_redirect", "pk": 2},
    )
    assert response.status_code == 400
    assert (
        response.json()["msg"]
        == "Set custom_response=True on this action to return a custom response"
    )


def test_action_and_row_action_forms_support_sync_and_async_callables():
    def _export_form(request: Request) -> str:
        return f"sync-form-for-{request.method}"

    async def _rename_form(request: Request, obj: Article) -> str:
        return f"async-form-for-{obj.status.value}"

    class CallableFormArticleView(ArticleView):
        actions = ["export"]
        row_actions = ["rename"]

        @action(name="export", text="Export selected", form=_export_form)
        async def export_action(
            self, request: Request, selection: ActionSelection
        ) -> str:
            return "exported"

        @row_action(name="rename", text="Rename", form=_rename_form)
        async def rename_row_action(self, request: Request, pk: Any) -> str:
            return "renamed"

    CallableFormArticleView._db.truncate()
    CallableFormArticleView._db.insert(Article(status=Status.Draft).to_tinydb_doc())

    app = Starlette()
    admin = BaseAdmin()
    admin.add_view(CallableFormArticleView(Article))
    admin.mount_to(app)
    form_client = CsrfTestClient(app, base_url="http://testserver")

    response = form_client.get("/admin/article/list")
    assert response.status_code == 200
    assert "sync-form-for-GET" in response.text
    assert f"async-form-for-{Status.Draft.value}" in response.text


def test_invalid_action_list():
    class InvalidArticleView(ArticleView):
        actions = ["invalid"]

    with pytest.raises(ValueError, match="Unknown action with name `invalid`"):
        InvalidArticleView(Article)


def test_invalid_row_action_list():
    class InvalidArticleView(ArticleView):
        row_actions = ["invalid"]

    with pytest.raises(ValueError, match="Unknown row action with name `invalid`"):
        InvalidArticleView(Article)


def test_dedicated_button_action_requires_allow_empty_selection():
    class DedicatedButtonArticleView(ArticleView):
        actions = [*ArticleView.actions, "dedicated_no_empty_selection"]

        @action(
            name="dedicated_no_empty_selection",
            text="Dedicated",
            dedicated_button=True,
        )
        async def dedicated_no_empty_selection_action(
            self, request: Request, selection: ActionSelection
        ) -> str:
            return "ok"

    with pytest.raises(
        ValueError,
        match=(
            "Action `dedicated_no_empty_selection`: dedicated_button=True "
            "requires allow_empty_selection=True"
        ),
    ):
        DedicatedButtonArticleView(Article)


@pytest.mark.parametrize(
    "url, params",
    [
        ("/admin/_api/article/action", {"pks": [2, 3]}),
        ("/admin/_api/article/row-action", {"pk": 2}),
    ],
)
def test_actions_when_model_is_not_accessible(url, params):
    class InaccessibleArticleView(ArticleView):
        def is_accessible(self, request: Request) -> bool:
            return False

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(InaccessibleArticleView(Article))
    admin.mount_to(app)
    client = CsrfTestClient(app, base_url="http://testserver")

    response = client.post(url, params={"name": "make_published", **params})
    assert response.status_code == 400
    assert response.json()["msg"] == "Forbidden"


# ── #654: filter context passed to actions ────────────────────────────────


class FilterArticle(TinydbBaseModel):
    title: str = ""
    status: Status = Status.Draft


class FilterArticleView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        EnumField("status", enum=Status),
    ]
    actions = ["record_context", "record_filters_only", "record_count", "delete"]

    recorded_contexts: list[dict] = []
    recorded_counts: list[int] = []

    @action(name="record_context", text="Record context", allow_empty_selection=True)
    async def record_context_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        type(self).recorded_contexts.append(
            {
                "pks": sorted(int(pk) for pk in await selection.pks()),
                "is_select_all": selection.is_select_all,
                "list_q": selection.q,
                "list_filters": selection.filters,
            }
        )

    @action(
        name="record_filters_only",
        text="Record filters only",
        allow_empty_selection=True,
    )
    async def record_filters_only_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Reasons directly about `filters`/`q` instead of materializing rows,
        # so `action_select_all_limit` never applies to this handler.
        type(self).recorded_contexts.append(
            {
                "is_select_all": selection.is_select_all,
                "list_q": selection.q,
                "list_filters": selection.filters,
            }
        )

    @action(name="record_count", text="Record count", allow_empty_selection=True)
    async def record_count_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # `rows()` first so `count()` reuses the already-fetched rows, then
        # `count()` again so the second call hits the cached `_count`.
        await selection.rows()
        first = await selection.count()
        second = await selection.count()
        type(self).recorded_counts.append(first)
        type(self).recorded_counts.append(second)


@pytest.fixture
def filter_client() -> TestClient:
    FilterArticleView.recorded_contexts = []
    FilterArticleView.recorded_counts = []
    FilterArticleView._db.truncate()
    FilterArticleView._db.insert(
        FilterArticle(title="alpha", status=Status.Draft).to_tinydb_doc()
    )
    FilterArticleView._db.insert(
        FilterArticle(title="beta", status=Status.Published).to_tinydb_doc()
    )
    FilterArticleView._db.insert(
        FilterArticle(title="gamma", status=Status.Draft).to_tinydb_doc()
    )

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(FilterArticleView(FilterArticle, key="article"))
    admin.mount_to(app)
    return CsrfTestClient(app, base_url="http://testserver")


def test_action_receives_list_filter_and_search_context(filter_client: TestClient):
    response = filter_client.post(
        "/admin/_api/article/action",
        params={
            "name": "record_context",
            "pks": [],
            "_list_query": "?q=alpha&filter=status__eq=d",
        },
    )
    assert response.status_code == 200
    ctx = FilterArticleView.recorded_contexts[-1]
    assert ctx["is_select_all"] is False
    assert ctx["list_q"] == "alpha"
    assert ctx["list_filters"].rules[0].field == "status"


def test_select_all_matching_resolves_pks_from_filter(filter_client: TestClient):
    response = filter_client.post(
        "/admin/_api/article/action",
        params={
            "name": "record_context",
            "all": "1",
            "_list_query": "?filter=status__eq=d",
        },
    )
    assert response.status_code == 200
    ctx = FilterArticleView.recorded_contexts[-1]
    assert ctx["is_select_all"] is True
    # Only the two Draft articles (id 1 and 3) match; the Published one (id 2)
    # does not, even though `all=1` was sent without any explicit `pks`.
    assert ctx["pks"] == [1, 3]


def test_select_all_matching_uncapped_when_handler_only_reads_filters(
    filter_client: TestClient,
):
    class LimitedFilterArticleView(FilterArticleView):
        action_select_all_limit = 1

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(LimitedFilterArticleView(FilterArticle, key="article"))
    admin.mount_to(app)
    client = CsrfTestClient(app, base_url="http://testserver")

    # 2 rows match the filter, above `action_select_all_limit=1`. The handler
    # only reads `selection.filters`/`selection.q` and never calls
    # `rows()`/`pks()`/`count()`, so the cap never applies.
    response = client.post(
        "/admin/_api/article/action",
        params={
            "name": "record_filters_only",
            "all": "1",
            "_list_query": "?filter=status__eq=d",
        },
    )
    assert response.status_code == 200
    ctx = LimitedFilterArticleView.recorded_contexts[-1]
    assert ctx["is_select_all"] is True
    assert ctx["list_filters"].rules[0].field == "status"


def test_select_all_matching_respects_select_all_limit(filter_client: TestClient):
    class LimitedFilterArticleView(FilterArticleView):
        action_select_all_limit = 1

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(LimitedFilterArticleView(FilterArticle, key="article"))
    admin.mount_to(app)
    client = CsrfTestClient(app, base_url="http://testserver")

    response = client.post(
        "/admin/_api/article/action",
        params={"name": "record_context", "all": "1", "_list_query": ""},
    )
    assert response.status_code == 400
    assert "Too many rows match" in response.json()["msg"]


def test_malformed_list_query_filter_returns_400(filter_client: TestClient):
    response = filter_client.post(
        "/admin/_api/article/action",
        params={
            "name": "record_context",
            "pks": [],
            "_list_query": "?filter=not-a-valid-filter",
        },
    )
    assert response.status_code == 400
    assert "Invalid 'filter' parameter" in response.json()["msg"]


def test_action_selection_count_is_cached(filter_client: TestClient):
    response = filter_client.post(
        "/admin/_api/article/action",
        params={
            "name": "record_count",
            "pks": [1, 3],
        },
    )
    assert response.status_code == 200
    assert FilterArticleView.recorded_counts == [2, 2]


def test_delete_action_works_with_select_all_matching(filter_client: TestClient):
    response = filter_client.post(
        "/admin/_api/article/action",
        params={
            "name": "delete",
            "all": "1",
            "_list_query": "?filter=status__eq=d",
        },
    )
    assert response.status_code == 200
    assert FilterArticleView._get(1) is None
    assert FilterArticleView._get(2) is not None
    assert FilterArticleView._get(3) is None
