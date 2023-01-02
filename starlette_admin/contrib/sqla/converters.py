# Inspired by wtforms-sqlalchemy
import enum
import inspect
from typing import Any, Callable, Dict

from sqlalchemy import ARRAY, Boolean, Column, Float
from starlette_admin import CollectionField, JSONField, ListField
from starlette_admin.contrib.sqla.exceptions import NotSupportedColumn
from starlette_admin.contrib.sqla.fields import FileField, ImageField
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EnumField,
    FloatField,
    IntegerField,
    StringField,
    TextAreaField,
    TimeField,
)

converters: Dict[str, Callable[[str, Column], BaseField]] = {}


def converts(*args: str):
    def wrap(func: Callable[[str, Column], BaseField]):
        for arg in args:
            converters[arg] = func
        return func

    return wrap


def find_converter(column: Column) -> Callable[[str, Column], BaseField]:
    types = inspect.getmro(type(column.type))
    # Search by module + name
    for col_type in types:
        print(col_type)
        type_string = f"{col_type.__module__}.{col_type.__name__}"
        if type_string in converters:
            return converters[type_string]

    # Search by name
    for col_type in types:
        print(col_type.__name__)
        if col_type.__name__ in converters:
            return converters[col_type.__name__]

        # Support for custom types like SQLModel which inherit TypeDecorator
        if hasattr(col_type, "impl"):
            if callable(col_type.impl):
                impl = col_type.impl
            else:
                impl = col_type.impl.__class__

            if impl.__name__ in converters:
                return converters[impl.__name__]
    raise NotSupportedColumn(  # pragma: no cover
        f"Column {column.type} can not be converted automatically. Find the appropriate field manually"
    )


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
    if isinstance(column.type.length, int) and column.type.length > 0:
        return {"maxlength": column.type.length}
    return {}


@converts("String")  # includes Unicode
def conv_string(name: str, column: Column):
    return StringField(name, **field_common(column), **_string_common(column))


@converts("Text", "LargeBinary", "Binary")  # includes UnicodeText
def conv_text(name: str, column: Column):
    return TextAreaField(name, **field_common(column), **_string_common(column))


@converts("Boolean", "BIT")  # includes UnicodeText
def conv_boolean(name: str, column: Column):
    return BooleanField(name, **field_common(column))


@converts("DateTime")
def conv_dateTime(name: str, column: Column):
    return DateTimeField(name, **field_common(column))


@converts("Date")
def conv_Date(name: str, column: Column):
    return DateField(name, **field_common(column))


@converts("Time")
def conv_time(name: str, column: Column):
    return TimeField(name, **field_common(column))


@converts("Enum")
def conv_enum(name: str, column: Column):
    return EnumField(name, enum=column.type.enum_class, **field_common(column))


@converts("Integer")  # includes BigInteger and SmallInteger
def conv_integer(name: str, column: Column):
    unsigned = getattr(column.type, "unsigned", False)
    extra = {}
    if unsigned:
        extra["min"] = 0
    return IntegerField(name, **field_common(column), **extra)


@converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
def conv_numeric(name: str, column: Column):
    if isinstance(column.type, Float) and not column.type.asdecimal:
        return FloatField(name, **field_common(column))
    return DecimalField(name, **field_common(column))


@converts("sqlalchemy.dialects.mysql.types.YEAR", "sqlalchemy.dialects.mysql.base.YEAR")
def conv_mysql_year(name: str, column: Column):
    return IntegerField(name, **field_common(column), min=1901, max=2155)


@converts("sqlalchemy.dialects.postgresql.base.INET")
def conv_postgresql_inet(name: str, column: Column):
    return StringField(name, **field_common(column))


@converts("sqlalchemy.dialects.postgresql.base.MACADDR")
def conv_postgresql_macaddr(name: str, column: Column):
    return StringField(name, **field_common(column))


@converts("sqlalchemy.dialects.postgresql.base.UUID")
def conv_postgresql_uuid(name: str, column: Column):
    return StringField(name, **field_common(column))


@converts("ARRAY")
def conv_array(name: str, column: Column):
    if isinstance(column.type, ARRAY) and (
        column.type.dimensions is None or column.type.dimensions == 1
    ):
        column = Column(name, column.type.item_type)
        return ListField(find_converter(column)(name, column))
    raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")


@converts("JSON")
def conv_json(name: str, column: Column):
    return JSONField(name, **field_common(column))


def _file_common(column: Column) -> Dict[str, Any]:
    return {"multiple": getattr(column.type, "multiple", False)}


@converts("sqlalchemy_file.types.FileField")
def conv_sqla_filefield(name: str, column: Column):
    return FileField(name, **field_common(column), **_file_common(column))


@converts("sqlalchemy_file.types.ImageField")
def conv_sqla_imagefield(name: str, column: Column):
    return ImageField(name, **field_common(column), **_file_common(column))


try:
    # Converters for sqlalchemy_utils types

    from sqlalchemy_utils import ChoiceType, CompositeType

    @converts("sqlalchemy_utils.types.choice.ChoiceType")
    def conv_choice(name: str, column: Column):
        assert isinstance(column.type, ChoiceType)
        choices = column.type.choices
        if isinstance(choices, type) and issubclass(choices, enum.Enum):
            return EnumField(name, enum=choices, **field_common(column))
        return EnumField(name, choices=choices, **field_common(column))

    @converts("sqlalchemy_utils.types.pg_composite.CompositeType")
    def conv_composite_type(name: str, column: Column):
        assert isinstance(column.type, CompositeType)
        fields = []
        for col in column.type.columns:
            fields.append(find_converter(col)(col.name, col))
        return CollectionField(
            name, fields=fields, required=field_common(col)["required"]
        )

except ImportError:
    pass
