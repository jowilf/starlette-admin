from collections.abc import Callable, Sequence
from typing import Any

from starlette_admin.contrib.tortoise.exceptions import NotSupportedField
from starlette_admin.contrib.tortoise.fields import BackwardHasOne
from starlette_admin.converters import BaseModelConverter, converts
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    StringField,
    TextAreaField,
    TimeField,
    UUIDField,
)
from starlette_admin.helpers import slugify_class_name
from tortoise import fields as tfields
from tortoise.fields.data import CharEnumFieldInstance, IntEnumFieldInstance
from tortoise.fields.relational import (
    BackwardFKRelation,
    BackwardOneToOneRelation,
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    OneToOneFieldInstance,
)
from tortoise.models import Model

# Converters registered by plugins for Tortoise field types, merged into
# every BaseTortoiseModelConverter instance (see
# BaseModelConverter._external_converters).
_EXTERNAL_CONVERTERS: dict[Any, Callable[..., BaseField]] = {}


def register_converter(
    *types: Any,
) -> Callable[[Callable[..., BaseField]], Callable[..., BaseField]]:
    """Register an external converter for Tortoise field types.
    Decorator form mirrors `@converts`. Used by plugins."""

    def wrap(func: Callable[..., BaseField]) -> Callable[..., BaseField]:
        for field_type in types:
            _EXTERNAL_CONVERTERS[field_type] = func
        return func

    return wrap


class BaseTortoiseModelConverter(BaseModelConverter):
    """Converts Tortoise ORM model fields to `starlette_admin` `BaseField` instances.

    Dispatch is by Tortoise field class: the converter registered for the
    closest class in the field's MRO wins, so `CharEnumFieldInstance` maps to
    an `EnumField` even though it subclasses `CharField`.
    """

    def _external_converters(self) -> dict[Any, Callable[..., BaseField]]:
        return _EXTERNAL_CONVERTERS

    def get_converter(self, field: tfields.Field) -> Any:
        for klass in type(field).__mro__:
            if klass in self.converters:
                return self.converters[klass]
        raise NotSupportedField(
            f"Field {type(field).__name__} is not supported. Find the appropriate"
            " field manually or provide your own converter"
        )

    @staticmethod
    def _common(name: str, field: tfields.Field) -> dict[str, Any]:
        """Shared `BaseField` kwargs derived from a Tortoise field.

        Auto-managed values (`auto_now`/`auto_now_add` timestamps) carry a
        `readOnly` constraint; they are rendered read-only and never required.
        """
        read_only = bool(field.constraints.get("readOnly", False))
        return {
            "name": name,
            "required": field.required and not read_only,
            "default": field.default,
            "read_only": read_only,
        }

    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        name, field = kwargs["name"], kwargs["field"]
        return self.get_converter(field)(name, field)

    def convert_fields_list(
        self, *, fields: Sequence[Any], model: type[Model], **kwargs: Any
    ) -> Sequence[BaseField]:
        converted_fields = []
        fields_map = model._meta.fields_map
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                if value not in fields_map:
                    raise ValueError(f"Can't find field with key: {value}")
                converted_fields.append(
                    self.convert(name=value, field=fields_map[value])
                )
        return converted_fields


class ModelConverter(BaseTortoiseModelConverter):
    @converts(tfields.IntField, tfields.SmallIntField, tfields.BigIntField)
    def conv_int(self, name: str, field: tfields.Field) -> BaseField:
        return IntegerField(
            **self._common(name, field),
            min=field.constraints.get("ge"),
            max=field.constraints.get("le"),
        )

    @converts(tfields.CharField)
    def conv_char(self, name: str, field: tfields.Field) -> BaseField:
        return StringField(
            **self._common(name, field),
            maxlength=field.constraints.get("max_length"),
        )

    @converts(tfields.TextField)
    def conv_text(self, name: str, field: tfields.Field) -> BaseField:
        return TextAreaField(**self._common(name, field))

    @converts(tfields.BooleanField)
    def conv_boolean(self, name: str, field: tfields.Field) -> BaseField:
        return BooleanField(**self._common(name, field))

    @converts(tfields.FloatField)
    def conv_float(self, name: str, field: tfields.Field) -> BaseField:
        return FloatField(**self._common(name, field))

    @converts(tfields.DecimalField)
    def conv_decimal(self, name: str, field: tfields.Field) -> BaseField:
        return DecimalField(**self._common(name, field))

    @converts(tfields.DatetimeField)
    def conv_datetime(self, name: str, field: tfields.Field) -> BaseField:
        return DateTimeField(**self._common(name, field))

    @converts(tfields.DateField)
    def conv_date(self, name: str, field: tfields.Field) -> BaseField:
        return DateField(**self._common(name, field))

    @converts(tfields.TimeField)
    def conv_time(self, name: str, field: tfields.Field) -> BaseField:
        return TimeField(**self._common(name, field))

    @converts(tfields.JSONField)
    def conv_json(self, name: str, field: tfields.Field) -> BaseField:
        return JSONField(**self._common(name, field))

    @converts(tfields.UUIDField)
    def conv_uuid(self, name: str, field: tfields.Field) -> BaseField:
        return UUIDField(**self._common(name, field))

    @converts(CharEnumFieldInstance, IntEnumFieldInstance)
    def conv_enum(self, name: str, field: Any) -> BaseField:
        return EnumField(**self._common(name, field), enum=field.enum_type)

    @converts(ForeignKeyFieldInstance, OneToOneFieldInstance)
    def conv_to_one_relation(self, name: str, field: Any) -> BaseField:
        return HasOne(
            **self._common(name, field),
            key=slugify_class_name(field.related_model.__name__),
        )

    @converts(ManyToManyFieldInstance)
    def conv_many_to_many(self, name: str, field: Any) -> BaseField:
        common = self._common(name, field)
        # An empty selection is always a valid many-to-many value.
        common["required"] = False
        return HasMany(
            **common,
            key=slugify_class_name(field.related_model.__name__),
        )

    @converts(BackwardFKRelation)
    def conv_backward_fk(self, name: str, field: Any) -> BaseField:
        """Backward relations are read-only: the key lives on the related model,
        so rows are attached from the other side's form.
        """
        return HasMany(
            name=name,
            required=False,
            read_only=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            key=slugify_class_name(field.related_model.__name__),
        )

    @converts(BackwardOneToOneRelation)
    def conv_backward_o2o(self, name: str, field: Any) -> BaseField:
        return BackwardHasOne(
            name=name,
            required=False,
            read_only=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            key=slugify_class_name(field.related_model.__name__),
        )
