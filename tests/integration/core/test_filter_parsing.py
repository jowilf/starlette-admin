"""Tests for _parse_list_params, _parse_filter_param, and filter-chip helpers."""

from unittest.mock import MagicMock

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    IntegerField,
    ListField,
    RequestAction,
    StringField,
    TextAreaField,
)
from starlette_admin.fields import BaseField
from starlette_admin.filters.registry import FilterRegistry
from starlette_admin.views import BaseModelView

from tests.integration.core.tinydb_model_view import (
    TinydbBaseModel,
    TinydbModelView,
)


class Article(TinydbBaseModel):
    title: str = ""
    body: str | None = None
    tags: list | None = None


class ArticleView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        TextAreaField("body"),
        ListField(StringField("tags")),
    ]
    searchable_fields = ("title", "body", "tags")
    sortable_fields = ("id", "title")
    page_size = 5


@pytest.fixture(autouse=True)
def seed():
    ArticleView._db.truncate()
    for i in range(1, 6):
        ArticleView._db.insert(
            Article(title=f"Article {i}", body=f"Body {i}").to_tinydb_doc()
        )
    yield
    ArticleView._db.truncate()


@pytest.fixture()
def client():
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    return TestClient(app)


# ── _parse_list_params edge cases ─────────────────────────────────────────────


def test_list_invalid_page_defaults_to_1(client):
    response = client.get("/admin/article/list", params={"page": "bad"})
    assert response.status_code == 200


def test_list_negative_page_size_minus_one(client):
    # page_size=-1 is not in page_size_options → rejected with 400
    response = client.get("/admin/article/list", params={"page_size": "-1"})
    assert response.status_code == 400


def test_list_invalid_page_size_defaults(client):
    # page_size=0 is not in page_size_options → rejected with 400
    response = client.get("/admin/article/list", params={"page_size": "0"})
    assert response.status_code == 400


def test_list_sort_invalid_field_uses_default(client):
    response = client.get("/admin/article/list", params={"sort": "nonexistent__asc"})
    assert response.status_code == 200


def test_list_sort_invalid_dir_defaults_to_asc(client):
    # valid field but invalid direction, coerced to asc
    response = client.get("/admin/article/list", params={"sort": "title__sideways"})
    assert response.status_code == 200


def test_list_multi_sort(client):
    """Multiple sort params produce multi-sort behavior."""
    response = client.get(
        "/admin/article/list",
        params=[("sort", "title__asc"), ("sort", "id__desc")],
    )
    assert response.status_code == 200
    # Both sort badges should appear since there are 2 active sorts
    assert "sort-link" in response.text


def test_list_q_param(client):
    response = client.get("/admin/article/list", params={"q": "Article 1"})
    assert response.status_code == 200


def test_list_visible_cols_restricts_table_columns(client):
    """The ``cols`` query parameter controls which columns are rendered."""
    response = client.get("/admin/article/list", params={"cols": "title"})
    assert response.status_code == 200
    assert 'data-column="title"' in response.text
    assert 'data-column="id"' not in response.text
    assert 'data-column="body"' not in response.text
    assert 'data-column="tags"' not in response.text


# ── _parse_filter_param: valid filters ───────────────────────────────────────


def test_list_with_valid_filter(client):
    filt = 'title__contains="Article 1"'
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


def test_list_with_group_filter(client):
    filt = "title__contains=1 OR title__contains=2"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


def test_list_with_no_value_filter(client):
    # is_null on a ListField takes no value
    filt = "tags__is_null"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


# ── _parse_filter_param: invalid filters → 400 ───────────────────────────────


def test_list_with_invalid_filter_no_dunder(client):
    # No __ separator → parse error → 400
    response = client.get("/admin/article/list", params={"filter": "notafilter"})
    assert response.status_code == 400


def test_list_with_unknown_field(client):
    filt = "nonexistent__contains=x"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_list_with_unknown_filter(client):
    filt = "title__no_such_filter=x"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_list_with_missing_value(client):
    # The 'contains' operator requires a value. A missing '=' in the leaf node leads to a 400 error.
    filt = "title__contains"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_list_with_trailing_garbage(client):
    # An unknown operator between rules, or trailing characters after parsing, results in a 400 error.
    filt = "title__contains=x XAND title__contains=y"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_list_with_invalid_leaf_token(client):
    # A missing '__' in the key part causes a parse error, resulting in a 400 error.
    filt = "titlecontains=x"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


