# Inspired by wtforms-sqlalchemy
import uuid
from typing import Any, Sequence, Type, Union, get_args, get_origin

from beanie import BackLink, Link, PydanticObjectId
from pydantic import AnyUrl, AwareDatetime, BaseModel, EmailStr, SecretStr
from pydantic.fields import FieldInfo
from starlette_admin.converters import StandardModelConverter, converts
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    DateTimeField,
    EmailField,
    HasMany,
    HasOne,
    PasswordField,
    StringField,
    URLField,
)
from starlette_admin.helpers import slugify_class_name


def get_pydantic_field_type(field: FieldInfo) -> Type:

    if get_origin(field.annotation) == Union:
        # if the field is a union, get the first type
        types = list(get_args(field.annotation))
        # remove NoneType from the list
        types = [t for t in types if t is not type(None)]
        if len(types) == 1:
            return types[0]
        raise RuntimeError(
            f"Field {field.title} has multiple types: {types}. Only one type is allowed."
        )
    return field.annotation


class BeanieModelConverter(StandardModelConverter):

    @converts(PydanticObjectId)
    def conv_pydantic_object_id(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(uuid.UUID)
    def conv_uuid(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(AwareDatetime)
    def conv_aware_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(BackLink)
    def conv_back_link(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(SecretStr)
    def conv_secret_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return PasswordField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(EmailStr)
    def conv_email_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return EmailField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(AnyUrl)
    def conv_any_url(self, *args: Any, **kwargs: Any) -> BaseField:
        return URLField(
            **self._standard_type_common(*args, **kwargs), label=kwargs.get("name")
        )

    @converts(Link)
    def conv_link(self, *args: Any, **kwargs: Any) -> BaseField:

        link_type = kwargs.get("type")
        # get the model type from the Link field
        link_model_type = get_args(link_type)[0]

        # check if this is a list of links
        if get_origin(link_type) is list:
            link_model_type = get_args(link_model_type)[0]
            return HasMany(
                **self._standard_type_common(*args, **kwargs),
                label=kwargs.get("name"),
                identity=slugify_class_name(link_model_type.__name__),
            )

        return HasOne(
            **self._standard_type_common(*args, **kwargs),
            label=kwargs.get("name"),
            identity=slugify_class_name(link_model_type.__name__),
        )

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
                        required=value["required"],
                        model=model,
                    )
                )
        return converted_fields
