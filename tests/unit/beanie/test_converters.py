from beanie import Document
from pydantic import AwareDatetime, FutureDate, IPvAnyAddress, NaiveDatetime, PastDate
from starlette_admin.contrib.beanie.view import ModelView
from starlette_admin.fields import DateField, DateTimeField, IPAddressField


def test_conv_pydantic_date_past():
    class MyModel(Document):
        expires: PastDate
        created_at: AwareDatetime
        updated_at: NaiveDatetime

    view = ModelView(MyModel)
    date_field = next(f for f in view.fields if f.name == "expires")
    assert isinstance(date_field, DateField)
    assert DateTimeField("created_at", required=True, timezone=True) in view.fields
    assert DateTimeField("updated_at", required=True, timezone=False) in view.fields


def test_conv_pydantic_date_future():
    class MyModel(Document):
        valid_until: FutureDate

    view = ModelView(MyModel)
    date_field = next(f for f in view.fields if f.name == "valid_until")
    assert isinstance(date_field, DateField)


def test_conv_ip_address():
    class MyModel(Document):
        ip: IPvAnyAddress

    view = ModelView(MyModel)
    ip_field = next(f for f in view.fields if f.name == "ip")
    assert isinstance(ip_field, IPAddressField)
    assert ip_field.ipv4 is True
    assert ip_field.ipv6 is True


def test_register_converter_plugin_api():
    """`register_converter` (the plugin API) extends every new
    `BeanieModelConverter` instance, since it feeds `_external_converters`."""
    from starlette_admin.contrib.beanie.converters import (
        _EXTERNAL_CONVERTERS,
        BeanieModelConverter,
        register_converter,
    )
    from starlette_admin.fields import StringField

    class _PluginType:
        pass

    @register_converter(_PluginType)
    def _conv_plugin_type(*args, **kwargs):
        return StringField(**kwargs)

    try:
        converter = BeanieModelConverter()
        assert converter.get_converter(_PluginType) is _conv_plugin_type
    finally:
        del _EXTERNAL_CONVERTERS[_PluginType]
