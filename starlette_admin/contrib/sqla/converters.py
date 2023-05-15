# Inspired by wtforms-sqlalchemy
import enum
import inspect
from typing import Any, Callable, Dict, Optional, Sequence

from sqlalchemy import ARRAY, Boolean, Column, Float, String
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
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
from starlette_admin.helpers import slugify_class_name


def converts(
    *args: str,
) -> Callable[
    [Callable[["ModelConverter", str, Column], BaseField]],
    Callable[["ModelConverter", str, Column], BaseField],
]:
    def wrap(
        func: Callable[["ModelConverter", str, Column], BaseField]
    ) -> Callable[["ModelConverter", str, Column], BaseField]:
        func._converter_for = frozenset(args)  # type:ignore [attr-defined]
        return func

    return wrap


class BaseModelConverter:
    def __init__(
        self, converters: Optional[Dict[str, Callable[[str, Column], BaseField]]] = None
    ):
        if converters is None:
            converters = {}

        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_converter_for"):
                for classname in method._converter_for:
                    converters[classname] = method

        self.converters = converters

    def get_converter(self, column: Column) -> Callable[[str, Column], BaseField]:
        field = self.find_converter_for_col_type(type(column.type))
        if field is not None:
            return field
        raise NotSupportedColumn(  # pragma: no cover
            f"Column {column.type} can not be converted automatically. Find the appropriate field manually"
        )

    def find_converter_for_col_type(
        self,
        col_type: Any,
    ) -> Optional[Callable[[str, Column], BaseField]]:
        types = inspect.getmro(col_type)

        # Search by module + name
        for col_type in types:
            type_string = f"{col_type.__module__}.{col_type.__name__}"
            if type_string in self.converters:
                return self.converters[type_string]

        # Search by name
        for col_type in types:
            if col_type.__name__ in self.converters:
                return self.converters[col_type.__name__]

            # Support for custom types which inherit TypeDecorator
            if hasattr(col_type, "impl"):
                impl = (
                    col_type.impl
                    if callable(col_type.impl)
                    else col_type.impl.__class__
                )
                return self.find_converter_for_col_type(impl)
        return None  # pragma: no cover

    def normalize_fields_list(
        self, fields: Sequence[Any], mapper: Mapper
    ) -> Sequence[BaseField]:
        converted_fields = []
        for field in fields:
            if isinstance(field, BaseField):
                converted_fields.append(field)
            else:
                if isinstance(field, InstrumentedAttribute):
                    attr = mapper.attrs.get(field.key)
                else:
                    attr = mapper.attrs.get(field)
                if attr is None:
                    raise ValueError(f"Can't find column with key {field}")
                if isinstance(attr, RelationshipProperty):
                    identity = slugify_class_name(attr.entity.class_.__name__)
                    if attr.direction.name == "MANYTOONE" or (
                        attr.direction.name == "ONETOMANY" and not attr.uselist
                    ):
                        converted_fields.append(HasOne(attr.key, identity=identity))
                    else:
                        converted_fields.append(HasMany(attr.key, identity=identity))
                elif isinstance(attr, ColumnProperty):
                    assert (
                        len(attr.columns) == 1
                    ), "Multiple-column properties are not supported"
                    column = attr.columns[0]
                    if not column.foreign_keys:
                        field_converter = self.get_converter(column)
                        converted_fields.append(field_converter(attr.key, column))
        return converted_fields


