import asyncio
import datetime
import decimal
import inspect
import typing as t
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, get_origin

import bson
import pydantic as pyd
from odmantic import EmbeddedModel, Model, SyncEngine, query
from odmantic.field import (
    FieldProxy,
    ODMBaseField,
    ODMEmbedded,
    ODMEmbeddedGeneric,
    ODMReference,
)
from odmantic.query import QueryExpression
from pydantic.color import Color
from pydantic.typing import get_args
from starlette_admin import (
    BaseField,
    BooleanField,
    CollectionField,
    ColorField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    EnumField,
    FloatField,
    HasOne,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    TimeField,
    URLField,
)
from starlette_admin.contrib.odmantic.exceptions import NotSupportedAnnotation
from starlette_admin.helpers import slugify_class_name
from wtforms.validators import Optional

annotation_map = {
    bson.ObjectId: StringField,
    bool: BooleanField,
    int: IntegerField,
    bson.Int64: IntegerField,
    float: FloatField,
    bson.Decimal128: DecimalField,
    decimal.Decimal: DecimalField,
    str: StringField,
    t.Pattern: StringField,
    bson.Regex: StringField,
    bytes: StringField,
    bson.Binary: StringField,
    datetime.datetime: DateTimeField,
    datetime.date: DateField,
    datetime.time: TimeField,
    datetime.timedelta: IntegerField,
    dict: JSONField,
    pyd.EmailStr: EmailField,
    pyd.NameEmail: StringField,
    Color: ColorField,
    pyd.AnyUrl: URLField,
}


def convert_odm_field_to_admin_field(
    field: ODMBaseField, field_name: str, annotation: t.Type[t.Any]
) -> BaseField:
    admin_field: Optional[BaseField] = None
    _origin = get_origin(annotation)
    if _origin is t.Union:
        """Support for Optional"""
        return convert_odm_field_to_admin_field(
            field, field_name, get_args(annotation)[0]
        )
    elif _origin in annotation_map:
        admin_field = annotation_map.get(_origin)(field_name)
    elif _origin in (list, set) and not isinstance(field, ODMEmbeddedGeneric):
        child_field = convert_odm_field_to_admin_field(
            field, field_name, get_args(annotation)[0]
        )
        if isinstance(child_field, EnumField):
            child_field.multiple = True
            admin_field = child_field
        else:
            admin_field = ListField(child_field)
    elif isinstance(field, (ODMEmbedded, ODMEmbeddedGeneric)):
        _type = field.model
        _fields = []
        for _field_name in list(_type.__odm_fields__.keys()):
            _fields.append(
                convert_odm_field_to_admin_field(
                    _type.__odm_fields__[_field_name],
                    _field_name,
                    _type.__annotations__[_field_name],
                )
            )
        admin_field = CollectionField(field_name, fields=_fields)
        if isinstance(field, ODMEmbeddedGeneric):
            admin_field = ListField(admin_field)
    elif isinstance(field, ODMReference):
        return HasOne(field_name, identity=slugify_class_name(field.model.__name__))
    elif hasattr(annotation, "__mro__"):
        types = inspect.getmro(annotation)
        for _type in types:
            if issubclass(_type, Enum):
                admin_field = EnumField.from_enum(field_name, _type)
                break
            elif annotation_map.get(_type) is not None:
                admin_field = annotation_map.get(_type)(field_name)
                break
    if admin_field is None:
        raise NotSupportedAnnotation(f"{annotation} is not supported")
    admin_field.required = field.is_required_in_doc()
    return admin_field


def normalize_list(arr: t.Optional[t.List[t.Any]]) -> t.Optional[t.List[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, FieldProxy):
            _new_list.append(+v)
        elif isinstance(v, str):
            _new_list.append(v)
        else:
            raise ValueError(
                f"Expected str or monogoengine.BaseField, got {type(v).__name__}"
            )
    return _new_list


OPERATORS: Dict[str, Callable[[FieldProxy, Any], QueryExpression]] = {
    "eq": lambda f, v: f == v,
    "neq": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "gt": lambda f, v: f > v,
    "le": lambda f, v: f <= v,
    "ge": lambda f, v: f >= v,
    "in": lambda f, v: f.in_(v),
    "not_in": lambda f, v: f.not_in(v),
    "startswith": lambda f, v: f.match(r"^%s" % v),
    "not_startswith": lambda f, v: query.nor_(f.match(r"^%s" % v)),
    "endswith": lambda f, v: f.match(r"%s$" % v),
    "not_endswith": lambda f, v: query.nor_(f.match(r"%s$" % v)),
    "contains": lambda f, v: f.match(r"%s" % v),
    "not_contains": lambda f, v: query.nor_(f.match(r"%s" % v)),
    "is_null": lambda f, v: f == None,  # noqa E711
    "is_not_null": lambda f, v: f != None,  # noqa E711
    "between": lambda f, v: query.and_(f >= v[0] , f <= v[1]),
    "not_between": lambda f, v: query.or_(f <= v[0] , f >= v[1])
}


def resolve_proxy(model: Type[Model], proxy_name: str) -> FieldProxy:
    _list = proxy_name.split(".")
    m, p = model, None
    for v in _list:
        if m is not None:
            m = getattr(m, v, None)
    return m


def resolve_query(
    dt_query: t.Dict[str, t.Any],
    model: t.Type[Model],
    field_proxy: t.Optional[FieldProxy] = None,
) -> t.Optional[QueryExpression]:
    _all_queries = []
    for key in dt_query:
        if key == "or":
            _all_queries.append(
                query.or_(
                    *[(resolve_query(q, model, field_proxy)) for q in dt_query[key]]
                )
            )
        elif key == "and":
            _all_queries.append(
                query.and_(
                    *[resolve_query(q, model, field_proxy) for q in dt_query[key]]
                )
            )
        elif key in OPERATORS:
            _all_queries.append(OPERATORS[key](field_proxy, dt_query[key]))
        else:
            proxy = resolve_proxy(model, key)
            if proxy is not None:
                _all_queries.append(resolve_query(dt_query[key], model, proxy))
    if len(_all_queries) == 1:
        return _all_queries[0]
    return query.and_(*_all_queries) if _all_queries else QueryExpression({})

if __name__ == "__main__":

    class CapitalCity(EmbeddedModel):
        name: str
        population: int

    class Country(Model):
        name: str
        currency: str
        capital_city: List[CapitalCity]

    engine = SyncEngine()
    q = resolve_query(
        {"and": [{"id": {"lt": 50}}, {"capital_city.name": {"startswith": "b"}}]},
        Country,
    )
    print(q)
    print(list(engine.find(Country, asyncio.run(q))))
