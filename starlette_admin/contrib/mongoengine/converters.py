import inspect
from typing import Any, Callable, Dict, Optional, Sequence, Type, Union

import mongoengine.fields as me
import starlette_admin.contrib.mongoengine.fields as internal_fields
import starlette_admin.fields as sa
from starlette_admin.contrib.mongoengine.exceptions import NotSupportedField
from starlette_admin.helpers import slugify_class_name


def converts(
    *args: Type[me.BaseField],
) -> Callable[
    [Callable[["ModelConverter", me.BaseField], sa.BaseField]],
    Callable[["ModelConverter", me.BaseField], sa.BaseField],
]:
    def wrap(
        func: Callable[["ModelConverter", me.BaseField], sa.BaseField]
    ) -> Callable[["ModelConverter", me.BaseField], sa.BaseField]:
        func._converter_for = frozenset(args)  # type:ignore [attr-defined]
        return func

    return wrap


class BaseModelConverter:
    def __init__(
        self,
        converters: Optional[
            Dict[Type[me.BaseField], Callable[[me.BaseField], sa.BaseField]]
        ] = None,
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

    def get_converter(
        self, field: me.BaseField
    ) -> Callable[[sa.BaseField], sa.BaseField]:
        converter = self.converters.get(field.__class__)
        if converter is not None:
            return converter
        for cls in self.converters:
            if isinstance(field, cls):
                return self.converters.get(cls)
        raise NotSupportedField(
            f"Field {field.__class__.__name__} can not be converted automatically. Find the appropriate field "
            "manually or provide your custom converter"
        )

    def normalize_fields_list(
        self,
        fields: Sequence[Any],
        document: Type[me.Document],
    ) -> Sequence[sa.BaseField]:
        converted_fields = []
        for value in fields:
            if isinstance(value, sa.BaseField):
                converted_fields.append(value)
            else:
                if isinstance(value, me.BaseField):
                    field = value
                elif isinstance(value, str) and hasattr(document, value):
                    field = getattr(document, value)
                else:
                    raise ValueError(f"Can't find field with key {value}")
                converted_fields.append(self.get_converter(field)(field))
        return converted_fields


class ModelConverter(BaseModelConverter):
    @classmethod
    def _field_common(cls, field: me.BaseField) -> Dict[str, Any]:
        return {
            "name": field.name,
            "help_text": getattr(field, "help_text", None),
            "required": field.required,
        }

    @classmethod
    def _numeric_field_common(cls, field: me.BaseField) -> Dict[str, Any]:
        return {
            "min": getattr(field, "min_value", None),
            "max": getattr(field, "max_value", None),
        }

    @converts(me.StringField, me.ObjectIdField, me.UUIDField)
    def conv_string_field(
        self, field: Union[me.StringField, me.ObjectIdField, me.UUIDField]
    ) -> sa.BaseField:
        return sa.StringField(**self._field_common(field))

    @converts(me.IntField, me.LongField)
    def conv_int_field(self, field: Union[me.IntField, me.LongField]) -> sa.BaseField:
        return sa.IntegerField(
            **self._field_common(field), **self._numeric_field_common(field)
        )

    @converts(me.FloatField)
    def conv_float_field(self, field: me.FloatField) -> sa.BaseField:
        return sa.FloatField(**self._field_common(field))

    @converts(me.DecimalField, me.Decimal128Field)
    def conv_decimal_field(
        self, field: Union[me.DecimalField, me.Decimal128Field]
    ) -> sa.BaseField:
        return sa.DecimalField(
            **self._field_common(field), **self._numeric_field_common(field)
        )

    @converts(me.BooleanField)
    def conv_boolean_field(self, field: me.BooleanField) -> sa.BaseField:
        return sa.BooleanField(**self._field_common(field))

    @converts(me.DateTimeField, me.ComplexDateTimeField)
    def conv_datetime_field(
        self, field: Union[me.DateTimeField, me.ComplexDateTimeField]
    ) -> sa.BaseField:
        return sa.DateTimeField(**self._field_common(field))

    @converts(me.DateField)
    def conv_date_field(self, field: me.DateField) -> sa.BaseField:
        return sa.DateField(**self._field_common(field))

    @converts(me.EmailField)
    def conv_email_field(self, field: me.DateField) -> sa.BaseField:
        return sa.EmailField(**self._field_common(field))

    @converts(me.URLField)
    def conv_url_field(self, field: me.URLField) -> sa.BaseField:
        return sa.URLField(**self._field_common(field))

    @converts(me.MapField, me.DictField)
    def conv_map_field(self, field: Union[me.MapField, me.DictField]) -> sa.BaseField:
        return sa.JSONField(**self._field_common(field))

    @converts(me.FileField)
    def conv_file_field(self, field: me.FileField) -> sa.BaseField:
        return internal_fields.FileField(**self._field_common(field))

    @converts(me.ImageField)
    def conv_image_field(self, field: me.ImageField) -> sa.BaseField:
        return internal_fields.ImageField(**self._field_common(field))

    @converts(me.EnumField)
    def conv_enum_field(self, field: me.EnumField) -> sa.BaseField:
        return sa.EnumField(**self._field_common(field), enum=field._enum_cls)

    @converts(me.ReferenceField)
    def conv_reference_field(self, field: me.ReferenceField) -> sa.BaseField:
        dtype = field.document_type_obj
        identity = slugify_class_name(
            dtype if isinstance(dtype, str) else dtype.__name__
        )
        return sa.HasOne(**self._field_common(field), identity=identity)

    @converts(me.EmbeddedDocumentField)
    def conv_embedded_document_field(self, field: me.ReferenceField) -> sa.BaseField:
        document_type_obj: me.EmbeddedDocument = field.document_type
        _fields = []
        for _field in document_type_obj._fields_ordered:
            _fields.append(
                self.get_converter(getattr(document_type_obj, _field))(
                    getattr(document_type_obj, _field)
                )
            )
        return sa.CollectionField(field.name, _fields, field.required)

    @converts(me.ListField, me.SortedListField)
    def conv_list_field(
        self, field: Union[me.ListField, me.SortedListField]
    ) -> sa.BaseField:
        if field.field is None:
            raise ValueError(f'ListField "{field.name}" must have field specified')
        if isinstance(
            field.field,
            (me.ReferenceField, me.CachedReferenceField, me.LazyReferenceField),
        ):
            """To Many reference"""
            dtype = field.field.document_type_obj
            identity = slugify_class_name(
                dtype if isinstance(dtype, str) else dtype.__name__
            )
            return sa.HasMany(**self._field_common(field), identity=identity)
        field.field.name = field.name
        if isinstance(field.field, (me.DictField, me.MapField)):
            return self.get_converter(field.field)(field.field)
        if isinstance(field.field, me.EnumField):
            admin_field = self.get_converter(field.field)(field.field)
            admin_field.multiple = True
            return admin_field
        return sa.ListField(
            self.get_converter(field.field)(field.field), required=field.required
        )
