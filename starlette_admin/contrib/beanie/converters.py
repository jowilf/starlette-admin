from collections.abc import Callable, Sequence
from typing import Any, Union, get_args, get_origin

from beanie import BackLink, Link, PydanticObjectId
from beanie.odm.fields import ExpressionField
from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    EmailStr,
    FutureDate,
    FutureDatetime,
    IPvAnyAddress,
    NaiveDatetime,
    PastDate,
    PastDatetime,
    SecretStr,
)
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from starlette_admin.contrib.beanie.fields import BeanieObjectIdField
from starlette_admin.contrib.beanie.helpers import (
    is_link_type,
    is_list_of_links_type,
    isvalid_field,
    resolve_expression_field_name,
)
from starlette_admin.converters import StandardModelConverter, converts
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    DateField,
    DateTimeField,
    EmailField,
    HasMany,
    HasOne,
    IPAddressField,
    PasswordField,
    StringField,
    URLField,
)
from starlette_admin.helpers import slugify_class_name

# Converters registered by plugins for Beanie/pydantic field types, merged
# into every BeanieModelConverter instance (see
# BaseModelConverter._external_converters).
_EXTERNAL_CONVERTERS: dict[Any, Callable[..., BaseField]] = {}


def register_converter(
    *types: Any,
) -> Callable[[Callable[..., BaseField]], Callable[..., BaseField]]:
    """Register an external converter for Beanie/pydantic field types.
    Decorator form mirrors `@converts`. Used by plugins."""

    def wrap(func: Callable[..., BaseField]) -> Callable[..., BaseField]:
        for field_type in types:
            _EXTERNAL_CONVERTERS[field_type] = func
        return func

    return wrap


