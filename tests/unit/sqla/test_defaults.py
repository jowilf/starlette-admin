import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    Time,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    FloatField,
    IntegerField,
    JSONField,
    StringField,
    TextAreaField,
    TimeField,
)
from starlette_admin.contrib.sqla.view import ModelView


class Base(DeclarativeBase):
    pass


class Status(enum.StrEnum):
    NEW = "new"
    DONE = "done"


class DefaultModel(Base):
    __tablename__ = "default_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    string_scalar: Mapped[str] = mapped_column(String(100), default="hello")
    text_scalar: Mapped[str] = mapped_column(Text, default="world")
    int_scalar: Mapped[int] = mapped_column(Integer, default=42)
    bool_scalar: Mapped[bool] = mapped_column(Boolean, default=True)
    float_scalar: Mapped[float] = mapped_column(Float, default=3.14)
    enum_scalar: Mapped[Status] = mapped_column(Enum(Status), default=Status.NEW)
    date_scalar: Mapped[date] = mapped_column(Date, default=date(2025, 1, 1))
    datetime_scalar: Mapped[datetime] = mapped_column(
        DateTime, default=datetime(2025, 1, 1, 12, 0)
    )
    time_scalar: Mapped[time] = mapped_column(Time, default=time(12, 30))
    json_scalar: Mapped[dict] = mapped_column(JSON, default={"x": 1})
    callable_default: Mapped[str] = mapped_column(
        String(100), default=lambda: "from-callable"
    )
    datetime_callable: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    uuid_callable: Mapped[str] = mapped_column(String(36), default=uuid.uuid4)
    func_now: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    server_default_string: Mapped[str] = mapped_column(
        String(100), server_default="active"
    )
    server_default_text: Mapped[str] = mapped_column(
        String(100), server_default=text("'active'")
    )


def test_scalar_defaults_are_detected():
    view = ModelView(DefaultModel)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["string_scalar"] == StringField(
        "string_scalar", default="hello", maxlength=100
    )
    assert fields_by_name["text_scalar"] == TextAreaField(
        "text_scalar", default="world"
    )
    assert fields_by_name["int_scalar"] == IntegerField("int_scalar", default=42)
    assert fields_by_name["bool_scalar"] == BooleanField("bool_scalar", default=True)
    assert fields_by_name["float_scalar"] == FloatField("float_scalar", default=3.14)
    assert fields_by_name["enum_scalar"] == EnumField(
        "enum_scalar", enum=Status, default=Status.NEW
    )
    assert fields_by_name["date_scalar"] == DateField(
        "date_scalar", default=date(2025, 1, 1)
    )
    assert fields_by_name["datetime_scalar"] == DateTimeField(
        "datetime_scalar", default=datetime(2025, 1, 1, 12, 0)
    )
    assert fields_by_name["time_scalar"] == TimeField(
        "time_scalar", default=time(12, 30)
    )
    assert fields_by_name["json_scalar"] == JSONField("json_scalar", default={"x": 1})


def test_callable_defaults_are_detected():
    view = ModelView(DefaultModel)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["callable_default"].default() == "from-callable"

    before = datetime.now()
    dt_value = fields_by_name["datetime_callable"].default()
    after = datetime.now()
    assert before <= dt_value <= after

    uuid_value = fields_by_name["uuid_callable"].default()
    assert isinstance(uuid_value, uuid.UUID)


def test_sql_expression_defaults_are_skipped():
    view = ModelView(DefaultModel)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["func_now"] == DateTimeField("func_now")


def test_server_defaults_are_skipped():
    view = ModelView(DefaultModel)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["server_default_string"] == StringField(
        "server_default_string", maxlength=100
    )
    assert fields_by_name["server_default_text"] == StringField(
        "server_default_text", maxlength=100
    )


def test_required_is_false_when_python_default_exists():
    view = ModelView(DefaultModel)
    fields_by_name = {f.name: f for f in view.fields}

    assert fields_by_name["string_scalar"].required is False
    assert fields_by_name["callable_default"].required is False


def test_label_column_default_is_skipped():
    from sqlalchemy import literal_column
    from sqlalchemy.sql.elements import Label
    from starlette_admin.contrib.sqla.converters import BaseSQLAModelConverter

    label_col = literal_column("1").label("alias")
    assert isinstance(label_col, Label)
    assert BaseSQLAModelConverter._extract_default(label_col) is None


def test_decimal_default_is_detected():
    class DecimalModel(Base):
        __tablename__ = "decimal_model"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        amount: Mapped[Decimal] = mapped_column(
            Float(asdecimal=True), default=Decimal("9.99")
        )

    view = ModelView(DecimalModel)
    from starlette_admin import DecimalField

    assert view.fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        DecimalField("amount", default=Decimal("9.99")),
    ]
