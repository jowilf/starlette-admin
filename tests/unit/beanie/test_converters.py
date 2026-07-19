from beanie import Document
from pydantic import FutureDate, IPvAnyAddress, PastDate
from starlette_admin.contrib.beanie.view import ModelView
from starlette_admin.fields import DateField, IPAddressField


def test_conv_pydantic_date_past():
    class MyModel(Document):
        expires: PastDate

    view = ModelView(MyModel)
    date_field = next(f for f in view.fields if f.name == "expires")
    assert isinstance(date_field, DateField)


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