# ── filter with has_value2 ────────────────────────────────────────────────────


def test_list_filter_missing_value2(client):
    # The 'eq' operator does not require 'value2'; this operation should succeed.
    filt = "title__eq=x"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


class ArticleWithRangeView(TinydbModelView):
    """View that exposes a BetweenFilter (has_value2=True) on the id field."""

    fields = [
        IntegerField("id"),
        StringField("title"),
    ]

    def get_filter_registry(self):
        from starlette_admin.filters.registry import FilterRegistry

        from tests.integration.core.tinydb_model_view import (
            TinyDBContainsFilter,
            TinyDBEqualFilter,
        )

        registry = FilterRegistry()
        registry.register(StringField, TinyDBContainsFilter, TinyDBEqualFilter)
        registry.register(IntegerField)
        return registry


@pytest.fixture()
def range_client():
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleWithRangeView(Article))
    admin.mount_to(app)
    return TestClient(app)


def test_list_filter_unknown_field_null(range_client):
    # A field name without '__' causes a parse error, resulting in a 400 error.
    filt = "contains=x"
    response = range_client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


# ── active filter chips ───────────────────────────────────────────────────────


def test_list_filter_chips_shown(client):
    filt = "title__contains=Article"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200
    # The chip removal link should appear in the rendered page
    assert "filter" in response.text


def test_list_filter_chips_group(client):
    filt = "title__contains=A AND tags__is_null"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200
    # The AND connector should appear between the two top-level chips
    assert "AND" in response.text


def test_list_filter_chips_nested_group(client):
    # A nested group produces a "(subgroup)" chip label.
    filt = '(title__contains=A OR title__contains=B) AND title__eq="Article 1"'
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


def test_list_default_sort_tuple_format():
    """Test _default_sort() with fields_default_sort as (field, desc) tuple."""

    class SortedArticleView(TinydbModelView):
        fields = [IntegerField("id"), StringField("title")]
        fields_default_sort = [("title", True)]

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(SortedArticleView(Article))
    admin.mount_to(app)
    client = TestClient(app)
    response = client.get("/admin/article/list")
    assert response.status_code == 200


def test_filter_base_model_view_default_registry():
    """get_filter_registry on the base returns an empty FilterRegistry."""

    # Create a bare-minimum concrete view just to call the method.
    class MinimalView(TinydbModelView):
        fields = [IntegerField("id"), StringField("title")]

        def get_filter_registry(self):
            return BaseModelView.get_filter_registry(self)

    view = MinimalView(Article)
    registry = view.get_filter_registry()
    assert isinstance(registry, FilterRegistry)
    # Default registry has no filters registered

    assert registry.filters_for(StringField("x")) == []


# ── _build_filter_rule: has_value2 missing second value → 400 ─────────────────


class ArticleWithBetweenView(TinydbModelView):
    """View with a custom filter that has has_value2=True."""

    fields = [IntegerField("id"), StringField("title")]

    def get_filter_registry(self):
        from starlette_admin.filters.base import (
            BaseFilter,
            FilterApplyContext,
            FilterDataType,
        )
        from starlette_admin.filters.registry import FilterRegistry

        class BetweenStrFilter(BaseFilter):
            name = "between"
            label = "Between"
            data_type = FilterDataType.STRING
            has_value2 = True

            def apply(self, ctx: FilterApplyContext):
                return ctx.value

        registry = FilterRegistry()
        registry.register(StringField, BetweenStrFilter)
        return registry


@pytest.fixture()
def between_client():
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleWithBetweenView(Article))
    admin.mount_to(app)
    return TestClient(app)


def test_filter_missing_value2_raises_400(between_client):
    # The 'between' operator requires 'value2'. Without a '..' separator, 'value2' is absent, leading to a 400 error.
    filt = "title__between=a"
    response = between_client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_filter_with_value2(between_client):
    filt = "title__between=a..z"
    response = between_client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


# ── _describe_filter_node unit tests ──────────────────────────────────────────


def test_describe_filter_node_group_in_group(client):
    """Group containing sub-groups; inner groups get parenthesised labels."""
    # outer AND: [(inner OR: [title contains X, (inner AND: title contains Y)]), title eq Z]
    filt = "(title__contains=X OR (title__contains=Y)) AND title__eq=Z"
    response = client.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


