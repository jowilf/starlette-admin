import enum
import ipaddress
import uuid
from uuid import UUID

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

import arrow
import pytest
import pytest_asyncio
from arrow import Arrow
from colour import Color
from httpx2 import AsyncClient
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
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
    IPAddressField,
    ListField,
    PasswordField,
    PhoneField,
    StringField,
    TimeZoneField,
    URLField,
    UUIDField,
)
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


class Base(DeclarativeBase):
    pass


class Counter(enum.StrEnum):
    ONE = "one"
    TWO = "two"


class Model(Base):
    __tablename__ = "model"

    uuid: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    choice: Mapped[int | None] = mapped_column(
        ChoiceType([(1, "One"), (2, "Two")], impl=Integer())
    )
    counter: Mapped[Counter | None] = mapped_column(ChoiceType(Counter))
    arrow: Mapped[Arrow | None] = mapped_column(ArrowType, default=arrow.utcnow)
    url: Mapped[str | None] = mapped_column(URLType)
    email: Mapped[str | None] = mapped_column(EmailType)
    ip_address: Mapped[ipaddress.IPv4Address | ipaddress.IPv6Address | None] = (
        mapped_column(IPAddressType)
    )
    country: Mapped[Country | None] = mapped_column(CountryType)
    color: Mapped[Color | None] = mapped_column(ColorType)
    timezone: Mapped[zoneinfo.ZoneInfo | None] = mapped_column(
        TimezoneType(backend="zoneinfo")
    )
    currency: Mapped[Currency | None] = mapped_column(CurrencyType)
    scalars: Mapped[list[str] | None] = mapped_column(ScalarListType)
    phonenumber: Mapped[str | None] = mapped_column(PhoneNumberType)
    password: Mapped[str | None] = mapped_column(
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(50))
    _type: Mapped[str | None] = mapped_column(String(50))


class SpecialItem(BaseItem):
    __tablename__ = "special_items"
    __mapper_args__ = {"polymorphic_identity": "special_item"}

    id: Mapped[int] = mapped_column(ForeignKey("base_items.id"), primary_key=True)
    special_power: Mapped[str | None] = mapped_column(String(50))


async def test_model_fields_conversion():
    from dataclasses import replace

    fields = ModelView(Model).fields
    arrow_field = next(f for f in fields if f.name == "arrow")
    # The converter auto-detects the Python-side callable default and wraps it
    # so it can be invoked without a SQLAlchemy execution context.
    assert arrow_field.default is not None
    assert arrow_field.default().isoformat()

    # Compare the remaining fields, ignoring the auto-detected arrow default.
    fields_for_comparison = [
        replace(f, default=None) if f.name == "arrow" else f for f in fields
    ]
    assert fields_for_comparison == [
        UUIDField("uuid", exclude_from_create=True, exclude_from_edit=True),
        EnumField("choice", choices=((1, "One"), (2, "Two")), coerce=int),
        EnumField("counter", enum=Counter, coerce=str),
        ArrowField("arrow"),
        URLField("url"),
        EmailField("email"),
        IPAddressField("ip_address", ipv4=True, ipv6=True),
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
    async with csrf_async_client(app) as c:
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

    response = await client.get(f"/admin/model/detail?pk={model.uuid}")
    assert response.status_code == 200


async def test_composite_type():
    from sqlalchemy_utils.types.pg_composite import (
        CompositeType,
        after_drop,
        before_create,
    )

    class CompositeModel(Base):
        __tablename__ = "compositemodel"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        balance = mapped_column(
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
