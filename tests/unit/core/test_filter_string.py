"""Unit tests for `BaseModelView` filter-string parsing and serialization helpers."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request
from starlette_admin import IntegerField, StringField
from starlette_admin.filters import FilterRegistry
from starlette_admin.filters.base import FilterGroup, FilterRule
from starlette_admin.filters.generic import EqualFilter
from starlette_admin.types import ListParams, RequestAction
from starlette_admin.views import BaseModelView


def _request_with_filter(filter_str: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/admin/post/list",
        "query_string": f"filter={filter_str}".encode(),
        "headers": [],
    }
    return Request(scope)


class _ConcreteEqualFilter(EqualFilter):
    """`EqualFilter` is abstract (no `apply`); `_describe_filter_node`
    instantiates the filter class to read its choices, so tests exercising
    that path need a concrete subclass rather than the generic base.
    """

    def apply(self, ctx: Any) -> Any:
        return ctx.query


class _DummyView(BaseModelView):
    key = "post"
    fields = [IntegerField("id"), StringField("title")]
    pk_attr = "id"

    def get_filter_registry(self) -> FilterRegistry:
        registry = FilterRegistry()
        registry.register(StringField, EqualFilter)
        return registry


# ── _parse_filter_string ──────────────────────────────────────────────────────


def test_parse_filter_string_simple_leaf():
    result = BaseModelView._parse_filter_string("title__eq=hello")
    assert result == {"field": "title", "filter": "eq", "value": "hello"}


def test_parse_filter_string_leaf_no_value():
    result = BaseModelView._parse_filter_string("title__is_null")
    assert result == {"field": "title", "filter": "is_null"}


def test_parse_filter_string_between():
    result = BaseModelView._parse_filter_string("id__between=1..10")
    assert result == {"field": "id", "filter": "between", "value": "1", "value2": "10"}


def test_parse_filter_string_quoted_value_with_spaces():
    result = BaseModelView._parse_filter_string('title__eq="hello world"')
    assert result == {"field": "title", "filter": "eq", "value": "hello world"}


def test_parse_filter_string_escaped_quote():
    result = BaseModelView._parse_filter_string('title__eq="say \\"hi\\""')
    assert result == {"field": "title", "filter": "eq", "value": 'say "hi"'}


def test_parse_filter_string_escaped_backslash():
    result = BaseModelView._parse_filter_string('title__eq="C:\\\\Users"')
    assert result == {"field": "title", "filter": "eq", "value": "C:\\Users"}


def test_parse_filter_string_comma_list():
    result = BaseModelView._parse_filter_string("title__in=a,b,c")
    assert result == {"field": "title", "filter": "in", "value": ["a", "b", "c"]}


def test_parse_filter_string_comma_with_quoted_item():
    result = BaseModelView._parse_filter_string('title__in="a, b",c')
    assert result == {"field": "title", "filter": "in", "value": ['"a, b"', "c"]}


def test_parse_filter_string_and_group():
    result = BaseModelView._parse_filter_string("title__eq=a AND views__gt=1")
    assert result == {
        "logic": "and",
        "rules": [
            {"field": "title", "filter": "eq", "value": "a"},
            {"field": "views", "filter": "gt", "value": "1"},
        ],
    }


def test_parse_filter_string_or_group_in_parens():
    result = BaseModelView._parse_filter_string("(title__eq=a OR title__eq=b)")
    assert result == {
        "logic": "or",
        "rules": [
            {"field": "title", "filter": "eq", "value": "a"},
            {"field": "title", "filter": "eq", "value": "b"},
        ],
    }


def test_parse_filter_string_empty_raises():
    with pytest.raises(ValueError, match="empty filter string"):
        BaseModelView._parse_filter_string("")


def test_parse_filter_string_trailing_keyword():
    result = BaseModelView._parse_filter_string("title__eq=a AND")
    assert result == {
        "logic": "and",
        "rules": [{"field": "title", "filter": "eq", "value": "a"}],
    }


def test_parse_filter_string_empty_group():
    result = BaseModelView._parse_filter_string("(AND)")
    assert result == {"logic": "and", "rules": []}


def test_parse_filter_string_double_keyword_raises():
    """A keyword where a leaf is expected is treated as a missing term."""
    with pytest.raises(ValueError, match="unexpected characters"):
        BaseModelView._parse_filter_string("(title__eq=a AND OR title__eq=b)")


def test_parse_filter_string_missing_separator_raises():
    with pytest.raises(ValueError, match="missing '__'"):
        BaseModelView._parse_filter_string("title")


# ── _serialize_filter_string ──────────────────────────────────────────────────


def test_serialize_filter_string_simple_leaf():
    node = {"field": "title", "filter": "eq", "value": "hello"}
    assert BaseModelView._serialize_filter_string(node) == "title__eq=hello"


def test_serialize_filter_string_leaf_no_value():
    node = {"field": "title", "filter": "is_null"}
    assert BaseModelView._serialize_filter_string(node) == "title__is_null"


def test_serialize_filter_string_between():
    node = {"field": "id", "filter": "between", "value": "1", "value2": "10"}
    assert BaseModelView._serialize_filter_string(node) == "id__between=1..10"


def test_serialize_filter_string_list_value():
    node = {"field": "title", "filter": "in", "value": ["a", "b", "c"]}
    assert BaseModelView._serialize_filter_string(node) == "title__in=a,b,c"


def test_serialize_filter_string_quoted_value():
    node = {"field": "title", "filter": "eq", "value": "hello world"}
    assert BaseModelView._serialize_filter_string(node) == 'title__eq="hello world"'


def test_serialize_filter_string_nested_group():
    node = {
        "logic": "and",
        "rules": [
            {"field": "title", "filter": "eq", "value": "a"},
            {
                "logic": "or",
                "rules": [
                    {"field": "views", "filter": "gt", "value": "1"},
                    {"field": "views", "filter": "lt", "value": "10"},
                ],
            },
        ],
    }
    serialized = BaseModelView._serialize_filter_string(node)
    assert serialized == "title__eq=a AND (views__gt=1 OR views__lt=10)"


# ── _build_filter_node / _parse_filter_param error paths ──────────────────────


def test_build_filter_node_not_dict_raises():
    view = _DummyView()
    registry = view.get_filter_registry()
    fields_by_name = {"title": StringField("title")}
    with pytest.raises(ValueError, match="must be a JSON object"):
        view._build_filter_node("not-a-dict", fields_by_name, registry)


def test_build_filter_node_invalid_logic_raises():
    view = _DummyView()
    registry = view.get_filter_registry()
    fields_by_name = {"title": StringField("title")}
    with pytest.raises(ValueError, match="invalid filter logic"):
        view._build_filter_node(
            {
                "logic": "xor",
                "rules": [{"field": "title", "filter": "eq", "value": "x"}],
            },
            fields_by_name,
            registry,
        )


def test_build_filter_node_rules_not_list_raises():
    view = _DummyView()
    registry = view.get_filter_registry()
    fields_by_name = {"title": StringField("title")}
    with pytest.raises(ValueError, match="'rules' must be a JSON array"):
        view._build_filter_node(
            {"logic": "and", "rules": "not-a-list"},
            fields_by_name,
            registry,
        )


# ── _describe_filter_node ─────────────────────────────────────────────────────


def test_describe_filter_node_simple():
    registry = FilterRegistry()
    registry.register(StringField, _ConcreteEqualFilter)
    fields_by_name = {"title": StringField("title")}
    assert (
        BaseModelView._describe_filter_node(
            {"field": "title", "filter": "eq", "value": "hello"},
            fields_by_name,
            registry,
            _request_with_filter("title__eq=hello"),
        )
        == "Title: Equal hello"
    )


def test_describe_filter_node_no_value():
    from starlette_admin.filters.generic import IsNullFilter

    registry = FilterRegistry()
    registry.register(StringField, IsNullFilter)
    fields_by_name = {"title": StringField("title")}
    assert (
        BaseModelView._describe_filter_node(
            {"field": "title", "filter": "is_null"},
            fields_by_name,
            registry,
            _request_with_filter("title__is_null"),
        )
        == "Title: Is null"
    )


def test_describe_filter_node_empty_group():
    registry = FilterRegistry()
    fields_by_name = {}
    assert (
        BaseModelView._describe_filter_node(
            {"logic": "and", "rules": []},
            fields_by_name,
            registry,
            _request_with_filter(""),
        )
        == ""
    )


def test_describe_filter_node_nested_group():
    registry = FilterRegistry()
    registry.register(StringField, _ConcreteEqualFilter)
    fields_by_name = {"title": StringField("title")}
    node = {
        "logic": "or",
        "rules": [
            {"field": "title", "filter": "eq", "value": "a"},
            {"field": "title", "filter": "eq", "value": "b"},
        ],
    }
    request = _request_with_filter("title__eq=a")
    assert (
        BaseModelView._describe_filter_node(node, fields_by_name, registry, request)
        == "(Title: Equal a OR Title: Equal b)"
    )


def test_describe_filter_node_missing_value_displays_empty():
    """A leaf whose filter takes a value but the node has none (e.g. built by
    hand rather than through the URL parser) renders that value as `""`
    instead of the literal `None`.
    """
    registry = FilterRegistry()
    registry.register(StringField, _ConcreteEqualFilter)
    fields_by_name = {"title": StringField("title")}
    assert (
        BaseModelView._describe_filter_node(
            {"field": "title", "filter": "eq"},
            fields_by_name,
            registry,
            _request_with_filter("title__eq"),
        )
        == "Title: Equal "
    )


def test_describe_filter_node_non_dict():
    """Non-dict nodes fall back to their string representation."""
    registry = FilterRegistry()
    fields_by_name = {}
    request = _request_with_filter("")
    assert (
        BaseModelView._describe_filter_node("raw", fields_by_name, registry, request)
        == "raw"
    )
    assert (
        BaseModelView._describe_filter_node(42, fields_by_name, registry, request)
        == "42"
    )


# ── _filter_builder_fields: filter-supplied choices ───────────────────────────


def test_filter_builder_fields_includes_filter_choices():
    """A filter whose `get_choices` returns pairs surfaces them as the
    field's `choices` in the filter-builder metadata, taking precedence over
    the field's own (here absent) choices.
    """

    class _ChoiceFilter(_ConcreteEqualFilter):
        def get_choices(self, request: Request) -> list[tuple[int, str]]:
            return [(1, "One"), (2, "Two")]

    class _ChoiceView(_DummyView):
        def get_filter_registry(self) -> FilterRegistry:
            registry = FilterRegistry()
            registry.register(StringField, _ChoiceFilter)
            return registry

    view = _ChoiceView()
    request = _request_with_filter("")
    request.state.action = RequestAction.LIST
    fields_data = view._filter_builder_fields(request)
    title_field = next(f for f in fields_data if f["name"] == "title")
    assert title_field["filters"][0]["choices"] == [["1", "One"], ["2", "Two"]]


# ── _serialize_filter_string: non-dict fallback ───────────────────────────────


def test_serialize_filter_string_non_dict_node():
    """A bare non-dict node falls through to str(node)."""
    assert BaseModelView._serialize_filter_string("raw_string") == "raw_string"
    assert BaseModelView._serialize_filter_string(42) == "42"


# ── _active_filter_chips: ValueError path ────────────────────────────────────


def test_active_filter_chips_returns_empty_on_invalid_filter_string():
    """When the filter query param is missing/invalid, returns []."""
    view = _DummyView()
    # Non-empty filters so is_empty() → False
    list_params = ListParams(
        filters=FilterGroup(rules=[FilterRule(field="title", filter="eq", value="x")])
    )
    # Request with no 'filter' param → not_none(None) raises ValueError
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/admin/post/list",
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)
    _logic, chips = view._active_filter_chips(request, list_params)
    assert chips == []


def test_active_filter_chips_returns_empty_when_rules_not_list(monkeypatch):
    """A malformed group with non-list rules is treated as having no pills."""
    view = _DummyView()
    list_params = ListParams(
        filters=FilterGroup(rules=[FilterRule(field="title", filter="eq", value="x")])
    )
    request = _request_with_filter("title__eq=x")
    monkeypatch.setattr(
        view, "_parse_filter_string", lambda _raw: {"logic": "and", "rules": "bad"}
    )
    _logic, chips = view._active_filter_chips(request, list_params)
    assert chips == []


# ── _parse_list_params: visible_cols from ?cols= ──────────────────────────────


def test_parse_list_params_visible_cols_subset():
    """cols=<subset> sets visible_cols; cols=<all> leaves it None."""
    view = _DummyView()  # fields: id, title

    def _req(qs: str) -> Request:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/admin/post/list",
            "query_string": qs.encode(),
            "headers": [],
        }
        req = Request(scope)
        req.state.action = RequestAction.LIST
        return req

    # Single column → visible_cols set
    params = view._parse_list_params(_req("cols=title"))
    assert params.visible_cols == ["title"]

    # All columns → visible_cols stays None
    params_all = view._parse_list_params(_req("cols=id,title"))
    assert params_all.visible_cols is None

    # Unknown column → filtered out → empty valid list → visible_cols None
    params_unknown = view._parse_list_params(_req("cols=nonexistent"))
    assert params_unknown.visible_cols is None


# ── Depth limit ───────────────────────────────────────────────────────────────


def _nested(n: int) -> str:
    """Build a string with n nested open-parens around a leaf token."""
    return "(" * n + "a__eq=1" + ")" * n


def test_depth_limit_at_max_allowed():
    """Parser accepts exactly 20 levels of nesting."""
    result = BaseModelView._parse_filter_string(_nested(20))
    assert result is not None


def test_depth_limit_raises_at_21():
    """Parser rejects 21 levels of nesting."""
    with pytest.raises(ValueError, match="nesting depth"):
        BaseModelView._parse_filter_string(_nested(21))


def test_depth_limit_raises_deep():
    """Parser rejects deeply nested input without stack overflow."""
    with pytest.raises(ValueError, match="nesting depth"):
        BaseModelView._parse_filter_string(_nested(1000))


# ── Empty / whitespace input ──────────────────────────────────────────────────


@pytest.mark.parametrize("raw", ["", "   ", "\t", "\n"])
def test_empty_or_whitespace_raises_value_error(raw: str):
    """Empty or whitespace-only strings raise ValueError (documented behavior)."""
    with pytest.raises(ValueError, match="empty filter"):
        BaseModelView._parse_filter_string(raw)


# ── Malformed tokens ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        "no_double_underscore",
        "a__",
        "__eq=val",
        "=value",
        "a__eq=",
        "a__eq=val AND",
        "a__eq=val OR",
        "AND",
        "OR",
        "AND OR AND",
        "a__eq=val AND AND b__eq=2",
    ],
)
def test_malformed_tokens_do_not_crash(raw: str):
    """Malformed input either raises ValueError or returns a (possibly partial) dict."""
    try:
        result = BaseModelView._parse_filter_string(raw)
        assert result is None or isinstance(result, dict)
    except ValueError:
        pass  # also acceptable


# ── Unbalanced parentheses ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        "(",
        ")",
        "(a__eq=1",
        "a__eq=1)",
        "((a__eq=1)",
        "(a__eq=1))",
        "(((",
        ")))",
    ],
)
def test_unbalanced_parens_do_not_crash(raw: str):
    """Unbalanced parentheses do not crash the parser."""
    try:
        result = BaseModelView._parse_filter_string(raw)
        assert result is None or isinstance(result, dict)
    except ValueError:
        pass


# ── Null bytes and unusual characters ────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        "a__eq=\x00",
        "\x00a__eq=1",
        "a__eq=val\x00ue",
        "a\x00__eq=1",
        "a__eq=\xff\xfe",
    ],
)
def test_null_and_control_chars_do_not_crash(raw: str):
    """Null bytes and non-ASCII bytes in input do not crash the parser."""
    try:
        result = BaseModelView._parse_filter_string(raw)
        assert result is None or isinstance(result, dict)
    except ValueError:
        pass


# ── Very long input ───────────────────────────────────────────────────────────


def test_very_long_leaf_value():
    """A leaf with a 100,000-character value parses without error."""
    raw = "a__eq=" + "x" * 100_000
    result = BaseModelView._parse_filter_string(raw)
    assert isinstance(result, dict)
    assert result["value"] == "x" * 100_000


def test_very_long_and_chain():
    """A long chain of AND-joined leaves parses without stack overflow."""
    terms = " AND ".join(f"a__eq={i}" for i in range(500))
    result = BaseModelView._parse_filter_string(terms)
    assert isinstance(result, dict)
