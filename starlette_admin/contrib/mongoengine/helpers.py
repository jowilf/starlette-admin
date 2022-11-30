import functools
from typing import Any, Callable, Dict, List, Optional, Sequence, Type

import mongoengine.fields as me
import starlette_admin.fields as sa
from mongoengine import EmbeddedDocument
from mongoengine.base.fields import BaseField as MongoBaseField
from mongoengine.queryset import Q as BaseQ
from mongoengine.queryset import QNode
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField
from starlette_admin.contrib.mongoengine.fields import FileField, ImageField
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
    me.FileField: FileField,
    me.ImageField: ImageField,
}

reference_fields = (
    me.ReferenceField,
    me.CachedReferenceField,
    me.LazyReferenceField,
)


def convert_mongoengine_field_to_admin_field(  # noqa: C901
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
        elif isinstance(field.field, (me.DictField, me.MapField)):
            admin_field = sa.JSONField(name)
        elif isinstance(field.field, me.EnumField):
            admin_field = sa.EnumField.from_enum(
                name, enum_type=field.field._enum_cls, multiple=True
            )
        else:
            field.field.name = name
            admin_field = sa.ListField(
                convert_mongoengine_field_to_admin_field(field.field)
            )
    elif isinstance(field, me.ReferenceField):
        dtype = field.document_type_obj
        identity = slugify_class_name(
            dtype if isinstance(dtype, str) else dtype.__name__
        )
        admin_field = sa.HasOne(name, identity=identity)
    elif isinstance(field, me.EmbeddedDocumentField):
        document_type_obj: EmbeddedDocument = field.document_type
        _fields = []
        for _field in document_type_obj._fields_ordered:
            _fields.append(
                convert_mongoengine_field_to_admin_field(
                    getattr(document_type_obj, _field)
                )
            )
        admin_field = sa.CollectionField(name, fields=_fields)
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


class Q(BaseQ):
    """
    Override mongoengine.Q class to support expression like this:
    >>> Q('name', 'Jo', 'istartswith') # same as Q(name__istartswith = 'Jo')
    or
    >>> Q('name', 'John') # same as Q(name = 'John')
    """

    def __init__(self, field: str, value: Any, op: Optional[str] = None) -> None:
        field = f'{field.replace(".", "__")}__'
        if op is not None:
            field = f"{field}{op}"
        super().__init__(**{field: value})

    @classmethod
    def empty(cls) -> BaseQ:
        return BaseQ()


OPERATORS: Dict[str, Callable[[str, Any], Q]] = {
    "eq": lambda f, v: Q(f, v),
    "neq": lambda f, v: Q(f, v, "ne"),
    "lt": lambda f, v: Q(f, v, "lt"),
    "gt": lambda f, v: Q(f, v, "gt"),
    "le": lambda f, v: Q(f, v, "lte"),
    "ge": lambda f, v: Q(f, v, "gte"),
    "in": lambda f, v: Q(f, v, "in"),
    "not_in": lambda f, v: Q(f, v, "nin"),
    "startswith": lambda f, v: Q(f, v, "istartswith"),
    "not_startswith": lambda f, v: Q(f, v, "not__istartswith"),
    "endswith": lambda f, v: Q(f, v, "iendswith"),
    "not_endswith": lambda f, v: Q(f, v, "not__iendswith"),
    "contains": lambda f, v: Q(f, v, "icontains"),
    "not_contains": lambda f, v: Q(f, v, "not__icontains"),
    "is_false": lambda f, v: Q(f, False),
    "is_true": lambda f, v: Q(f, True),
    "is_null": lambda f, v: Q(f, None),
    "is_not_null": lambda f, v: Q(f, None, "ne"),
    "between": lambda f, v: Q(f, v[0], "gte") & Q(f, v[1], "lte"),
    "not_between": lambda f, v: Q(f, v[0], "lt") | Q(f, v[1], "gt"),
}


def isvalid_field(document: Type[me.Document], field: str) -> bool:
    """
    Check if field is valid field for document. nested field is separate with '.'
    """
    try:
        document._lookup_field(field.split("."))
    except Exception:  # pragma: no cover
        return False
    return True


def resolve_deep_query(
    where: Dict[str, Any],
    document: Type[me.Document],
    latest_field: Optional[str] = None,
) -> QNode:
    _all_queries = []
    for key in where:
        if key in ["or", "and"]:
            _arr = [(resolve_deep_query(q, document, latest_field)) for q in where[key]]
            if len(_arr) > 0:
                funcs = {"or": lambda q1, q2: q1 | q2, "and": lambda q1, q2: q1 & q2}
                _all_queries.append(functools.reduce(funcs[key], _arr))
        elif key in OPERATORS:
            _all_queries.append(OPERATORS[key](latest_field, where[key]))  # type: ignore
        elif isvalid_field(document, key):
            _all_queries.append(resolve_deep_query(where[key], document, key))
    if _all_queries:
        return functools.reduce(lambda q1, q2: q1 & q2, _all_queries)
    return Q.empty()


def build_order_clauses(order_list: List[str]) -> List[str]:
    clauses = []
    for value in order_list:
        key, order = value.strip().split(maxsplit=1)
        clauses.append("{}{}".format("-" if order.lower() == "desc" else "+", key))
    return clauses


def normalize_list(arr: Optional[Sequence[Any]]) -> Optional[Sequence[str]]:
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
