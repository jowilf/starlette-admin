import datetime
import decimal
import enum
import inspect
import ipaddress
import types
import typing
import uuid
from abc import abstractmethod
from collections.abc import Callable, Sequence
from typing import (
    Any,
    get_args,
    get_origin,
)

from starlette_admin.exceptions import NotSupportedAnnotation
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EnumField,
    FloatField,
    IntegerField,
    IPAddressField,
    JSONField,
    ListField,
    StringField,
    TimeField,
    UUIDField,
)


def converts(
    *args: Any,
) -> Callable[
    [Callable[..., BaseField]],
    Callable[..., BaseField],
]:
    def wrap(func: Callable[..., BaseField]) -> Callable[..., BaseField]:
        func._converter_for = frozenset(args)  # ty: ignore[unresolved-attribute]
        return func

    return wrap


class BaseModelConverter:
    def __init__(
        self,
        converters: dict[Any, Callable[..., BaseField]] | None = None,
    ):
        merged: dict[Any, Callable[..., BaseField]] = {}

        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_converter_for"):
                for arg in method._converter_for:
                    merged[arg] = method

        # Plugin-registered converters (see `register_converter` in a
        # backend's converters module) sit between the class's own
        # @converts methods and the caller-supplied dict, so precedence is
        # user > plugin > core.
        merged.update(self._external_converters())
        merged.update(converters or {})

        self.converters = merged

    def _external_converters(self) -> dict[Any, Callable[..., BaseField]]:
        """Override in a backend's base converter to merge in converters
        registered by plugins for that backend. Empty by default."""
        return {}

    @abstractmethod
    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        """Searches for the appropriate `starlette_admin.BaseField` that corresponds to a specific model attribute
        and performs the conversion."""

    @abstractmethod
    def convert_fields_list(
        self,
        *,
        fields: Sequence[Any],
        model: type[Any],
        **kwargs: Any,
    ) -> Sequence[BaseField]:
        """Override this method to convert non-BaseField instances in your defined fields list into corresponding
        ``starlette_admin.BaseField`` objects."""


class BaseStandardModelConverter(BaseModelConverter):
    """Converters for Python built-in types."""

    @staticmethod
    def _normalize_type(_type: Any) -> Any:
        """Normalizes PEP 604 union syntax (X | Y) to typing.Union.

        This allows existing converters and error messages to treat both forms
        uniformly.
        """
        if get_origin(_type) is types.UnionType:
            return typing.Union[get_args(_type)]  # noqa: UP007
        return _type

    def get_converter(self, _type: Any) -> Callable[..., BaseField]:
        _type = self._normalize_type(_type)

        # If there is a converter for the specified type, use it.
        if _type in self.converters:
            return self.converters[_type]

        # If the type is a generic type, search the origin type.
        _origin = get_origin(_type)
        if _origin is not None and _origin in self.converters:
            return self.converters[_origin]

        # Otherwise, try to find a converter for any of the type's base classes.
        for cls, converter in self.converters.items():
            if (
                inspect.isclass(cls)
                and inspect.isclass(_type)
                and _origin is None  # Exclude generic types.
                and issubclass(_type, cls)
            ):
                return converter
            if inspect.isclass(cls) and isinstance(_type, cls):
                return converter

        raise NotSupportedAnnotation(
            f"Cannot automatically convert '{_type}'. Find the appropriate field"
            " manually or provide your own converter"
        )

    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        kwargs["type"] = self._normalize_type(kwargs.get("type"))
        return self.get_converter(kwargs.get("type"))(*args, **kwargs)

    def get_type(self, model: Any, value: Any) -> Any:
        return model.__annotations__[value]

    def convert_fields_list(
        self, *, fields: Sequence[Any], model: type[Any], **kwargs: Any
    ) -> Sequence[BaseField]:
        converted_fields = []
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                converted_fields.append(
                    self.convert(
                        name=value,
                        type=self.get_type(model, value),
                        model=model,
                    )
                )
        return converted_fields


