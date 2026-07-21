"""Unit tests for starlette_admin.contrib.beanie.filters.

All tests here call filter methods directly without a running MongoDB instance,
targeting the branches that are not exercised by the integration tests in
tests/integration/beanie/test_view.py::TestBeanieFilters.
"""

import datetime
import re

import pytest
from bson import ObjectId
from starlette_admin.contrib.beanie.fields import BeanieObjectIdField
from starlette_admin.contrib.beanie.filters import (
    ArrayInFilter,
    ArrayNotInFilter,
    BeanieFilterRegistry,
    BetweenFilter,
    ContainsFilter,
    DateBetweenFilter,
    DateEqualFilter,
    DateInFutureFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    EndsWithFilter,
    EqualFilter,
    GreaterThanFilter,
    GreaterThanOrEqualFilter,
    IsFalseFilter,
    IsNotNullFilter,
    IsNullFilter,
    IsTrueFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    NotContainsFilter,
    NotEqualFilter,
    NumericEqualFilter,
    NumericNotEqualFilter,
    ObjectIdEqualFilter,
    ObjectIdInFilter,
    ObjectIdNotEqualFilter,
    ObjectIdNotInFilter,
    StartsWithFilter,
    StringEqualFilter,
    StringNotEqualFilter,
    _parse_object_id,
    _parse_object_id_list,
    build_filter_query,
)
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    StringField,
    TextAreaField,
)
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRegistry,
    FilterRule,
    FilterValidationError,
)

filter_registry = BeanieFilterRegistry()


def _ctx(field_name: str = "field", value=None, value2=None) -> FilterApplyContext:
    return FilterApplyContext(
        query=None, field_name=field_name, value=value, value2=value2
    )


class TestGenericFilters:
    async def test_not_equal(self):
        assert NotEqualFilter().apply(_ctx(value="bar")) == {"field": {"$ne": "bar"}}

    async def test_equal(self):
        assert EqualFilter().apply(_ctx(value="foo")) == {"field": "foo"}

    async def test_is_null(self):
        assert IsNullFilter().apply(_ctx()) == {"field": None}

    async def test_is_not_null(self):
        assert IsNotNullFilter().apply(_ctx()) == {"field": {"$ne": None}}


class TestStringFilters:
    async def test_contains(self):
        result = ContainsFilter().apply(_ctx(value="hello"))
        assert result == {"field": {"$regex": re.escape("hello"), "$options": "i"}}

    async def test_not_contains(self):
        result = NotContainsFilter().apply(_ctx(value="hello"))
        assert "$not" in result["field"]

    async def test_starts_with(self):
        result = StartsWithFilter().apply(_ctx(value="hel"))
        assert result["field"]["$regex"].startswith("^")

    async def test_ends_with(self):
        result = EndsWithFilter().apply(_ctx(value="llo"))
        assert result["field"]["$regex"].endswith("$")

    async def test_string_equal(self):
        result = StringEqualFilter().apply(_ctx(value="foo"))
        assert result["field"]["$options"] == "i"
        assert result["field"]["$regex"] == f"^{re.escape('foo')}$"

    async def test_string_not_equal(self):
        result = StringNotEqualFilter().apply(_ctx(value="foo"))
        assert "$not" in result["field"]


class TestNumericFilters:
    async def test_numeric_equal(self):
        assert NumericEqualFilter().apply(_ctx(value=42)) == {"field": 42}

    async def test_numeric_not_equal(self):
        assert NumericNotEqualFilter().apply(_ctx(value=42)) == {"field": {"$ne": 42}}

    async def test_greater_than(self):
        assert GreaterThanFilter().apply(_ctx(value=10)) == {"field": {"$gt": 10}}

    async def test_less_than(self):
        assert LessThanFilter().apply(_ctx(value=10)) == {"field": {"$lt": 10}}

    async def test_greater_than_or_equal(self):
        assert GreaterThanOrEqualFilter().apply(_ctx(value=10)) == {
            "field": {"$gte": 10}
        }

    async def test_less_than_or_equal(self):
        assert LessThanOrEqualFilter().apply(_ctx(value=10)) == {"field": {"$lte": 10}}

    async def test_between(self):
        assert BetweenFilter().apply(_ctx(value=1, value2=10)) == {
            "field": {"$gte": 1, "$lte": 10}
        }


