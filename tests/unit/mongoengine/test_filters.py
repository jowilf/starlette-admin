"""Unit tests for starlette_admin.contrib.mongoengine.filters.

No live MongoDB connection required: covers parse_value helpers, apply()
Q-fragment shapes, filter registry registrations, and build_filter_query
behavior with a stub registry.
"""

import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from starlette_admin.contrib.mongoengine.fields import ObjectIdField
from starlette_admin.contrib.mongoengine.filters import (
    ArrayInFilter,
    ArrayNotInFilter,
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
    InFilter,
    IsFalseFilter,
    IsNotNullFilter,
    IsNullFilter,
    IsTrueFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    MongoEngineFilterRegistry,
    NotContainsFilter,
    NotEqualFilter,
    NotInFilter,
    NumericEqualFilter,
    NumericNotEqualFilter,
    ObjectIdEqualFilter,
    ObjectIdInFilter,
    ObjectIdNotEqualFilter,
    ObjectIdNotInFilter,
    StartsWithFilter,
    _parse_object_id,
    _parse_object_id_list,
    build_filter_query,
)
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    RelationField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.filters import FilterGroup, FilterRule, FilterValidationError
from starlette_admin.filters.base import FilterApplyContext

filter_registry = MongoEngineFilterRegistry()

_VALID_OID = "507f1f77bcf86cd799439011"
_VALID_OID2 = "507f191e810c19729de860ea"


# _parse_object_id


def test_parse_object_id_valid():
    result = _parse_object_id(_VALID_OID)
    assert isinstance(result, ObjectId)
    assert str(result) == _VALID_OID


def test_parse_object_id_strips_whitespace():
    result = _parse_object_id(f"  {_VALID_OID}  ")
    assert str(result) == _VALID_OID


def test_parse_object_id_invalid_raises():
    with pytest.raises(FilterValidationError, match="Invalid ObjectId"):
        _parse_object_id("not-an-objectid")


def test_parse_object_id_empty_raises():
    with pytest.raises(FilterValidationError, match="Invalid ObjectId"):
        _parse_object_id("")


# _parse_object_id_list


def test_parse_object_id_list_csv():
    result = _parse_object_id_list(f"{_VALID_OID},{_VALID_OID2}")
    assert result == [ObjectId(_VALID_OID), ObjectId(_VALID_OID2)]


def test_parse_object_id_list_python_list():
    result = _parse_object_id_list([_VALID_OID, _VALID_OID2])
    assert result == [ObjectId(_VALID_OID), ObjectId(_VALID_OID2)]


def test_parse_object_id_list_strips_spaces():
    result = _parse_object_id_list(f"  {_VALID_OID} , {_VALID_OID2} ")
    assert result == [ObjectId(_VALID_OID), ObjectId(_VALID_OID2)]


def test_parse_object_id_list_empty_raises():
    with pytest.raises(FilterValidationError, match="At least one value"):
        _parse_object_id_list("")


def test_parse_object_id_list_invalid_entry_raises():
    with pytest.raises(FilterValidationError, match="Invalid ObjectId in list"):
        _parse_object_id_list(f"{_VALID_OID},bad-id")


# ObjectIdEqualFilter


def test_object_id_equal_filter_parse_value():
    f = ObjectIdEqualFilter()
    result = f.parse_value(_VALID_OID)
    assert isinstance(result, ObjectId)
    assert str(result) == _VALID_OID


def test_object_id_equal_filter_apply():
    oid = ObjectId(_VALID_OID)
    ctx = FilterApplyContext(query=None, field_name="ref_id", value=oid)
    q = ObjectIdEqualFilter().apply(ctx)
    assert q.query == {"ref_id": oid}


def test_object_id_equal_filter_meta():
    f = ObjectIdEqualFilter()
    assert f.name == "eq"


# ObjectIdNotEqualFilter


def test_object_id_not_equal_filter_parse_value():
    f = ObjectIdNotEqualFilter()
    result = f.parse_value(_VALID_OID)
    assert isinstance(result, ObjectId)


def test_object_id_not_equal_filter_apply():
    oid = ObjectId(_VALID_OID)
    ctx = FilterApplyContext(query=None, field_name="ref_id", value=oid)
    q = ObjectIdNotEqualFilter().apply(ctx)
    assert q.query == {"ref_id__ne": oid}


