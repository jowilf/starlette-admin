# Inspired by wtforms-sqlalchemy
import enum
import inspect
from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import ARRAY, Boolean, Column, Float, String
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
from sqlalchemy.sql.elements import ColumnElement, Label
from starlette_admin.contrib.sqla.exceptions import NotSupportedColumn
from starlette_admin.contrib.sqla.fields import FileField, ImageField
from starlette_admin.converters import BaseModelConverter, converts
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
    IPAddressField,
    JSONField,
    ListField,
    PasswordField,
    PhoneField,
    StringField,
    TextAreaField,
    TimeField,
    TimeZoneField,
    URLField,
    UUIDField,
)
from starlette_admin.helpers import slugify_class_name
from starlette_admin.logging import get_logger

_log = get_logger(__name__)

# Converters registered by plugins for SQLAlchemy column types, merged into
# every BaseSQLAModelConverter instance (see BaseModelConverter._external_converters).
_EXTERNAL_CONVERTERS: dict[Any, Callable[..., BaseField]] = {}


def register_converter(
    *types: Any,
) -> Callable[[Callable[..., BaseField]], Callable[..., BaseField]]:
    """Register an external converter for SQLAlchemy column types.

    Decorator form mirrors `@converts`. Used by plugins from `setup()`:

    ```python
    @register_converter(Geometry)
    def convert_geometry(*args, **kwargs) -> BaseField:
        return PointField(**kwargs)
    ```

    Each type is keyed by its fully-qualified `module.ClassName`, the same
    format `find_converter_for_col_type` checks first, so a plugin's column
    type can never collide with an unrelated core/plugin type of the same
    short name.
    """

    def wrap(func: Callable[..., BaseField]) -> Callable[..., BaseField]:
        for col_type in types:
            _EXTERNAL_CONVERTERS[f"{col_type.__module__}.{col_type.__name__}"] = func
        return func

    return wrap


class BaseSQLAModelConverter(BaseModelConverter):
    def _external_converters(self) -> dict[Any, Callable[..., BaseField]]:
        return _EXTERNAL_CONVERTERS

    @classmethod
    def _extract_default(cls, column: ColumnElement) -> Any:
        """Return a Python-usable default value from a SQLAlchemy column.

        Only Python-side defaults (`Column.default`) on non-primary-key
        columns are extracted. Primary keys are typically auto-generated and
        are not pre-filled in create forms. Scalar defaults are returned
        as-is; callable defaults (e.g. ``datetime.now`` or ``uuid.uuid4``)
        are wrapped so they can be invoked without a SQLAlchemy execution
        context. SQL-expression defaults (``func.now()``) and server-side
        defaults are ignored because they cannot be meaningfully pre-filled
        in an HTML form.
        """
        column_name = getattr(column, "name", None)
        if isinstance(column, Label):
            _log.debug("_extract_default: skipping label column")
            return None
        if getattr(column, "primary_key", False):
            _log.debug(
                "_extract_default: skipping primary key column '%s'", column_name
            )
            return None
        if column.default is not None:
            if getattr(column.default, "is_scalar", False):
                default_value = column.default.arg
                _log.debug(
                    "_extract_default: scalar default for '%s' = %r",
                    column_name,
                    default_value,
                )
                return default_value
            if getattr(column.default, "is_callable", False):
                sa_arg = column.default.arg
                _log.debug(
                    "_extract_default: callable default for '%s' (%r)",
                    column_name,
                    sa_arg,
                )
                return lambda: sa_arg(None)
            _log.debug(
                "_extract_default: unsupported default for '%s' (%r)",
                column_name,
                column.default,
            )
        else:
            _log.debug("_extract_default: no default for '%s'", column_name)
        return None

    def get_converter(self, col_type: Any) -> Callable[..., BaseField]:
        converter = self.find_converter_for_col_type(type(col_type))
        if converter is not None:
            return converter
        raise NotSupportedColumn(  # pragma: no cover
            f"Column {col_type} can not be converted automatically. Find the appropriate field manually or provide "
            "your custom converter"
        )

    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        col_type = kwargs.get("type")
        field = self.get_converter(col_type)(*args, **kwargs)
        _log.debug(
            "Converted column %r (%s) → %s",
            kwargs.get("name"),
            type(col_type).__name__,
            type(field).__name__,
        )
        return field

    def find_converter_for_col_type(
        self,
        col_type: Any,
    ) -> Callable[..., BaseField] | None:
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

            # Custom types built on TypeDecorator expose the underlying
            # implementation type via `impl`; fall back to converting that.
            if hasattr(col_type, "impl"):
                impl = (
                    col_type.impl
                    if callable(col_type.impl)
                    else col_type.impl.__class__
                )
                return self.find_converter_for_col_type(impl)
        return None  # pragma: no cover

    def convert_fields_list(
        self,
        *,
        fields: Sequence[Any],
        model: type[Any],
        explicit_fields: bool = False,
        **kwargs: Any,
    ) -> Sequence[BaseField]:
        mapper: Mapper = kwargs["mapper"]
        _log.debug(
            "convert_fields_list for %s (%d field(s))", model.__name__, len(fields)
        )
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
                    _log.error(
                        "Cannot find column with key %r in model %s",
                        field,
                        model.__name__,
                    )
                    raise ValueError(f"Can't find column with key {field}")
                if isinstance(attr, RelationshipProperty):
                    key = slugify_class_name(attr.entity.class_.__name__)
                    _log.debug(
                        "Converting relationship %r (%s) for %s",
                        attr.key,
                        attr.direction.name,
                        model.__name__,
                    )
                    if attr.direction.name == "MANYTOONE" or (
                        attr.direction.name == "ONETOMANY" and not attr.uselist
                    ):
                        # The FK column(s) backing a MANYTOONE relation live on
                        # this model; mirror their nullability onto the
                        # relation field so it shows as required in the form.
                        # A reverse ONETOMANY (uselist=False) has its FK on the
                        # other model, so it can't be derived here.
                        required = attr.direction.name == "MANYTOONE" and all(
                            not local_col.nullable
                            for local_col, _ in attr.local_remote_pairs
                        )
                        converted_fields.append(
                            HasOne(attr.key, key=key, required=required)
                        )
                    else:
                        converted_fields.append(
                            HasMany(
                                attr.key,
                                key=key,
                                collection_class=attr.collection_class or list,
                            )
                        )
                elif isinstance(attr, ColumnProperty):
                    # A primary key column redeclared on a subclass in joined-table
                    # polymorphic inheritance still needs a field of its own.
                    is_inherited_pk = mapper.inherits is not None and any(
                        col.primary_key for col in attr.columns
                    )
                    if is_inherited_pk:
                        column = attr.columns[0]
                        converted_fields.append(
                            self.convert(
                                name=attr.key, type=column.type, column=column
                            ),
                        )
                    else:
                        assert len(attr.columns) == 1, (
                            "Multiple-column properties are not supported"
                        )
                        column = attr.columns[0]
                        if not column.foreign_keys or explicit_fields:
                            converted_field = self.convert(
                                name=attr.key, type=column.type, column=column
                            )
                            converted_fields.append(converted_field)
        _log.debug(
            "convert_fields_list for %s → %d converted field(s)",
            model.__name__,
            len(converted_fields),
        )
        return converted_fields