class TestDateFilters:
    async def test_date_equal(self):
        d = datetime.date(2024, 1, 1)
        assert DateEqualFilter().apply(_ctx(value=d)) == {"field": d}

    async def test_datetime_equal(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0)
        assert DateTimeEqualFilter().apply(_ctx(value=dt)) == {"field": dt}

    async def test_date_between(self):
        d1, d2 = datetime.date(2024, 1, 1), datetime.date(2024, 12, 31)
        assert DateBetweenFilter().apply(_ctx(value=d1, value2=d2)) == {
            "field": {"$gte": d1, "$lte": d2}
        }

    async def test_datetime_between(self):
        dt1 = datetime.datetime(2024, 1, 1)
        dt2 = datetime.datetime(2024, 12, 31)
        assert DateTimeBetweenFilter().apply(_ctx(value=dt1, value2=dt2)) == {
            "field": {"$gte": dt1, "$lte": dt2}
        }

    async def test_date_in_past(self):
        result = DateInPastFilter().apply(_ctx())
        assert "$lt" in result["field"]

    async def test_date_in_future(self):
        result = DateInFutureFilter().apply(_ctx())
        assert "$gt" in result["field"]


class TestBooleanFilters:
    async def test_is_true(self):
        assert IsTrueFilter().apply(_ctx()) == {"field": True}

    async def test_is_false(self):
        assert IsFalseFilter().apply(_ctx()) == {"field": False}


class TestArrayFilters:
    async def test_array_in(self):
        assert ArrayInFilter().apply(_ctx(value=["a", "b"])) == {
            "field": {"$in": ["a", "b"]}
        }

    async def test_array_not_in(self):
        assert ArrayNotInFilter().apply(_ctx(value=["a", "b"])) == {
            "field": {"$nin": ["a", "b"]}
        }


class TestObjectIdFilters:
    @pytest.fixture
    def oid(self):
        return ObjectId()

    async def test_equal_apply(self, oid):
        assert ObjectIdEqualFilter().apply(_ctx(value=oid)) == {"field": oid}

    async def test_not_equal_parse_value(self, oid):
        assert ObjectIdNotEqualFilter().parse_value(str(oid)) == oid

    async def test_not_equal_apply(self, oid):
        assert ObjectIdNotEqualFilter().apply(_ctx(value=oid)) == {
            "field": {"$ne": oid}
        }

    async def test_in_apply(self, oid):
        assert ObjectIdInFilter().apply(_ctx(value=[oid])) == {"field": {"$in": [oid]}}

    async def test_not_in_parse_value(self, oid):
        assert ObjectIdNotInFilter().parse_value([str(oid)]) == [oid]

    async def test_not_in_apply(self, oid):
        assert ObjectIdNotInFilter().apply(_ctx(value=[oid])) == {
            "field": {"$nin": [oid]}
        }


class TestParseObjectId:
    async def test_valid(self):
        oid = ObjectId()
        assert _parse_object_id(str(oid)) == oid

    async def test_invalid_string_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid ObjectId"):
            _parse_object_id("not-a-valid-id")

    async def test_none_raises(self):
        with pytest.raises(FilterValidationError):
            _parse_object_id(None)


class TestParseObjectIdList:
    async def test_list_input(self):
        ids = [ObjectId(), ObjectId()]
        assert _parse_object_id_list([str(i) for i in ids]) == ids

    async def test_string_csv_input(self):
        ids = [ObjectId(), ObjectId()]
        csv = ",".join(str(i) for i in ids)
        assert _parse_object_id_list(csv) == ids

    async def test_empty_list_raises(self):
        with pytest.raises(FilterValidationError, match="At least one value"):
            _parse_object_id_list([])

    async def test_blank_csv_raises(self):
        with pytest.raises(FilterValidationError, match="At least one value"):
            _parse_object_id_list(" , ")

    async def test_invalid_in_list_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid ObjectId in list"):
            _parse_object_id_list(["not-valid"])