def test_describe_filter_node_direct_has_value2():
    """Direct call to _describe_filter_node with a has_value2 filter node."""
    from starlette.requests import Request
    from starlette_admin.filters.base import (
        BaseFilter,
        FilterDataType,
    )
    from starlette_admin.filters.registry import FilterRegistry
    from starlette_admin.views import BaseModelView

    class RangeFilt(BaseFilter):
        name = "between"
        label = "Between"
        data_type = FilterDataType.STRING
        has_value2 = True

    RangeFilt.__abstractmethods__ = frozenset()

    registry = FilterRegistry()
    registry.register(StringField, RangeFilt)
    fields_by_name = {"title": StringField("title")}

    # The raw node dict format (same structure the Django parser produces)
    node = {"field": "title", "filter": "between", "value": "a", "value2": "z"}
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
    )
    result = BaseModelView._describe_filter_node(
        node, fields_by_name, registry, request
    )
    assert "a" in result and "z" in result


# ── can_access_field ──────────────────────────────────────────────────────────


def _req(action: RequestAction) -> MagicMock:
    r = MagicMock(spec=Request)
    r.state.action = action
    return r


def test_can_access_field_default_true_for_non_excluded():
    """Default can_access_field returns True for a non-excluded field."""
    view = ArticleView(Article)
    assert view.can_access_field(_req(RequestAction.LIST), StringField("title")) is True


def test_can_access_field_default_false_for_excluded_list():
    """Default can_access_field returns False when exclude_from_list is set."""
    view = ArticleView(Article)
    assert (
        view.can_access_field(
            _req(RequestAction.LIST), StringField("x", exclude_from_list=True)
        )
        is False
    )


def test_can_access_field_default_false_for_excluded_detail():
    view = ArticleView(Article)
    assert (
        view.can_access_field(
            _req(RequestAction.DETAIL), StringField("x", exclude_from_detail=True)
        )
        is False
    )


def test_can_access_field_default_false_for_excluded_create():
    view = ArticleView(Article)
    assert (
        view.can_access_field(
            _req(RequestAction.CREATE), StringField("x", exclude_from_create=True)
        )
        is False
    )


def test_can_access_field_default_false_for_excluded_edit():
    view = ArticleView(Article)
    assert (
        view.can_access_field(
            _req(RequestAction.EDIT), StringField("x", exclude_from_edit=True)
        )
        is False
    )


def test_can_access_field_other_action_ignores_exclude_from_list():
    """exclude_from_list does not block a DETAIL request."""
    view = ArticleView(Article)
    f = StringField("x", exclude_from_list=True)
    assert view.can_access_field(_req(RequestAction.DETAIL), f) is True


def test_filter_inaccessible_field_returns_400():
    """A filter referencing a field blocked by can_access_field raises HTTP 400."""

    class RestrictedArticleView(ArticleView):
        def can_access_field(
            self,
            request: Request,
            field: BaseField,
            action: RequestAction | None = None,
        ) -> bool:
            if field.name == "body":
                return False
            return super().can_access_field(request, field, action)

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(RestrictedArticleView(Article))
    admin.mount_to(app)
    c = TestClient(app)

    filt = "body__contains=x"
    response = c.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 400


def test_filter_accessible_field_still_works():
    """Filtering an accessible field returns 200 even when another field is blocked."""

    class RestrictedArticleView(ArticleView):
        def can_access_field(
            self,
            request: Request,
            field: BaseField,
            action: RequestAction | None = None,
        ) -> bool:
            if field.name == "body":
                return False
            return super().can_access_field(request, field, action)

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(RestrictedArticleView(Article))
    admin.mount_to(app)
    c = TestClient(app)

    filt = "title__contains=x"
    response = c.get("/admin/article/list", params={"filter": filt})
    assert response.status_code == 200


def test_sort_by_inaccessible_field_returns_400():
    """sort_by a field blocked by can_access_field returns HTTP 400."""

    class RestrictedArticleView(ArticleView):
        def can_access_field(
            self,
            request: Request,
            field: BaseField,
            action: RequestAction | None = None,
        ) -> bool:
            if field.name == "title":
                return False
            return super().can_access_field(request, field, action)

    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(RestrictedArticleView(Article))
    admin.mount_to(app)
    c = TestClient(app)

    response = c.get("/admin/article/list", params={"sort": "title__asc"})
    assert response.status_code == 400


def test_sort_unknown_field_still_falls_back():
    """sort with a completely unknown field name still falls back silently (200)."""
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    c = TestClient(app)

    response = c.get("/admin/article/list", params={"sort": "nonexistent_xyz__asc"})
    assert response.status_code == 200
