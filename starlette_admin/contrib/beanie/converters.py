# Inspired by wtforms-sqlalchemy
import enum
import inspect
from typing import Any, Callable, Dict, Optional, Sequence, Type
from beanie import PydanticObjectId, Link, BackLink
import uuid
from pydantic import AwareDatetime, BaseModel

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


class BeanieModelConverter(StandardModelConverter):
    
    @converts(PydanticObjectId)
    def conv_pydantic_object_id(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label="MongoDB ID")

    @converts(uuid.UUID)
    def conv_uuid(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label="UUID")

    @converts(AwareDatetime)
    def conv_aware_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(**self._standard_type_common(*args, **kwargs), label="DateTime")
    
    @converts(Link, BackLink)
    def conv_link(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label="Link")
    
    @converts(BaseModel)
    def conv_base_model(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs), label="BaseModel")
    
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