class StandardModelConverter(BaseStandardModelConverter):
    """Converters for Python built-in types."""

    @classmethod
    def _ensure_get_args_is_not_null(cls, *args: Any, **kwargs: Any) -> None:
        if not get_args or not get_origin:  # type: ignore [truthy-function]
            raise ImportError(  # pragma: no cover
                f"'typing_extensions' package is required to convert '{kwargs.get('type')}'"
            )

    @classmethod
    def _standard_type_common(
        cls,
        *,
        name: str,
        required: bool | None = True,
        default: Any = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {"name": name, "required": required, "default": default}

    @converts(str, bytes, typing.Pattern)
    def conv_standard_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(**kwargs))

    @converts(int, datetime.timedelta)
    def conv_standard_int(self, *args: Any, **kwargs: Any) -> BaseField:
        return IntegerField(**self._standard_type_common(**kwargs))

    @converts(float)
    def conv_standard_float(self, *args: Any, **kwargs: Any) -> BaseField:
        return FloatField(**self._standard_type_common(**kwargs))

    @converts(decimal.Decimal)
    def conv_standard_decimal(self, *args: Any, **kwargs: Any) -> BaseField:
        return DecimalField(**self._standard_type_common(**kwargs))

    @converts(bool)
    def conv_standard_bool(self, *args: Any, **kwargs: Any) -> BaseField:
        return BooleanField(**self._standard_type_common(**kwargs))

    @converts(datetime.datetime)
    def conv_standard_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(**self._standard_type_common(**kwargs))

    @converts(datetime.date)
    def conv_standard_date(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateField(**self._standard_type_common(**kwargs))

    @converts(datetime.time)
    def conv_standard_time(self, *args: Any, **kwargs: Any) -> BaseField:
        return TimeField(**self._standard_type_common(**kwargs))

    @converts(dict)
    def conv_standard_dict(self, *args: Any, **kwargs: Any) -> BaseField:
        return JSONField(**self._standard_type_common(**kwargs))

    @converts(uuid.UUID)
    def conv_standard_uuid(self, *args: Any, **kwargs: Any) -> BaseField:
        return UUIDField(**self._standard_type_common(**kwargs))

    @converts(ipaddress.IPv4Address, ipaddress.IPv6Address)
    def conv_standard_ip_address(self, *args: Any, **kwargs: Any) -> BaseField:
        return IPAddressField(
            ipv4=True, ipv6=True, **self._standard_type_common(**kwargs)
        )

    @converts(enum.Enum)
    def conv_standard_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        return EnumField(
            **self._standard_type_common(*args, **kwargs),
            enum=kwargs.get("type"),
            multiple=kwargs.get("multiple", False),
        )

    @converts(list, set)
    def conv_standard_list(self, *args: Any, **kwargs: Any) -> BaseField:
        """Converter for `list` annotation (e.g., `list[str]`, `list[int]`).
        `list` will be treated as `list[str]`.
        """
        self._ensure_get_args_is_not_null(*args, **kwargs)
        subtypes = get_args(kwargs.get("type"))
        subtype = subtypes[0] if len(subtypes) > 0 else str
        if inspect.isclass(subtype) and issubclass(subtype, enum.Enum):
            kwargs.update({"type": subtype, "multiple": True})
            return self.convert(*args, **kwargs)
        default = kwargs.pop("default", None)
        kwargs.update({"type": subtype, "default": None})
        list_field = ListField(
            required=kwargs.get("required", True), field=self.convert(*args, **kwargs)
        )
        list_field.default = default
        return list_field

    @converts(typing.Union)
    def conv_standard_optional(self, *args: Any, **kwargs: Any) -> BaseField:
        """Support for Optional[type], Union[type, None], or Union[None, type]."""
        self._ensure_get_args_is_not_null(*args, **kwargs)
        type_args = get_args(kwargs.get("type"))
        if len(type_args) == 2 and type(None) in type_args:
            _sub_type = type_args[0] if type_args[1] is type(None) else type_args[1]
            kwargs.update({"type": _sub_type, "required": False})
            return self.convert(*args, **kwargs)
        raise NotSupportedAnnotation(
            f"Cannot convert {kwargs.get('type')}. Only annotations of the form Optional[type], Union[type, None], "
            f"or Union[None, type] are supported."
        )
