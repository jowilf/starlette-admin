import enum
import ipaddress
import uuid

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

import arrow
import pytest
import pytest_asyncio
from colour import Color
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Session,
    declarative_base,
)
from sqlalchemy_utils import (
    ArrowType,
    ChoiceType,
    ColorType,
    Country,
    CountryType,
    Currency,
    CurrencyType,
    EmailType,
    IPAddressType,
    PasswordType,
    PhoneNumberType,
    ScalarListType,
    TimezoneType,
    URLType,
    UUIDType,
)
from starlette.applications import Starlette
from starlette_admin import (
    ArrowField,
    CollectionField,
    ColorField,
    CountryField,
    CurrencyField,
    EmailField,
    EnumField,
    IntegerField,
    ListField,
    PasswordField,
    PhoneField,
    StringField,
    TimeZoneField,
    URLField,
)
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.sqla.utils import get_test_engine

pytestmark = pytest.mark.asyncio


Base = declarative_base()


class Counter(str, enum.Enum):
    ONE = "one"
    TWO = "two"


class Model(Base):
    __tablename__ = "model"

    uuid = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    choice = Column(ChoiceType([(1, "One"), (2, "Two")], impl=Integer()))
    counter = Column(ChoiceType(Counter))
    arrow = Column(ArrowType, default=arrow.utcnow())
    url = Column(URLType)
    email = Column(EmailType)
    ip_address = Column(IPAddressType)
    country = Column(CountryType)
    color = Column(ColorType)
    timezone = Column(TimezoneType(backend="zoneinfo"))
    currency = Column(CurrencyType)
    scalars = Column(ScalarListType)
    phonenumber = Column(PhoneNumberType)
    password = Column(
        PasswordType(
            schemes=["pbkdf2_sha512"],
        )
    )


# Test joined table polymorphic inheritance
class BaseItem(Base):
    __tablename__ = "base_items"
    __mapper_args__ = {
        "polymorphic_identity": "base_item",
        "polymorphic_on": "_type",
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    _type = Column(String(50))


class SpecialItem(BaseItem):
    __tablename__ = "special_items"
    __mapper_args__ = {"polymorphic_identity": "special_item"}

    id = Column(ForeignKey("base_items.id"), primary_key=True)
    special_power = Column(String(50))


async def test_model_fields_conversion():
    assert ModelView(Model).fields == [
        StringField("uuid", exclude_from_create=True, exclude_from_edit=True),
        EnumField("choice", choices=((1, "One"), (2, "Two")), coerce=int),
        EnumField("counter", enum=Counter, coerce=str),
        ArrowField("arrow"),
        URLField("url"),
        EmailField("email"),
        StringField("ip_address"),
        CountryField("country"),
        ColorField("color"),
        TimeZoneField("timezone", coerce=zoneinfo.ZoneInfo),
        CurrencyField("currency"),
        ListField(StringField("scalars")),
        PhoneField("phonenumber"),
        PasswordField("password"),
    ]


async def test_polymorphic():
    assert ModelView(BaseItem).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("name", maxlength=50),
        StringField("_type", maxlength=50),
    ]
    assert ModelView(SpecialItem).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("special_power", maxlength=50),
        StringField("name", maxlength=50),
        StringField("_type", maxlength=50),
    ]


@pytest.fixture
def engine(fake_image) -> Engine:
    _engine = get_test_engine()
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest_asyncio.fixture
async def client(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(Model))
    app = Starlette()
    admin.mount_to(app)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


async def test_create(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/model/create",
        data={
            "choice": "1",
            "counter": "one",
            "arrow": "2023-01-06T16:12:16+00:00",
            "url": "https://example.com",
            "email": "admin@example.com",
            "ip_address": "192.123.45.55",
            "country": "BJ",
            "color": "#fde",
            "timezone": "Africa/Porto-Novo",
            "currency": "XOF",
            "scalars.1": "item-1",
            "scalars.2": "item-2",
            "phonenumber": "+358401234567",
            "password": "pass1234",
            # "balance.currency": "XOF",
            # "balance.amount": "1000000",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Model).where(Model.email == "admin@example.com")
    model = session.execute(stmt).scalar_one()
    assert model is not None
    assert model.choice == 1
    assert model.counter == Counter("one")
    assert model.arrow == arrow.get("2023-01-06T16:12:16+00:00")
    assert model.url == "https://example.com"
    assert model.email == "admin@example.com"
    assert model.ip_address == ipaddress.ip_address("192.123.45.55")
    assert model.country == Country("BJ")
    assert model.color == Color("#fde")
    assert model.timezone == zoneinfo.ZoneInfo("Africa/Porto-Novo")
    assert model.currency == Currency("XOF")
    assert model.scalars == ["item-1", "item-2"]
    assert model.phonenumber.e164 == "+358401234567"
    assert model.password == "pass1234"

    response = await client.get(f"/admin/model/detail/{model.uuid}")
    assert response.status_code == 200


async def test_composite_type():
    from sqlalchemy_utils.types.pg_composite import (
        CompositeType,
        after_drop,
        before_create,
    )

    class CompositeModel(Base):
        __tablename__ = "compositemodel"

        id = Column(Integer, primary_key=True)
        balance = Column(
            CompositeType(
                "money_type",
                [Column("currency", CurrencyType), Column("amount", Integer)],
            )
        )

    assert ModelView(CompositeModel).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        CollectionField(
            "balance",
            fields=[
                CurrencyField("currency", searchable=False, orderable=False),
                IntegerField("amount", searchable=False, orderable=False),
            ],
        ),
    ]
    # Remove all listeners added by CompositeType
    listeners = [
        (MetaData, "before_create", before_create),
        (MetaData, "after_drop", after_drop),
    ]
    for listener in listeners:
        event.remove(*listener)
