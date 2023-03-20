# Inspired by wtforms-sqlalchemy
import enum
import inspect
from typing import Any, Callable, Dict, Optional

from sqlalchemy import ARRAY, Boolean, Column, Float, String
from starlette_admin.contrib.sqla.exceptions import NotSupportedColumn
from starlette_admin.contrib.sqla.fields import FileField, ImageField
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

converters: Dict[str, Callable[[str, Column], BaseField]] = {}


def converts(
    *args: str,
) -> Callable[[Callable[[str, Column], BaseField]], Callable[[str, Column], BaseField]]:
    def wrap(
        func: Callable[[str, Column], BaseField]
    ) -> Callable[[str, Column], BaseField]:
        for arg in args:
            converters[arg] = func
        return func

    return wrap


def find_converter(column: Column) -> Callable[[str, Column], BaseField]:
    field = _search_converter_for_col_type(type(column.type))
    if field is not None:
        return field
    raise NotSupportedColumn(  # pragma: no cover
        f"Column {column.type} can not be converted automatically. Find the appropriate field manually"
    )


def _search_converter_for_col_type(
    col_type: Any,
) -> Optional[Callable[[str, Column], BaseField]]:
    types = inspect.getmro(col_type)

    # Search by module + name
    for col_type in types:
        type_string = f"{col_type.__module__}.{col_type.__name__}"
        if type_string in converters:
            return converters[type_string]

    # Search by name
    for col_type in types:
        if col_type.__name__ in converters:
            return converters[col_type.__name__]

        # Support for custom types which inherit TypeDecorator
        if hasattr(col_type, "impl"):
            if callable(col_type.impl):
                impl = col_type.impl
            else:
                impl = col_type.impl.__class__
            return _search_converter_for_col_type(impl)
    return None  # pragma: no cover


def field_common(column: Column) -> Dict[str, Any]:
    extra_args: Dict[str, Any] = {
        "help_text": column.comment,
        "required": (
            not column.nullable
            and not isinstance(column.type, (Boolean,))
            and not column.default
            and not column.server_default
        ),
    }
    return extra_args


def _string_common(column: Column) -> Dict[str, Any]:
    if (
        isinstance(column.type, String)
        and isinstance(column.type.length, int)
        and column.type.length > 0
    ):
        return {"maxlength": column.type.length}
    return {}


@converts(
    "String",
    "sqlalchemy.sql.sqltypes.Uuid",
    "sqlalchemy.dialects.postgresql.base.UUID",
    "sqlalchemy.dialects.postgresql.base.MACADDR",
    "sqlalchemy.dialects.postgresql.types.MACADDR",
    "sqlalchemy.dialects.postgresql.base.INET",
    "sqlalchemy.dialects.postgresql.types.INET",
    "sqlalchemy_utils.types.locale.LocaleType",
    "sqlalchemy_utils.types.ip_address.IPAddressType",
    "sqlalchemy_utils.types.uuid.UUIDType",
)  # includes Unicode
def conv_string(name: str, column: Column) -> BaseField:
    return StringField(name, **field_common(column), **_string_common(column))


@converts("Text", "LargeBinary", "Binary")  # includes UnicodeText
def conv_text(name: str, column: Column) -> BaseField:
    return TextAreaField(name, **field_common(column), **_string_common(column))


@converts("Boolean", "BIT")  # includes UnicodeText
def conv_boolean(name: str, column: Column) -> BaseField:
    return BooleanField(name, **field_common(column))


@converts("DateTime")
def conv_dateTime(name: str, column: Column) -> BaseField:
    return DateTimeField(name, **field_common(column))


@converts("Date")
def conv_Date(name: str, column: Column) -> BaseField:
    return DateField(name, **field_common(column))


@converts("Time")
def conv_time(name: str, column: Column) -> BaseField:
    return TimeField(name, **field_common(column))


@converts("Enum")
def conv_enum(name: str, column: Column) -> BaseField:
    assert hasattr(column.type, "enum_class")
    return EnumField(name, enum=column.type.enum_class, **field_common(column))


@converts("Integer")  # includes BigInteger and SmallInteger
def conv_integer(name: str, column: Column) -> BaseField:
    unsigned = getattr(column.type, "unsigned", False)
    extra = field_common(column)
    if unsigned:
        extra["min"] = 0
    return IntegerField(name, **extra)


@converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
def conv_numeric(name: str, column: Column) -> BaseField:
    if isinstance(column.type, Float) and not column.type.asdecimal:
        return FloatField(name, **field_common(column))
    return DecimalField(name, **field_common(column))


@converts("sqlalchemy.dialects.mysql.types.YEAR", "sqlalchemy.dialects.mysql.base.YEAR")
def conv_mysql_year(name: str, column: Column) -> BaseField:
    return IntegerField(name, **field_common(column), min=1901, max=2155)


@converts("ARRAY")
def conv_array(name: str, column: Column) -> BaseField:
    if isinstance(column.type, ARRAY) and (
        column.type.dimensions is None or column.type.dimensions == 1
    ):
        column = Column(name, column.type.item_type)
        return ListField(find_converter(column)(name, column))
    raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")


@converts("JSON", "sqlalchemy_utils.types.json.JSONType")
def conv_json(name: str, column: Column) -> BaseField:
    return JSONField(name, **field_common(column))


def _file_common(column: Column) -> Dict[str, Any]:
    return {"multiple": getattr(column.type, "multiple", False)}


@converts("sqlalchemy_file.types.FileField")
def conv_sqla_filefield(name: str, column: Column) -> BaseField:
    return FileField(name, **field_common(column), **_file_common(column))


@converts("sqlalchemy_file.types.ImageField")
def conv_sqla_imagefield(name: str, column: Column) -> BaseField:
    return ImageField(name, **field_common(column), **_file_common(column))


@converts("sqlalchemy_utils.types.arrow.ArrowType")
def conv_arrow(name: str, column: Column) -> BaseField:
    return ArrowField(name, **field_common(column))


@converts("sqlalchemy_utils.types.color.ColorType")
def conv_color(name: str, column: Column) -> BaseField:
    return ColorField(name, **field_common(column))


@converts("sqlalchemy_utils.types.email.EmailType")
def conv_email(name: str, column: Column) -> BaseField:
    return EmailField(name, **field_common(column), **_string_common(column))


@converts("sqlalchemy_utils.types.password.PasswordType")
def conv_password(name: str, column: Column) -> BaseField:
    return PasswordField(name, **field_common(column), **_string_common(column))


@converts("sqlalchemy_utils.types.phone_number.PhoneNumberType")
def conv_phonenumbers(name: str, column: Column) -> BaseField:
    return PhoneField(name, **field_common(column), **_string_common(column))


@converts("sqlalchemy_utils.types.scalar_list.ScalarListType")
def conv_scalar_list(name: str, column: Column) -> BaseField:
    return ListField(StringField(name, **field_common(column)))


@converts("sqlalchemy_utils.types.url.URLType")
def conv_url(name: str, column: Column) -> BaseField:
    return URLField(name, **field_common(column))


@converts("sqlalchemy_utils.types.timezone.TimezoneType")
def conv_timezone(name: str, column: Column) -> BaseField:
    return TimeZoneField(
        name,
        coerce=column.type.python_type,
        **field_common(column),
    )


@converts("sqlalchemy_utils.types.country.CountryType")
def conv_country(name: str, column: Column) -> BaseField:
    return CountryField(name, **field_common(column))


@converts("sqlalchemy_utils.types.currency.CurrencyType")
def conv_currency(name: str, column: Column) -> BaseField:
    return CurrencyField(name, **field_common(column))


try:
    from sqlalchemy_utils import ChoiceType, CompositeType

    @converts("sqlalchemy_utils.types.choice.ChoiceType")
    def conv_choice(name: str, column: Column) -> BaseField:
        assert isinstance(column.type, ChoiceType)
        choices = column.type.choices
        if isinstance(choices, type) and issubclass(choices, enum.Enum):
            return EnumField(
                name,
                enum=choices,
                **field_common(column),
                coerce=column.type.python_type,
            )
        return EnumField(name, choices=choices, **field_common(column), coerce=column.type.python_type)  # type: ignore

    @converts("sqlalchemy_utils.types.pg_composite.CompositeType")
    def conv_composite_type(name: str, column: Column) -> BaseField:
        assert isinstance(column.type, CompositeType)
        fields = []
        for col in column.type.columns:
            fields.append(find_converter(col)(col.name, col))
        return CollectionField(
            name, fields=fields, required=field_common(column)["required"]
        )

except ImportError:
    pass
