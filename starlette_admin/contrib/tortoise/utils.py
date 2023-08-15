from . import types as t
from tortoise.fields.relational import (
    ForeignKeyFieldInstance,
    OneToOneFieldInstance,
    ManyToManyFieldInstance,
)
from tortoise import fields as tfields
import starlette_admin.fields as fields


def starlette_admin_order_by2tortoise_order_by(order_bys: t.OrderBy):
    def convert(order_by: str):
        field_part, order_part = order_by.split(" ")
        order_by = "" if order_by == "acs" else "-"
        return f"{order_part}{field_part}"

    return tuple(map(convert, order_bys))


def remove_nones(item: dict):
    return {
        k: remove_nones(v) if isinstance(v, dict) else v
        for k, v in item.items()
        if v is not None
    }


def fk_fields(repo: t.TortoiseModel):
    return tuple(
        k
        for k, v in repo._meta.fields_map.items()
        if isinstance(v, ForeignKeyFieldInstance)
    )


def add_id2fk_fields(data: dict, fields: t.Sequence[str]):
    fk_fields_ = set(fields)
    convert = lambda k: k if k not in fk_fields_ else f"{k}_id"
    return {convert(k): v for k, v in data.items()}


tortoise2starlette_admin_fields = {
    tfields.IntField: fields.IntegerField,
    tfields.BigIntField: fields.IntegerField,
    tfields.SmallIntField: fields.IntegerField,
    tfields.IntEnumField: fields.IntEnum,
    tfields.CharField: fields.StringField,
    tfields.CharEnumField: fields.EnumField,
    tfields.BooleanField: fields.BooleanField,
    tfields.DateField: fields.DateField,
    tfields.DatetimeField: fields.DateTimeField,
    tfields.FloatField: fields.FloatField,
    tfields.DecimalField: fields.DecimalField,
    tfields.UUIDField: fields.StringField,
    ForeignKeyFieldInstance: fields.HasOne,
    OneToOneFieldInstance: fields.HasOne,
    ManyToManyFieldInstance: fields.HasMany,
    tfields.TextField: fields.TinyMCEEditorField,
    tfields.TimeField: fields.TimeField,
}


def related_starlette_field(field_map_item: tuple, **kw):
    name, field = field_map_item
    starlette_type = tortoise2starlette_admin_fields[field]
    kwargs = {"name": name, "label": name, "required": field.required}
    if isinstance(field, ForeignKeyFieldInstance):
        kwargs.update(dict(identity=field.model_name.split(".")[-1]))
    elif isinstance(field, tfields.CharField):
        kwargs.update(dict(maxlength=field.max_length))
    kwargs.update(kw)
    return starlette_type(**kwargs)


def tortoise_fields2starlette_fields(model: t.TortoiseModel, **kwargs):
    return tuple(
        map(
            lambda i: related_starlette_field(i, kwargs.get(i[0], dict())),
            model._meta.fields_map.items(),
        )
    )
