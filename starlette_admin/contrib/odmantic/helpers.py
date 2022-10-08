import datetime
import decimal
import inspect
import typing as t
from enum import Enum
from typing import Dict, Optional, get_origin

import bson
import pydantic as pyd
from odmantic.field import (
    FieldProxy,
    ODMBaseField,
    ODMEmbedded,
    ODMEmbeddedGeneric,
    ODMReference,
)
from pydantic import ValidationError
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
    IntegerField,
    JSONField,
    ListField,
    StringField,
    TimeField,
    URLField, HasOne,
)
from starlette_admin.exceptions import FormValidationError
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
    datetime.date: DateField,
    datetime.time: TimeField,
    datetime.timedelta: IntegerField,
    t.Dict: JSONField,
    pyd.EmailStr: EmailField,
    pyd.NameEmail: StringField,
    Color: ColorField,
    pyd.Json: JSONField,
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
    else:
        types = inspect.getmro(annotation)
        for _type in types:
            if issubclass(_type, Enum):
                admin_field = EnumField.from_enum(field_name, _type)
                break
            elif annotation_map.get(_type) is not None:
                admin_field = annotation_map.get(_type)(field_name)
                break
    if admin_field is None:
        raise ValueError()
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


comparison_map = {
    "eq": "$eq",
    "neq": "$ne",
    "ge": "$gte",
    "gt": "$gt",
    "le": "$lte",
    "lt": "$lt",
    "in": "$in",
    "not_in": "$nin",
}


def build_raw_query(dt_query: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    raw_query: t.Dict[str, t.Any] = dict()
    for key in dt_query:
        if key == "or":
            raw_query["$or"] = [build_raw_query(q) for q in dt_query[key]]
        elif key == "and":
            raw_query["$and"] = [build_raw_query(q) for q in dt_query[key]]
        elif key == "not":
            raw_query["$not"] = build_raw_query(dt_query[key])
        elif key == "between":
            values = dt_query[key]
            raw_query = {"$gte": values[0], "$lte": values[1]}
        elif key == "not_between":
            values = dt_query[key]
            raw_query = {"$not": {"$gte": values[0], "$lte": values[1]}}
        elif key == "contains":
            raw_query = {"$regex": dt_query[key], "$options": "mi"}
        elif key == "startsWith":
            raw_query = {"$regex": "^%s" % dt_query[key], "$options": "mi"}
        elif key == "endsWith":
            raw_query = {"$regex": "%s$" % dt_query[key], "$options": "mi"}
        elif key in comparison_map:
            raw_query[comparison_map[key]] = dt_query[key]
        else:
            raw_query[key] = build_raw_query(dt_query[key])
    return raw_query


def pydantic_error_to_form_validation_errors(exc: ValidationError):
    errors: Dict[str, str] = dict()
    for pydantic_error in exc.errors():
        errors[str(pydantic_error["loc"][-1])] = pydantic_error["msg"]
    return FormValidationError(errors)
