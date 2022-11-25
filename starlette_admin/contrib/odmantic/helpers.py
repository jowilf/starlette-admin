import datetime
import decimal
import inspect
import re
import typing as t
from enum import Enum

import bson
import pydantic as pyd
import pydantic.datetime_parse
from odmantic import Model, query
from odmantic.field import (
    FieldProxy,
    ODMBaseField,
    ODMEmbedded,
    ODMEmbeddedGeneric,
    ODMReference,
)
from odmantic.query import QueryExpression
from pydantic.color import Color
from pydantic.typing import get_args, get_origin
from starlette_admin.contrib.odmantic.exceptions import NotSupportedAnnotation
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    CollectionField,
    ColorField,
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
    URLField,
)
from starlette_admin.helpers import slugify_class_name

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
    datetime.timedelta: IntegerField,
    dict: JSONField,
    pyd.EmailStr: EmailField,
    pyd.NameEmail: StringField,
    Color: ColorField,
    pyd.AnyUrl: URLField,
}


def convert_odm_field_to_admin_field(  # noqa: C901
    field: ODMBaseField, field_name: str, annotation: t.Type[t.Any]
) -> BaseField:
    admin_field: t.Optional[BaseField] = None
    _origin = get_origin(annotation)
    if _origin is t.Union:  # type: ignore
        """Support for Optional"""
        return convert_odm_field_to_admin_field(
            field, field_name, get_args(annotation)[0]
        )
    elif _origin in annotation_map:
        admin_field = annotation_map.get(_origin)(field_name)  # type: ignore
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
                admin_field = annotation_map.get(_type)(field_name)  # type: ignore
                break
    if admin_field is None:
        raise NotSupportedAnnotation(f"{annotation} is not supported")
    admin_field.required = field.is_required_in_doc() and not field.primary_field  # type: ignore
    return admin_field


def normalize_list(arr: t.Optional[t.Sequence[t.Any]]) -> t.Optional[t.Sequence[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, FieldProxy):
            _new_list.append(str(+v))
        elif isinstance(v, str):
            _new_list.append(v)
        else:
            raise ValueError(f"Expected str or FieldProxy, got {type(v).__name__}")
    return _new_list


def _rec(value: t.Any, regex: str) -> t.Pattern:
    return re.compile(regex % re.escape(value), re.IGNORECASE)


OPERATORS: t.Dict[str, t.Callable[[FieldProxy, t.Any], QueryExpression]] = {
    "eq": lambda f, v: f == v,
    "neq": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "gt": lambda f, v: f > v,
    "le": lambda f, v: f <= v,
    "ge": lambda f, v: f >= v,
    "in": lambda f, v: f.in_(v),
    "not_in": lambda f, v: f.not_in(v),
    "startswith": lambda f, v: f.match(_rec(v, r"^%s")),
    "not_startswith": lambda f, v: query.nor_(f.match(_rec(v, r"^%s"))),
    "endswith": lambda f, v: f.match(_rec(v, r"%s$")),
    "not_endswith": lambda f, v: query.nor_(f.match(_rec(v, r"%s$"))),
    "contains": lambda f, v: f.match(_rec(v, r"%s")),
    "not_contains": lambda f, v: query.nor_(f.match(_rec(v, r"%s"))),
    "is_false": lambda f, v: f.eq(False),
    "is_true": lambda f, v: f.eq(True),
    "is_null": lambda f, v: f.eq(None),
    "is_not_null": lambda f, v: f.ne(None),
    "between": lambda f, v: query.and_(f >= v[0], f <= v[1]),
    "not_between": lambda f, v: query.or_(f < v[0], f > v[1]),
}


def resolve_proxy(model: t.Type[Model], proxy_name: str) -> t.Optional[FieldProxy]:
    _list = proxy_name.split(".")
    m = model
    for v in _list:
        if m is not None:
            m = getattr(m, v, None)  # type: ignore
    return m  # type: ignore


def _check_value(v: t.Any, proxy: t.Optional[FieldProxy]) -> t.Any:
    """
    The purpose of this function is to detect datetime string, or ObjectId
    and convert them into the appropriate python type.
    """
    if isinstance(v, str) and pyd.datetime_parse.datetime_re.match(v):
        return datetime.datetime.fromisoformat(v)
    elif proxy is not None and +proxy == "_id" and bson.ObjectId.is_valid(v):
        return bson.ObjectId(v)
    return v


def resolve_deep_query(
    where: t.Dict[str, t.Any],
    model: t.Type[Model],
    field_proxy: t.Optional[FieldProxy] = None,
) -> QueryExpression:
    _all_queries = []
    for key in where:
        if key == "or":
            _all_queries.append(
                query.or_(
                    *[(resolve_deep_query(q, model, field_proxy)) for q in where[key]]
                )
            )
        elif key == "and":
            _all_queries.append(
                query.and_(
                    *[resolve_deep_query(q, model, field_proxy) for q in where[key]]
                )
            )
        elif key in OPERATORS:
            v = where[key]
            v = (
                [_check_value(it, field_proxy) for it in v]
                if isinstance(v, list)
                else _check_value(v, field_proxy)
            )
            _all_queries.append(OPERATORS[key](field_proxy, v))  # type: ignore
        else:
            proxy = resolve_proxy(model, key)
            if proxy is not None:
                _all_queries.append(resolve_deep_query(where[key], model, proxy))
    if len(_all_queries) == 1:
        return _all_queries[0]
    return query.and_(*_all_queries) if _all_queries else QueryExpression({})