def test_object_id_not_equal_filter_meta():
    assert ObjectIdNotEqualFilter.name == "neq"


# ObjectIdInFilter


def test_object_id_in_filter_parse_value_csv():
    f = ObjectIdInFilter()
    result = f.parse_value(f"{_VALID_OID},{_VALID_OID2}")
    assert result == [ObjectId(_VALID_OID), ObjectId(_VALID_OID2)]


def test_object_id_in_filter_parse_value_list():
    f = ObjectIdInFilter()
    result = f.parse_value([_VALID_OID])
    assert result == [ObjectId(_VALID_OID)]


def test_object_id_in_filter_apply():
    oids = [ObjectId(_VALID_OID), ObjectId(_VALID_OID2)]
    ctx = FilterApplyContext(query=None, field_name="ref_id", value=oids)
    q = ObjectIdInFilter().apply(ctx)
    assert q.query == {"ref_id__in": oids}


def test_object_id_in_filter_meta():
    assert ObjectIdInFilter.name == "in"


# ObjectIdNotInFilter


def test_object_id_not_in_filter_parse_value():
    f = ObjectIdNotInFilter()
    result = f.parse_value(_VALID_OID)
    assert result == [ObjectId(_VALID_OID)]


def test_object_id_not_in_filter_apply():
    oids = [ObjectId(_VALID_OID)]
    ctx = FilterApplyContext(query=None, field_name="ref_id", value=oids)
    q = ObjectIdNotInFilter().apply(ctx)
    assert q.query == {"ref_id__nin": oids}


def test_object_id_not_in_filter_meta():
    assert ObjectIdNotInFilter.name == "not_in"


# generic filter apply() coverage


def _ctx(field_name: str, value: Any, value2: Any | None = None) -> FilterApplyContext:
    return FilterApplyContext(
        query=None, field_name=field_name, value=value, value2=value2
    )


def test_equal_filter_apply():
    q = EqualFilter().apply(_ctx("status", "active"))
    assert q.query == {"status": "active"}


def test_not_equal_filter_apply():
    q = NotEqualFilter().apply(_ctx("status", "active"))
    assert q.query == {"status__ne": "active"}


def test_is_null_filter_apply():
    q = IsNullFilter().apply(_ctx("status", None))
    assert q.query == {"status": None}


def test_is_not_null_filter_apply():
    q = IsNotNullFilter().apply(_ctx("status", None))
    assert q.query == {"status__ne": None}


# string filter apply() coverage


def test_contains_filter_apply():
    q = ContainsFilter().apply(_ctx("title", "foo"))
    assert q.query == {"title__icontains": "foo"}


def test_not_contains_filter_apply():
    q = NotContainsFilter().apply(_ctx("title", "foo"))
    assert q.query == {"title__not__icontains": "foo"}


def test_starts_with_filter_apply():
    q = StartsWithFilter().apply(_ctx("title", "foo"))
    assert q.query == {"title__istartswith": "foo"}


def test_ends_with_filter_apply():
    q = EndsWithFilter().apply(_ctx("title", "foo"))
    assert q.query == {"title__iendswith": "foo"}


# numeric filter apply() coverage


def test_numeric_equal_filter_apply():
    q = NumericEqualFilter().apply(_ctx("count", 5))
    assert q.query == {"count": 5}


def test_numeric_not_equal_filter_apply():
    q = NumericNotEqualFilter().apply(_ctx("count", 5))
    assert q.query == {"count__ne": 5}


def test_greater_than_filter_apply():
    q = GreaterThanFilter().apply(_ctx("count", 5))
    assert q.query == {"count__gt": 5}


def test_less_than_filter_apply():
    q = LessThanFilter().apply(_ctx("count", 5))
    assert q.query == {"count__lt": 5}


def test_greater_than_or_equal_filter_apply():
    q = GreaterThanOrEqualFilter().apply(_ctx("count", 5))
    assert q.query == {"count__gte": 5}


def test_less_than_or_equal_filter_apply():
    q = LessThanOrEqualFilter().apply(_ctx("count", 5))
    assert q.query == {"count__lte": 5}