class ModelConverter(BaseSQLAModelConverter):
    @classmethod
    def _field_common(
        cls, *, name: str, column: ColumnElement, **kwargs: Any
    ) -> dict[str, Any]:
        if isinstance(column, Label):
            return {
                "name": column.key,
                "exclude_from_edit": True,
                "exclude_from_create": True,
            }
        return {
            "name": name,
            "help_text": column.comment,
            "default": cls._extract_default(column),
            "required": (
                not column.nullable
                and not isinstance(column.type, (Boolean,))
                and not column.default
                and not column.server_default
            ),
        }

    @classmethod
    def _string_common(cls, *, type: Any, **kwargs: Any) -> dict[str, Any]:
        if (
            isinstance(type, String)
            and isinstance(type.length, int)
            and type.length > 0
        ):
            return {"maxlength": type.length}
        return {}

    @classmethod
    def _file_common(cls, *, type: Any, **kwargs: Any) -> dict[str, Any]:
        return {"multiple": getattr(type, "multiple", False)}

    @converts(
        "String",
        "sqlalchemy.dialects.postgresql.base.MACADDR",
        "sqlalchemy.dialects.postgresql.types.MACADDR",
        "sqlalchemy_utils.types.locale.LocaleType",
    )  # includes Unicode
    def conv_string(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts(
        "sqlalchemy.sql.sqltypes.Uuid",
        "sqlalchemy.dialects.postgresql.base.UUID",
        "sqlalchemy_utils.types.uuid.UUIDType",
    )
    def conv_uuid(self, *args: Any, **kwargs: Any) -> BaseField:
        return UUIDField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts(
        "sqlalchemy.dialects.postgresql.base.INET",
        "sqlalchemy.dialects.postgresql.types.INET",
        "sqlalchemy_utils.types.ip_address.IPAddressType",
    )
    def conv_ip_address(self, *args: Any, **kwargs: Any) -> BaseField:
        return IPAddressField(
            ipv4=True,
            ipv6=True,
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts("Text", "LargeBinary", "Binary")  # includes UnicodeText
    def conv_text(self, *args: Any, **kwargs: Any) -> BaseField:
        return TextAreaField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts("Boolean", "BIT")
    def conv_boolean(self, *args: Any, **kwargs: Any) -> BaseField:
        return BooleanField(
            **self._field_common(*args, **kwargs),
        )

    @converts("DateTime")
    def conv_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateTimeField(
            **self._field_common(*args, **kwargs),
        )

    @converts("Date")
    def conv_date(self, *args: Any, **kwargs: Any) -> BaseField:
        return DateField(
            **self._field_common(*args, **kwargs),
        )

    @converts("Time")
    def conv_time(self, *args: Any, **kwargs: Any) -> BaseField:
        return TimeField(
            **self._field_common(*args, **kwargs),
        )

    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        assert hasattr(_type, "enum_class")
        return EnumField(**self._field_common(*args, **kwargs), enum=_type.enum_class)

    @converts("Integer")  # includes BigInteger and SmallInteger
    def conv_integer(self, *args: Any, **kwargs: Any) -> BaseField:
        unsigned = getattr(kwargs["type"], "unsigned", False)
        extra = self._field_common(*args, **kwargs)
        if unsigned:
            extra["min"] = 0
        return IntegerField(**extra)

    @converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    def conv_numeric(self, *args: Any, **kwargs: Any) -> BaseField:
        if isinstance(kwargs["type"], Float) and not kwargs["type"].asdecimal:
            return FloatField(
                **self._field_common(*args, **kwargs),
            )
        return DecimalField(
            **self._field_common(*args, **kwargs),
        )

    @converts(
        "sqlalchemy.dialects.mysql.types.YEAR", "sqlalchemy.dialects.mysql.base.YEAR"
    )
    def conv_mysql_year(self, *args: Any, **kwargs: Any) -> BaseField:
        return IntegerField(**self._field_common(*args, **kwargs), min=1901, max=2155)

    @converts("ARRAY")
    def conv_array(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        if isinstance(_type, ARRAY) and (
            _type.dimensions is None or _type.dimensions == 1
        ):
            kwargs.update(
                {
                    "column": Column(kwargs["name"], _type.item_type),
                    "type": _type.item_type,
                }
            )
            return ListField(self.convert(*args, **kwargs))
        raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")

    @converts(
        "JSON",
        "sqlalchemy_utils.types.json.JSONType",
        "sqlalchemy.dialects.postgresql.hstore.HSTORE",
    )
    def conv_json(self, *args: Any, **kwargs: Any) -> BaseField:
        return JSONField(**self._field_common(*args, **kwargs))

    @converts("sqlalchemy_file.types.FileField")
    def conv_sqla_filefield(self, *args: Any, **kwargs: Any) -> BaseField:
        return FileField(
            **self._field_common(*args, **kwargs), **self._file_common(*args, **kwargs)
        )

    @converts("sqlalchemy_file.types.ImageField")
    def conv_sqla_imagefield(self, *args: Any, **kwargs: Any) -> BaseField:
        return ImageField(
            **self._field_common(*args, **kwargs), **self._file_common(*args, **kwargs)
        )

    @converts("sqlalchemy_utils.types.arrow.ArrowType")
    def conv_arrow(self, *args: Any, **kwargs: Any) -> BaseField:
        return ArrowField(
            **self._field_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.color.ColorType")
    def conv_color(self, *args: Any, **kwargs: Any) -> BaseField:
        return ColorField(
            **self._field_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.email.EmailType")
    def conv_email(self, *args: Any, **kwargs: Any) -> BaseField:
        return EmailField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.password.PasswordType")
    def conv_password(self, *args: Any, **kwargs: Any) -> BaseField:
        return PasswordField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.phone_number.PhoneNumberType")
    def conv_phonenumbers(self, *args: Any, **kwargs: Any) -> BaseField:
        return PhoneField(
            **self._field_common(*args, **kwargs),
            **self._string_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.scalar_list.ScalarListType")
    def conv_scalar_list(self, *args: Any, **kwargs: Any) -> BaseField:
        return ListField(
            StringField(
                **self._field_common(*args, **kwargs),
            )
        )

    @converts("sqlalchemy_utils.types.url.URLType")
    def conv_url(self, *args: Any, **kwargs: Any) -> BaseField:
        return URLField(
            **self._field_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.timezone.TimezoneType")
    def conv_timezone(self, *args: Any, **kwargs: Any) -> BaseField:
        return TimeZoneField(
            **self._field_common(*args, **kwargs),
            coerce=kwargs["type"].python_type,
        )

    @converts("sqlalchemy_utils.types.country.CountryType")
    def conv_country(self, *args: Any, **kwargs: Any) -> BaseField:
        return CountryField(
            **self._field_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.currency.CurrencyType")
    def conv_currency(self, *args: Any, **kwargs: Any) -> BaseField:
        return CurrencyField(
            **self._field_common(*args, **kwargs),
        )

    @converts("sqlalchemy_utils.types.choice.ChoiceType")
    def conv_choice(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        choices = _type.choices
        if isinstance(choices, type) and issubclass(choices, enum.Enum):
            return EnumField(
                **self._field_common(*args, **kwargs),
                enum=choices,
                coerce=_type.python_type,
            )
        return EnumField(
            **self._field_common(*args, **kwargs),
            choices=choices,
            coerce=_type.python_type,
        )

    @converts("sqlalchemy_utils.types.pg_composite.CompositeType")
    def conv_composite_type(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        fields = []
        field_common = self._field_common(*args, **kwargs)
        for col in _type.columns:
            kwargs.update({"name": col.name, "column": col, "type": col.type})
            fields.append(self.convert(*args, **kwargs))
        return CollectionField(
            field_common["name"], fields=fields, required=field_common["required"]
        )