class ModelConverter(BaseModelConverter):
    @classmethod
    def _field_common(cls, column: Column) -> Dict[str, Any]:
        return {
            "help_text": column.comment,
            "required": (
                not column.nullable
                and not isinstance(column.type, (Boolean,))
                and not column.default
                and not column.server_default
            ),
        }

    @classmethod
    def _string_common(cls, column: Column) -> Dict[str, Any]:
        if (
            isinstance(column.type, String)
            and isinstance(column.type.length, int)
            and column.type.length > 0
        ):
            return {"maxlength": column.type.length}
        return {}

    @classmethod
    def _file_common(cls, column: Column) -> Dict[str, Any]:
        return {"multiple": getattr(column.type, "multiple", False)}

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
    def conv_string(self, name: str, column: Column) -> BaseField:
        return StringField(
            name, **self._field_common(column), **self._string_common(column)
        )

    @converts("Text", "LargeBinary", "Binary")  # includes UnicodeText
    def conv_text(self, name: str, column: Column) -> BaseField:
        return TextAreaField(
            name, **self._field_common(column), **self._string_common(column)
        )

    @converts("Boolean", "BIT")  # includes UnicodeText
    def conv_boolean(self, name: str, column: Column) -> BaseField:
        return BooleanField(name, **self._field_common(column))

    @converts("DateTime")
    def conv_datetime(self, name: str, column: Column) -> BaseField:
        return DateTimeField(name, **self._field_common(column))

    @converts("Date")
    def conv_date(self, name: str, column: Column) -> BaseField:
        return DateField(name, **self._field_common(column))

    @converts("Time")
    def conv_time(self, name: str, column: Column) -> BaseField:
        return TimeField(name, **self._field_common(column))

    @converts("Enum")
    def conv_enum(self, name: str, column: Column) -> BaseField:
        assert hasattr(column.type, "enum_class")
        return EnumField(
            name, enum=column.type.enum_class, **self._field_common(column)
        )

    @converts("Integer")  # includes BigInteger and SmallInteger
    def conv_integer(self, name: str, column: Column) -> BaseField:
        unsigned = getattr(column.type, "unsigned", False)
        extra = self._field_common(column)
        if unsigned:
            extra["min"] = 0
        return IntegerField(name, **extra)

    @converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    def conv_numeric(self, name: str, column: Column) -> BaseField:
        if isinstance(column.type, Float) and not column.type.asdecimal:
            return FloatField(name, **self._field_common(column))
        return DecimalField(name, **self._field_common(column))

    @converts(
        "sqlalchemy.dialects.mysql.types.YEAR", "sqlalchemy.dialects.mysql.base.YEAR"
    )
    def conv_mysql_year(self, name: str, column: Column) -> BaseField:
        return IntegerField(name, **self._field_common(column), min=1901, max=2155)

    @converts("ARRAY")
    def conv_array(self, name: str, column: Column) -> BaseField:
        if isinstance(column.type, ARRAY) and (
            column.type.dimensions is None or column.type.dimensions == 1
        ):
            column = Column(name, column.type.item_type)
            return ListField(self.get_converter(column)(name, column))
        raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")

    @converts("JSON", "sqlalchemy_utils.types.json.JSONType")
    def conv_json(self, name: str, column: Column) -> BaseField:
        return JSONField(name, **self._field_common(column))

    @converts("sqlalchemy_file.types.FileField")
    def conv_sqla_filefield(self, name: str, column: Column) -> BaseField:
        return FileField(
            name, **self._field_common(column), **self._file_common(column)
        )

    @converts("sqlalchemy_file.types.ImageField")
    def conv_sqla_imagefield(self, name: str, column: Column) -> BaseField:
        return ImageField(
            name, **self._field_common(column), **self._file_common(column)
        )

    @converts("sqlalchemy_utils.types.arrow.ArrowType")
    def conv_arrow(self, name: str, column: Column) -> BaseField:
        return ArrowField(name, **self._field_common(column))

    @converts("sqlalchemy_utils.types.color.ColorType")
    def conv_color(self, name: str, column: Column) -> BaseField:
        return ColorField(name, **self._field_common(column))

    @converts("sqlalchemy_utils.types.email.EmailType")
    def conv_email(self, name: str, column: Column) -> BaseField:
        return EmailField(
            name, **self._field_common(column), **self._string_common(column)
        )

    @converts("sqlalchemy_utils.types.password.PasswordType")
    def conv_password(self, name: str, column: Column) -> BaseField:
        return PasswordField(
            name, **self._field_common(column), **self._string_common(column)
        )

    @converts("sqlalchemy_utils.types.phone_number.PhoneNumberType")
    def conv_phonenumbers(self, name: str, column: Column) -> BaseField:
        return PhoneField(
            name, **self._field_common(column), **self._string_common(column)
        )

    @converts("sqlalchemy_utils.types.scalar_list.ScalarListType")
    def conv_scalar_list(self, name: str, column: Column) -> BaseField:
        return ListField(StringField(name, **self._field_common(column)))

    @converts("sqlalchemy_utils.types.url.URLType")
    def conv_url(self, name: str, column: Column) -> BaseField:
        return URLField(name, **self._field_common(column))

    @converts("sqlalchemy_utils.types.timezone.TimezoneType")
    def conv_timezone(self, name: str, column: Column) -> BaseField:
        return TimeZoneField(
            name,
            coerce=column.type.python_type,
            **self._field_common(column),
        )

    @converts("sqlalchemy_utils.types.country.CountryType")
    def conv_country(self, name: str, column: Column) -> BaseField:
        return CountryField(name, **self._field_common(column))

    @converts("sqlalchemy_utils.types.currency.CurrencyType")
    def conv_currency(self, name: str, column: Column) -> BaseField:
        return CurrencyField(name, **self._field_common(column))

    @converts("sqlalchemy_utils.types.choice.ChoiceType")
    def conv_choice(self, name: str, column: Column) -> BaseField:
        choices = column.type.choices
        if isinstance(choices, type) and issubclass(choices, enum.Enum):
            return EnumField(
                name,
                enum=choices,
                **self._field_common(column),
                coerce=column.type.python_type,
            )
        return EnumField(name, choices=choices, **self._field_common(column), coerce=column.type.python_type)  # type: ignore

    #

    @converts("sqlalchemy_utils.types.pg_composite.CompositeType")
    def conv_composite_type(self, name: str, column: Column) -> BaseField:
        fields = []
        for col in column.type.columns:
            fields.append(self.get_converter(col)(col.name, col))
        return CollectionField(
            name, fields=fields, required=self._field_common(column)["required"]
        )