def test_between_filter_apply():
    q = BetweenFilter().apply(_ctx("count", 1, 10))
    assert [c.query for c in q.children] == [
        {"count__gte": 1},
        {"count__lte": 10},
    ]


# date / datetime filter apply() coverage


def test_date_equal_filter_apply():
    value = datetime.date(2024, 1, 15)
    q = DateEqualFilter().apply(_ctx("created_on", value))
    assert q.query == {"created_on": value}


def test_datetime_equal_filter_apply():
    value = datetime.datetime(2024, 1, 15, 10, 30)
    q = DateTimeEqualFilter().apply(_ctx("created_at", value))
    assert q.query == {"created_at": value}


def test_date_between_filter_apply():
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 1, 31)
    q = DateBetweenFilter().apply(_ctx("created_on", start, end))
    assert [c.query for c in q.children] == [
        {"created_on__gte": start},
        {"created_on__lte": end},
    ]


def test_datetime_between_filter_apply():
    start = datetime.datetime(2024, 1, 1, 0, 0)
    end = datetime.datetime(2024, 1, 31, 23, 59)
    q = DateTimeBetweenFilter().apply(_ctx("created_at", start, end))
    assert [c.query for c in q.children] == [
        {"created_at__gte": start},
        {"created_at__lte": end},
    ]


def test_date_in_past_filter_apply():
    q = DateInPastFilter().apply(_ctx("created_on", None))
    assert "created_on__lt" in q.query


def test_date_in_future_filter_apply():
    q = DateInFutureFilter().apply(_ctx("created_on", None))
    assert "created_on__gt" in q.query


# boolean filter apply() coverage


def test_is_true_filter_apply():
    q = IsTrueFilter().apply(_ctx("active", True))
    assert q.query == {"active": True}


def test_is_false_filter_apply():
    q = IsFalseFilter().apply(_ctx("active", False))
    assert q.query == {"active": False}


# array / enum filter apply() coverage


def test_array_in_filter_apply():
    q = ArrayInFilter().apply(_ctx("tags", ["a", "b"]))
    assert q.query == {"tags__in": ["a", "b"]}


def test_array_not_in_filter_apply():
    q = ArrayNotInFilter().apply(_ctx("tags", ["a", "b"]))
    assert q.query == {"tags__nin": ["a", "b"]}


def test_in_filter_apply():
    q = InFilter().apply(_ctx("status", ["active", "pending"]))
    assert q.query == {"status__in": ["active", "pending"]}


def test_not_in_filter_apply():
    q = NotInFilter().apply(_ctx("status", ["active", "pending"]))
    assert q.query == {"status__nin": ["active", "pending"]}


# filter_registry registrations for ObjectIdField


def test_registry_object_id_field():
    names = {f.name for f in filter_registry.filters_for(ObjectIdField("x"))}
    assert names == {"eq", "neq", "in", "not_in", "is_null", "is_not_null"}


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


def test_registry_relation_field():
    names = {f.name for f in filter_registry.filters_for(RelationField("x"))}
    assert names == {"is_null", "is_not_null"}


def test_registry_tags_field():
    names = {f.name for f in filter_registry.filters_for(TagsField("x"))}
    assert names == {"in", "not_in", "is_null", "is_not_null"}


# build_filter_query edge cases


class _DummyView:
    model = None


def test_build_filter_query_empty_group():
    result = build_filter_query(
        FilterGroup(logic="and", rules=[]),
        {"oid": ObjectIdField("oid")},
        filter_registry,
        _DummyView(),
        MagicMock(),
    )
    assert result is None


def test_build_filter_query_unknown_filter_returns_none():
    from starlette_admin.filters.registry import FilterRegistry

    empty = FilterRegistry()
    empty.register(ObjectIdField)

    result = build_filter_query(
        FilterGroup(
            logic="and",
            rules=[FilterRule(field="oid", filter="eq", value=_VALID_OID)],
        ),
        {"oid": ObjectIdField("oid")},
        empty,
        _DummyView(),
        MagicMock(),
    )
    assert result is None


# ObjectIdField


def test_object_id_field_is_string_field_subclass():
    assert issubclass(ObjectIdField, StringField)


def test_object_id_field_instantiation():
    f = ObjectIdField("my_id")
    assert f.name == "my_id"
