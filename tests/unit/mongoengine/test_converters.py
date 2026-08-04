import mongoengine as me
from starlette_admin.contrib.mongoengine.view import ModelView
from starlette_admin.fields import UUIDField


class UUIDDocument(me.Document):
    uuid_scalar = me.UUIDField()


def test_conv_uuid_field():
    view = ModelView(UUIDDocument)
    field = next(f for f in view.fields if f.name == "uuid_scalar")
    assert isinstance(field, UUIDField)


def test_register_converter_plugin_api():
    """`register_converter` (the plugin API) extends every new
    `ModelConverter` instance, since it feeds `_external_converters`."""
    from starlette_admin.contrib.mongoengine.converters import (
        _EXTERNAL_CONVERTERS,
        ModelConverter,
        register_converter,
    )
    from starlette_admin.fields import StringField

    class _PluginFieldType(me.fields.BaseField):
        pass

    @register_converter(_PluginFieldType)
    def _conv_plugin_type(*args, **kwargs):
        return StringField(kwargs["field"].name)

    try:
        converter = ModelConverter()
        field = _PluginFieldType()
        field.name = "plugin_field"
        assert converter.get_converter(field) is _conv_plugin_type
    finally:
        del _EXTERNAL_CONVERTERS[_PluginFieldType]
