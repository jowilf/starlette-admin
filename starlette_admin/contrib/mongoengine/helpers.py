from typing import Any, Dict, List, Optional

import mongoengine.fields as me
import starlette_admin as sa
from mongoengine.base.fields import BaseField as MongoBaseField
from starlette_admin import TagsField
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField
from starlette_admin.helpers import slugify_class_name

mongoengine_to_admin_map = {
    me.ObjectIdField: sa.StringField,
    me.StringField: sa.StringField,
    me.IntField: sa.IntegerField,
    me.LongField: sa.IntegerField,
    me.FloatField: sa.FloatField,
    me.BooleanField: sa.BooleanField,
    me.DateTimeField: sa.DateTimeField,
    me.DateField: sa.DateField,
    me.ComplexDateTimeField: sa.DateTimeField,
    me.DecimalField: sa.DecimalField,
    me.EmailField: sa.EmailField,
    me.UUIDField: sa.StringField,
    me.URLField: sa.URLField,
    me.MapField: sa.JSONField,
    me.DictField: sa.JSONField,
    me.FileField: sa.FileField,
    me.ImageField: sa.ImageField,
    me.GenericEmbeddedDocumentField: sa.JSONField,
    me.EmbeddedDocumentField: sa.JSONField,
}

reference_fields = (
    me.ReferenceField,
    me.CachedReferenceField,
    me.LazyReferenceField,
)

json_like_fields = (
    me.DictField,
    me.MapField,
    me.GenericEmbeddedDocumentField,
    me.EmbeddedDocumentField,
)


def convert_mongoengine_field_to_admin_field(
    field: MongoBaseField,
) -> sa.BaseField:
    name = field.name
    admin_field: sa.BaseField
    if isinstance(field, (me.ListField, me.SortedListField)):
        if field.field is None:
            raise ValueError('ListField "%s" must have field specified' % name)
        if isinstance(field.field, reference_fields):
            """To Many reference"""
            dtype = field.field.document_type_obj
            identity = slugify_class_name(
                dtype if isinstance(dtype, str) else dtype.__name__
            )
            admin_field = sa.HasMany(name, identity=identity)
        else:
            if isinstance(field.field, json_like_fields):
                admin_field = sa.JSONField(name)
            elif isinstance(field.field, me.EnumField):
                admin_field = sa.EnumField.from_enum(
                    name, enum_type=field.field._enum_cls, multiple=True
                )
            else:
                admin_field = TagsField(name)
    elif isinstance(field, me.ReferenceField):
        dtype = field.document_type_obj
        identity = slugify_class_name(
            dtype if isinstance(dtype, str) else dtype.__name__
        )
        admin_field = sa.HasOne(name, identity=identity)
    elif isinstance(field, me.EnumField):
        admin_field = sa.EnumField.from_enum(name, enum_type=field._enum_cls)
    else:
        if mongoengine_to_admin_map.get(type(field), None) is None:
            raise NotSupportedField(
                f"Field {field.__class__.__name__} is not supported"
            )
        admin_field = mongoengine_to_admin_map.get(type(field))(name)  # type: ignore
        if field.required:
            admin_field.required = True
    return admin_field


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


def build_raw_query(dt_query: Dict[str, Any]) -> Dict[str, Any]:
    raw_query: Dict[str, Any] = dict()
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


def build_order_clauses(order_list: List[str]) -> List[str]:
    clauses = []
    for value in order_list:
        key, order = value.strip().split(maxsplit=1)
        clauses.append("%s%s" % ("-" if order.lower() == "desc" else "+", key))
    return clauses


def normalize_list(arr: Optional[List[Any]]) -> Optional[List[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, MongoBaseField):
            _new_list.append(v.name)
        elif isinstance(v, str):
            _new_list.append(v)
        else:
            raise ValueError(
                f"Expected str or monogoengine.BaseField, got {type(v).__name__}"
            )
    return _new_list
