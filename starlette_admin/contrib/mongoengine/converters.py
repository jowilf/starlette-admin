from collections.abc import Callable, Sequence
from typing import Any, cast

import mongoengine.fields as me
import starlette_admin.contrib.mongoengine.fields as internal_fields
import starlette_admin.fields as sa
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField
from starlette_admin.converters import BaseModelConverter, converts
from starlette_admin.helpers import slugify_class_name

# Converters registered by plugins for mongoengine field types, merged into
# every BaseMongoEngineModelConverter instance (see
# BaseModelConverter._external_converters).
_EXTERNAL_CONVERTERS: dict[Any, Callable[..., sa.BaseField]] = {}


def register_converter(
    *types: Any,
) -> Callable[[Callable[..., sa.BaseField]], Callable[..., sa.BaseField]]:
    """Register an external converter for mongoengine field types.
    Decorator form mirrors `@converts`. Used by plugins."""

    def wrap(func: Callable[..., sa.BaseField]) -> Callable[..., sa.BaseField]:
        for field_type in types:
            _EXTERNAL_CONVERTERS[field_type] = func
        return func

    return wrap


class BaseMongoEngineModelConverter(BaseModelConverter):
    """Base class for converting mongoengine document fields to admin fields.

    Subclasses register one converter method per mongoengine field type using
    the [converts][starlette_admin.converters.converts] decorator.
    """

    def _external_converters(self) -> dict[Any, Callable[..., sa.BaseField]]:
        return _EXTERNAL_CONVERTERS

    def get_converter(self, field: me.BaseField) -> Callable[..., sa.BaseField]:
        """Look up the converter function registered for `field`'s type.

        Tries an exact class match first, then falls back to the first
        registered class that `field` is an instance of, so a converter
        registered for a base mongoengine field type also matches its subclasses.

        Raises:
            NotSupportedField: If no registered converter matches `field`'s type.
        """
        if field.__class__ in self.converters:
            return self.converters[field.__class__]
        for cls, converter in self.converters.items():
            if isinstance(field, cls):
                return converter
        raise NotSupportedField(
            f"Field {field.__class__.__name__} can not be converted automatically. Find the appropriate field "
            "manually or provide your custom converter"
        )

    def convert(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        """Convert a single mongoengine field, passed as the `field` keyword argument,
        to its admin field equivalent.
        """
        return self.get_converter(cast(me.BaseField, kwargs.get("field")))(
            *args, **kwargs
        )

    def convert_fields_list(
        self,
        *,
        fields: Sequence[Any],
        model: type[me.Document],
        **kwargs: Any,
    ) -> Sequence[sa.BaseField]:
        """Convert a mixed list of field specs into a list of admin fields.

        Each entry in `fields` may already be a `sa.BaseField` instance (passed
        through unchanged), a mongoengine field instance, or a string naming an
        attribute on `model`.

        Parameters:
            fields: The field specs to convert.
            model: The document class `fields` entries are resolved against
                when given as attribute-name strings.

        Returns:
            The converted admin fields, in the same order as `fields`.

        Raises:
            ValueError: If a string entry does not name an attribute on `model`.
        """
        converted_fields = []
        for value in fields:
            if isinstance(value, sa.BaseField):
                converted_fields.append(value)
            else:
                if isinstance(value, me.BaseField):
                    field = value
                elif isinstance(value, str) and hasattr(model, value):
                    field = getattr(model, value)
                else:
                    raise ValueError(f"Can't find field with key {value}")
                converted_fields.append(self.convert(field=field))
        return converted_fields


class ModelConverter(BaseMongoEngineModelConverter):
    """Default converter mapping mongoengine field types to `starlette_admin` fields."""

    @classmethod
    def _extract_default(cls, field: me.BaseField) -> Any:
        """Return a Python-usable default value from a mongoengine field.

        Primary keys are excluded since they are auto-generated and are not
        pre-filled in create forms. Both scalar defaults (e.g. ``default=0``)
        and callable defaults (e.g. ``default=datetime.utcnow`` or
        ``default=list``) are supported, as `BaseField.default` already
        accepts either.
        """
        if getattr(field, "primary_key", False):
            return None
        return field.default

    @classmethod
    def _field_common(cls, *, field: me.BaseField, **kwargs: Any) -> dict[str, Any]:
        """Return the kwargs shared by every field conversion: name, help text,
        required flag, and default value.
        """
        return {
            "name": field.name,
            "help_text": getattr(field, "help_text", None),
            "required": field.required,
            "default": cls._extract_default(field),
        }

    @classmethod
    def _numeric_field_common(
        cls, *, field: me.BaseField, **kwargs: Any
    ) -> dict[str, Any]:
        """Return the `min`/`max` kwargs for numeric field conversions, read from
        mongoengine's `min_value`/`max_value` validators.
        """
        return {
            "min": getattr(field, "min_value", None),
            "max": getattr(field, "max_value", None),
        }

    @converts(me.StringField)
    def conv_string_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.StringField(**self._field_common(*args, **kwargs))

    @converts(me.UUIDField)
    def conv_uuid_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.UUIDField(**self._field_common(*args, **kwargs))

    @converts(me.ObjectIdField)
    def conv_object_id_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return internal_fields.ObjectIdField(**self._field_common(*args, **kwargs))

    @converts(me.IntField, me.LongField)
    def conv_int_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.IntegerField(
            **self._field_common(*args, **kwargs),
            **self._numeric_field_common(*args, **kwargs),
        )

    @converts(me.FloatField)
    def conv_float_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.FloatField(**self._field_common(*args, **kwargs))

    @converts(me.DecimalField, me.Decimal128Field)
    def conv_decimal_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DecimalField(
            **self._field_common(*args, **kwargs),
            **self._numeric_field_common(*args, **kwargs),
        )

    @converts(me.BooleanField)
    def conv_boolean_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.BooleanField(**self._field_common(*args, **kwargs))

    @converts(me.DateTimeField, me.ComplexDateTimeField)
    def conv_datetime_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DateTimeField(**self._field_common(*args, **kwargs))

    @converts(me.DateField)
    def conv_date_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DateField(**self._field_common(*args, **kwargs))

    @converts(me.EmailField)
    def conv_email_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.EmailField(**self._field_common(*args, **kwargs))

    @converts(me.URLField)
    def conv_url_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.URLField(**self._field_common(*args, **kwargs))

    @converts(me.MapField, me.DictField)
    def conv_map_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.JSONField(**self._field_common(*args, **kwargs))

    @converts(me.FileField)
    def conv_file_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return internal_fields.FileField(**self._field_common(*args, **kwargs))

    @converts(me.ImageField)
    def conv_image_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return internal_fields.ImageField(**self._field_common(*args, **kwargs))

    @converts(me.EnumField)
    def conv_enum_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs["field"]
        # mongoengine stores the wrapped Python enum class on the private
        # `_enum_cls` attribute; there is no public accessor for it.
        return sa.EnumField(**self._field_common(*args, **kwargs), enum=field._enum_cls)

    @converts(me.ReferenceField)
    def conv_reference_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        """Convert a `ReferenceField` to a `HasOne` relation.

        `document_type_obj` is a class for direct references and a string for
        lazy references (declared before the target class exists); both are
        normalized to the same key slug.
        """
        field = kwargs["field"]
        dtype = field.document_type_obj
        key = slugify_class_name(dtype if isinstance(dtype, str) else dtype.__name__)
        return sa.HasOne(**self._field_common(*args, **kwargs), key=key)

    @converts(me.EmbeddedDocumentField)
    def conv_embedded_document_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        """Convert an `EmbeddedDocumentField` to a `CollectionField`.

        Recursively converts each field of the embedded document type, in the
        order declared on that type.
        """
        field = kwargs["field"]
        document_type_obj: me.EmbeddedDocument = field.document_type
        _fields = []
        for _field in document_type_obj._fields_ordered:
            kwargs["field"] = getattr(document_type_obj, _field)
            _fields.append(self.convert(*args, **kwargs))
        return sa.CollectionField(field.name, _fields, field.required)

    @converts(me.ListField, me.SortedListField)
    def conv_list_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        """Convert a `ListField`/`SortedListField` based on its inner field type.

        A list of references becomes a `HasMany` relation. A list of dicts or
        maps collapses to a single `JSONField`, since JSON already represents
        nested lists natively. A list of enum values becomes a multi-select
        dropdown over the enum's choices. Everything else is wrapped in a
        generic `ListField` around the converted inner field.

        Raises:
            ValueError: If the `ListField` was declared without an inner `field`.
        """
        field = kwargs["field"]
        if field.field is None:
            raise ValueError(f'ListField "{field.name}" must have field specified')
        if isinstance(
            field.field,
            (me.ReferenceField, me.CachedReferenceField, me.LazyReferenceField),
        ):
            # List of references: a to-many relationship.
            dtype = field.field.document_type_obj
            key = slugify_class_name(
                dtype if isinstance(dtype, str) else dtype.__name__
            )
            return sa.HasMany(**self._field_common(*args, **kwargs), key=key)
        field.field.name = field.name
        kwargs["field"] = field.field
        if isinstance(field.field, (me.DictField, me.MapField)):
            return self.convert(*args, **kwargs)
        if isinstance(field.field, me.EnumField):
            admin_field = self.convert(*args, **kwargs)
            assert isinstance(admin_field, sa.EnumField)
            admin_field.multiple = True
            admin_field.select2 = True
            return admin_field
        return sa.ListField(self.convert(*args, **kwargs), required=field.required)
