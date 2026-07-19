import datetime
import decimal
import enum
import ipaddress

import pytest
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    IntegerField,
    IPAddressField,
    JSONField,
    ListField,
    StringField,
    TimeField,
)
from starlette_admin.converters import (
    BaseStandardModelConverter,
    StandardModelConverter,
)
from starlette_admin.exceptions import NotSupportedAnnotation
from starlette_admin.fields import DecimalField


class Model:
    datetime: datetime.datetime
    date: datetime.date
    time: datetime.time | None


class UnsupportedModel:
    code: str | int


class AllTypesModel:
    name: str
    count: int
    ratio: float
    amount: decimal.Decimal
    flag: bool
    data: dict
    tags: list[str]
    optional_name: str | None


class MyStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"


class EnumModel:
    status: MyStatus


class EnumListModel:
    statuses: list[MyStatus]


class SubStr(str):
    pass


class SubStrModel:
    value: SubStr


class IPAddressModel:
    ipv4: ipaddress.IPv4Address
    ipv6: ipaddress.IPv6Address


@pytest.fixture()
def converter() -> StandardModelConverter:
    return StandardModelConverter()


def test_standard_model_converter(converter: StandardModelConverter):
    assert converter.convert_fields_list(
        fields=["datetime", "date", "time"], model=Model
    ) == [
        DateTimeField("datetime", required=True),
        DateField("date", required=True),
        TimeField("time"),
    ]


def test_not_supported_annotation(converter: StandardModelConverter):
    with pytest.raises(NotSupportedAnnotation, match="Cannot convert"):
        converter.convert_fields_list(fields=["code"], model=UnsupportedModel)


def test_base_standard_converter_get_converter_not_supported():
    """`BaseStandardModelConverter.get_converter` raises `NotSupportedAnnotation` for unknown types."""

    class UnknownType:
        pass

    base_converter = BaseStandardModelConverter()
    with pytest.raises(NotSupportedAnnotation, match="Cannot automatically convert"):
        base_converter.get_converter(UnknownType)


def test_conv_str(converter):
    assert converter.convert_fields_list(fields=["name"], model=AllTypesModel) == [
        StringField("name", required=True)
    ]


def test_conv_int(converter):
    assert converter.convert_fields_list(fields=["count"], model=AllTypesModel) == [
        IntegerField("count", required=True)
    ]


def test_conv_float(converter):
    assert converter.convert_fields_list(fields=["ratio"], model=AllTypesModel) == [
        FloatField("ratio", required=True)
    ]


def test_conv_decimal(converter):
    assert converter.convert_fields_list(fields=["amount"], model=AllTypesModel) == [
        DecimalField("amount", required=True)
    ]


def test_conv_bool(converter):
    assert converter.convert_fields_list(fields=["flag"], model=AllTypesModel) == [
        BooleanField("flag", required=True)
    ]


def test_conv_dict(converter):
    assert converter.convert_fields_list(fields=["data"], model=AllTypesModel) == [
        JSONField("data", required=True)
    ]


def test_conv_list(converter):
    result = converter.convert_fields_list(fields=["tags"], model=AllTypesModel)
    assert len(result) == 1
    assert isinstance(result[0], ListField)


def test_conv_optional(converter):
    result = converter.convert_fields_list(
        fields=["optional_name"], model=AllTypesModel
    )
    assert result == [StringField("optional_name", required=False)]


def test_conv_enum(converter):
    result = converter.convert_fields_list(fields=["status"], model=EnumModel)
    assert len(result) == 1
    assert isinstance(result[0], EnumField)
    assert result[0].enum is MyStatus


def test_conv_enum_list(converter):
    result = converter.convert_fields_list(fields=["statuses"], model=EnumListModel)
    assert len(result) == 1
    assert isinstance(result[0], EnumField)
    assert result[0].multiple is True


def test_conv_subclass_lookup(converter):
    # `SubStr` is a subclass of `str`; therefore, its converter should be found via MRO.
    result = converter.convert_fields_list(fields=["value"], model=SubStrModel)
    assert isinstance(result[0], StringField)


def test_convert_method_directly(converter):
    field = converter.convert(name="x", type=str)
    assert isinstance(field, StringField)


def test_pass_field_instance_unchanged(converter):
    existing = IntegerField("myid")
    result = converter.convert_fields_list(fields=[existing], model=AllTypesModel)
    assert result[0] is existing


def test_conv_ip_address(converter):
    result = converter.convert_fields_list(
        fields=["ipv4", "ipv6"], model=IPAddressModel
    )
    assert result == [
        IPAddressField("ipv4", required=True, ipv4=True, ipv6=True),
        IPAddressField("ipv6", required=True, ipv4=True, ipv6=True),
    ]


def test_conv_type_instance_via_isinstance(converter):
    """`get_converter` handles `_type` when it is an *instance* of a registered class.

    The `isinstance(cls)` branch in `get_converter` is activated when `_type` is not a class but an instance of a registered class. For example, a string literal is an instance of `str`, which is registered."""
    # A string literal is an instance of `str`, which is registered.
    # `inspect.isclass("hello")` is `False`, so the subclass branch is skipped.
    # `isinstance("hello", str)` is triggered, which returns the `str` converter.
    conv_fn = converter.get_converter("hello")
    assert conv_fn is not None
