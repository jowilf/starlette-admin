# Inspired by wtforms-sqlalchemy
import enum
import inspect
from typing import Any, Callable, Dict, Optional, Sequence, Type, get_args
from beanie import PydanticObjectId, Link, BackLink
import uuid
from pydantic import AwareDatetime, BaseModel
from pydantic.fields import FieldInfo

from starlette_admin.converters import StandardModelConverter, converts
from starlette_admin.fields import (
    ArrowField,
    BaseField,
    BooleanField,
    CollectionField,
    ColorField,
    CountryField,
    CurrencyField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    JSONField,
    ListField,
    PasswordField,
    PhoneField,
    StringField,
    TextAreaField,
    TimeField,
    TimeZoneField,
    URLField,
)

def get_pydantic_field_type(field: FieldInfo) -> Type:
    if isinstance(get_args(field.annotation), list):
        types = list(get_args(field.annotation))
    else:
        types = [field.annotation]
    types = [t for t in types if t is not type(None)]
    if not len(types) == 1:
        raise RuntimeError(
            f"Field {field.title} has multiple types: {types}. Only one type is allowed."
        )
    return types[0]

class BeanieModelConverter(StandardModelConverter):

    @converts(PydanticObjectId)
    def conv_pydantic_object_id(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label=kwargs.get("name"))

    @converts(uuid.UUID)
    def conv_uuid(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label=kwargs.get("name"))

    @converts(AwareDatetime)
    def conv_aware_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(**self._standard_type_common(*args, **kwargs), label=kwargs.get("name"))

    @converts(Link, BackLink)
    def conv_link(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label=kwargs.get("name"))

    @converts(BaseModel)
    def conv_base_model(self, *args: Any, **kwargs: Any) -> BaseField:
        field = kwargs.get("name")
        field_required = kwargs.get("required", False)
        document_type_obj: BaseModel = kwargs.get("type")
        _fields = []
        for subfield_name, subfield_field in document_type_obj.model_fields.items():
            subfield_type = get_pydantic_field_type(subfield_field)
            kwargs["type"] = subfield_type
            kwargs["name"] = subfield_name
            kwargs["required"] = subfield_field.is_required()
            _fields.append(self.convert(*args, **kwargs))
        return CollectionField(field, _fields, required=field_required)

    def convert_fields_list(
        self, *, fields: Sequence[Any], model: Type[Any], **kwargs: Any
    ) -> Sequence[BaseField]:
        converted_fields = []
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                converted_fields.append(
                    self.convert(
                        name=value["name"],
                        type=value["type"],
                        model=model,
                    )
                )
        return converted_fields
