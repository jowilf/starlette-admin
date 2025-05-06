from typing import List, Optional

import pymongo
import pytest
from beanie import Link
from pydantic import BaseModel
from starlette_admin.contrib.beanie.helpers import (
    BeanieLogicalOperator,
    build_order_clauses,
    is_list_of_links_type,
    isvalid_field,
)


class Toy(BaseModel):
    name: str
    color: str


class Child(BaseModel):
    toy: Toy
    age: int


class Parent(BaseModel):
    child: Child
    age: int


class Car(BaseModel):
    passengers: Optional[List[Link["Parent"]]] = None


class TestBeanieHelpers:

    async def test_beanie_logical_operator_not_empty(self):
        operator = BeanieLogicalOperator(None)

        with pytest.raises(ValueError):
            _ = operator.query

    async def test_isvalid_field(self):

        parent1 = Parent(child=Child(toy=Toy(name="car", color="red"), age=5), age=30)

        assert isvalid_field(parent1, "child.toy.name")
        assert isvalid_field(parent1, "child.toy.color")
        assert isvalid_field(parent1, "child.toy")
        assert isvalid_field(parent1, "child.age")
        assert isvalid_field(parent1, "child")
        assert isvalid_field(parent1, "age")

        assert not isvalid_field(parent1, "child.toy.unknown")
        assert not isvalid_field(parent1, "child.unknown")
        assert not isvalid_field(parent1, "unknown")
        assert not isvalid_field(parent1, "__dict__")

    async def test_is_list_of_links_type(self):
        assert is_list_of_links_type(Car.model_fields["passengers"].annotation)
        assert not is_list_of_links_type(Parent.model_fields["child"].annotation)
        assert not is_list_of_links_type(Parent.model_fields["age"].annotation)

    async def test_build_order_clauses(self):
        assert build_order_clauses(["name desc", "age desc"]) == [
            ("name", pymongo.DESCENDING),
            ("age", pymongo.DESCENDING),
        ]
        assert build_order_clauses(["name asc", "age asc"]) == [
            ("name", pymongo.ASCENDING),
            ("age", pymongo.ASCENDING),
        ]
        assert build_order_clauses(["name asc", "age desc"]) == [
            ("name", pymongo.ASCENDING),
            ("age", pymongo.DESCENDING),
        ]
        assert build_order_clauses(["name desc", "age asc"]) == [
            ("name", pymongo.DESCENDING),
            ("age", pymongo.ASCENDING),
        ]
        assert build_order_clauses([]) == []

        assert build_order_clauses(["id desc"]) == [("_id", pymongo.DESCENDING)]
        assert build_order_clauses(["id asc"]) == [("_id", pymongo.ASCENDING)]