class TestBuildFilterQuery:
    def _registry(self):
        reg = FilterRegistry()
        reg.register(StringField, EqualFilter)
        return reg

    def _fields(self):
        return {"name": StringField("name")}

    async def test_empty_group_returns_none(self):
        group = FilterGroup(logic="and", rules=[])
        assert build_filter_query(group, {}, FilterRegistry(), None, None) is None

    async def test_all_rules_skipped_returns_none(self):
        # Unknown filter name → _build_rule_query returns None → fragments empty
        group = FilterGroup(
            logic="and",
            rules=[FilterRule(field="name", filter="unknown_op", value="x")],
        )
        result = build_filter_query(group, self._fields(), self._registry(), None, None)
        assert result is None

    async def test_single_rule_returned_unwrapped(self):
        # One fragment must not be wrapped in {"$and": [...]}
        group = FilterGroup(
            logic="and",
            rules=[FilterRule(field="name", filter="eq", value="Alice")],
        )
        result = build_filter_query(group, self._fields(), self._registry(), None, None)
        assert result == {"name": "Alice"}

    async def test_multiple_rules_and(self):
        group = FilterGroup(
            logic="and",
            rules=[
                FilterRule(field="name", filter="eq", value="Alice"),
                FilterRule(field="name", filter="eq", value="Bob"),
            ],
        )
        result = build_filter_query(group, self._fields(), self._registry(), None, None)
        assert result == {"$and": [{"name": "Alice"}, {"name": "Bob"}]}

    async def test_multiple_rules_or(self):
        group = FilterGroup(
            logic="or",
            rules=[
                FilterRule(field="name", filter="eq", value="Alice"),
                FilterRule(field="name", filter="eq", value="Bob"),
            ],
        )
        result = build_filter_query(group, self._fields(), self._registry(), None, None)
        assert result == {"$or": [{"name": "Alice"}, {"name": "Bob"}]}

    async def test_id_field_remapped_to_underscore_id(self):
        oid = ObjectId()
        reg = FilterRegistry()
        reg.register(BeanieObjectIdField, ObjectIdEqualFilter)
        fields = {"id": BeanieObjectIdField("id")}
        group = FilterGroup(
            logic="and",
            rules=[FilterRule(field="id", filter="eq", value=oid)],
        )
        result = build_filter_query(group, fields, reg, None, None)
        assert result == {"_id": oid}


def test_registry_base_field_fallback():
    """A field type with no dedicated registration still gets null filters."""
    names = {f.name for f in filter_registry.filters_for(BaseField("x"))}
    assert names == {"is_null", "is_not_null"}


def test_registry_textarea_field():
    names = {f.name for f in filter_registry.filters_for(TextAreaField("x"))}
    assert names == {
        "contains",
        "not_contains",
        "startswith",
        "endswith",
        "is_null",
        "is_not_null",
    }


def test_registry_date_field():
    names = {f.name for f in filter_registry.filters_for(DateField("x"))}
    assert names == {"eq", "between", "in_past", "in_future", "is_null", "is_not_null"}


def test_registry_boolean_field():
    names = {f.name for f in filter_registry.filters_for(BooleanField("x"))}
    assert names == {"is_true", "is_false", "is_null", "is_not_null"}


def test_register_filters_plugin_api():
    """`register_filters` (the plugin API) extends every new
    `BeanieFilterRegistry` instance, since it feeds `_external_filters`."""
    from starlette_admin.contrib.beanie import filters as beanie_filters

    class _PluginField(BaseField):
        pass

    class _PluginFilter(ContainsFilter):
        name = "plugin-filter"

    beanie_filters.register_filters(_PluginField, _PluginFilter)
    try:
        registry = BeanieFilterRegistry()
        assert registry.filters_for(_PluginField("x")) == [_PluginFilter]
    finally:
        del beanie_filters._EXTERNAL_FILTERS[_PluginField]