class BeanieModelConverter(StandardModelConverter):
    """Converts Beanie `Document` fields to `starlette_admin` `BaseField` instances.

    Extends `StandardModelConverter` with converters for Beanie- and
    pydantic-specific types: `PydanticObjectId`, `Link`/`BackLink`, `SecretStr`,
    `EmailStr`, `AnyUrl`, the pydantic date/datetime constrained types, and
    nested `BaseModel`s.
    """

    def _external_converters(self) -> dict[Any, Callable[..., BaseField]]:
        return _EXTERNAL_CONVERTERS

    @staticmethod
    def _extract_default(field_info: FieldInfo) -> Any:
        """Return a Python-usable default value from a pydantic ``FieldInfo``.

        Both scalar defaults (e.g., ``= 0``) and factory defaults
        (e.g., ``default_factory=list``) are supported, as `BaseField.default`
        already accepts either a static value or a callable.
        """
        if field_info.default_factory is not None:
            return field_info.default_factory
        if field_info.default is PydanticUndefined:
            return None
        return field_info.default

    @converts(PydanticObjectId)
    def conv_pydantic_object_id(self, *args: Any, **kwargs: Any) -> BaseField:
        return BeanieObjectIdField(**self._standard_type_common(*args, **kwargs))

    @converts(IPvAnyAddress)
    def conv_ip_address(self, *args: Any, **kwargs: Any) -> BaseField:
        return IPAddressField(
            ipv4=True, ipv6=True, **self._standard_type_common(*args, **kwargs)
        )

    @converts(BackLink)
    def conv_back_link(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(*args, **kwargs))

    @converts(SecretStr)
    def conv_secret_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return PasswordField(**self._standard_type_common(*args, **kwargs))

    @converts(EmailStr)
    def conv_email_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return EmailField(**self._standard_type_common(*args, **kwargs))

    @converts(AnyUrl)
    def conv_any_url(self, *args: Any, **kwargs: Any) -> BaseField:
        return URLField(**self._standard_type_common(*args, **kwargs))

    @converts(AwareDatetime, NaiveDatetime, FutureDatetime, PastDatetime)
    def conv_aware_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(**self._standard_type_common(*args, **kwargs))

    @converts(PastDate, FutureDate)
    def conv_pydantic_date(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateField(**self._standard_type_common(*args, **kwargs))

    @converts(Link)
    def conv_link(self, *args: Any, **kwargs: Any) -> BaseField:
        """Convert a Beanie `Link[T]` or `list[Link[T]]` annotation to a relation field.

        A single `Link[T]` becomes a `HasOne` field; `list[Link[T]]` becomes a
        `HasMany` field. Both derive their `key` from `T`'s class name.
        """
        link_type = kwargs.get("type")
        # Unwrap the first type argument: `T` for `Link[T]`, or `Link[T]` itself
        # for `list[Link[T]]`.
        link_model_type = get_args(link_type)[0]

        # For `list[Link[T]]`, unwrap once more to reach `T` and build a
        # to-many relation instead of a to-one relation.
        if get_origin(link_type) is list:
            link_model_type = get_args(link_model_type)[0]
            return HasMany(
                **self._standard_type_common(*args, **kwargs),
                key=slugify_class_name(link_model_type.__name__),
            )

        return HasOne(
            **self._standard_type_common(*args, **kwargs),
            key=slugify_class_name(link_model_type.__name__),
        )

    @converts(BaseModel)
    def conv_base_model(
        self,
        name: str,
        required: bool,
        *args: Any,
        **kwargs: Any,
    ) -> BaseField:
        """Convert a nested pydantic `BaseModel` annotation to a `CollectionField`.

        Recursively converts each of the model's own fields and nests the
        results under a single `CollectionField` named `name`.
        """
        model_type: type[BaseModel] | None = kwargs.get("type")
        assert model_type is not None

        _fields = []
        for subfield_name, subfield_field in model_type.model_fields.items():
            kwargs["type"] = subfield_field.annotation
            kwargs["name"] = subfield_name
            kwargs["required"] = subfield_field.is_required()
            kwargs["default"] = self._extract_default(subfield_field)
            _fields.append(self.convert(*args, **kwargs))
        return CollectionField(name=name, fields=_fields, required=required)

    def get_type_beanie(self, model_fields: Any, value: Any) -> Any:
        """Return the annotated type of `value` in `model_fields`.

        Unwraps a `Union`/`Optional` annotation by repeatedly taking its first
        type argument, so `Optional[X]` resolves to `X`.
        """
        field_type = model_fields[value].annotation
        while get_origin(field_type) is Union:
            field_type = get_args(field_type)[0]

        return field_type

    def convert_fields_list(
        self, *, fields: Sequence[Any], model: type[Any], **kwargs: dict[str, Any]
    ) -> Sequence[BaseField]:
        """Convert a mixed list of field names, `ExpressionField`s, and
        `BaseField` instances into a list of `BaseField` instances.

        `BaseField` instances pass through unchanged. `ExpressionField`s
        (e.g., `Model.id`) are resolved to their attribute name first. Every
        other entry is validated against `model` with `isvalid_field` and
        routed to `conv_link` for `Link`/`list[Link[T]]` annotations, or to
        the standard `convert` dispatch otherwise.
        """
        converted_fields = []
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                field = (
                    resolve_expression_field_name(value)
                    if isinstance(value, ExpressionField)
                    else value
                )
                if not isvalid_field(model, field):
                    raise ValueError(f"Invalid field: {field}")
                field_type = self.get_type_beanie(model.model_fields, value)
                field_info = model.model_fields[value]
                if is_link_type(field_type) or is_list_of_links_type(field_type):
                    converted_fields.append(
                        self.conv_link(
                            name=field,
                            type=field_type,
                            required=field_info.is_required(),
                            default=self._extract_default(field_info),
                        )
                    )
                else:
                    converted_fields.append(
                        self.convert(
                            name=field,
                            type=field_type,
                            required=field_info.is_required(),
                            default=self._extract_default(field_info),
                            model=model,
                        )
                    )
        return converted_fields
