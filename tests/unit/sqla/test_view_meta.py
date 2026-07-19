import enum
import re
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest
import sqlalchemy_file
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    TypeDecorator,
)
from sqlalchemy.dialects.mysql import INTEGER, YEAR
from sqlalchemy.dialects.postgresql import BIT, HSTORE, INET, MACADDR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    column_property,
    mapped_column,
    relationship,
)
from sqlalchemy_file.exceptions import ValidationError as FileValidationError
from starlette_admin import (
    BooleanField,
    DateField,
    DateTimeField,
    DecimalField,
    EnumField,
    FloatField,
    HasMany,
    HasOne,
    IntegerField,
    IPAddressField,
    JSONField,
    ListField,
    StringField,
    TextAreaField,
    TimeField,
    UUIDField,
)
from starlette_admin.contrib.sqla.exceptions import (
    InvalidModelError,
    NotSupportedColumn,
)
from starlette_admin.contrib.sqla.fields import FileField, ImageField
from starlette_admin.contrib.sqla.view import ModelView
from starlette_admin.exceptions import FormValidationError


class Base(DeclarativeBase):
    pass


class Status(enum.StrEnum):
    NEW = "new"
    ONGOING = "ongoing"
    DONE = "done"


class User(Base):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(
        String(100), primary_key=True, comment="user fullname"
    )
    bio: Mapped[str | None] = mapped_column(Text)
    document: Mapped["Document"] = relationship(
        "Document", back_populates="user", uselist=False
    )


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image = mapped_column(sqlalchemy_file.ImageField)
    images = mapped_column(sqlalchemy_file.ImageField(multiple=True))
    file = mapped_column(sqlalchemy_file.FileField)
    files = mapped_column(sqlalchemy_file.FileField(multiple=True))
    document_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("document.int"))
    document: Mapped["Document"] = relationship(
        "Document", back_populates="attachments"
    )


class Document(Base):
    __tablename__ = "document"

    int: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="This is the primary key"
    )
    float: Mapped[float | None] = mapped_column(Float, nullable=True)
    decimal: Mapped[Decimal | None] = mapped_column(Float(asdecimal=True))
    bool: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    time: Mapped[time | None] = mapped_column(Time, nullable=True)
    enum: Mapped[Status | None] = mapped_column(Enum(Status))
    json_field: Mapped[dict | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String, dimensions=1))
    ints: Mapped[list[int] | None] = mapped_column(ARRAY(Integer, dimensions=1))
    user_name: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.name"))
    user: Mapped["User"] = relationship("User", back_populates="document")
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="document"
    )


class Other(Base):
    __tablename__ = "other"

    uuid: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True
    )
    bit: Mapped[bool | None] = mapped_column(BIT)
    year: Mapped[int | None] = mapped_column(YEAR)
    macaddr: Mapped[str | None] = mapped_column(MACADDR)
    inet: Mapped[str | None] = mapped_column(INET)
    hstore: Mapped[dict | None] = mapped_column(HSTORE)
    cp = column_property(macaddr + ";" + inet)


class UserView(ModelView):
    show_pk_in_forms = True


def test_view_meta_info():
    model_view = ModelView(
        Other, key="other-id", menu_label="Other label", display_name="Other name"
    )
    assert model_view.key == "other-id"
    assert model_view.menu_label == "Other label"
    assert model_view.display_name == "Other name"


def test_view_meta_info_with_class_level_config():
    class CustomView(ModelView):
        key = "custom-id"
        menu_label = "Custom label"
        display_name = "Custom name"

    model_view = CustomView(Other)
    assert model_view.key == "custom-id"
    assert model_view.menu_label == "Custom label"
    assert model_view.display_name == "Custom name"


def test_view_meta_info_with_overridden_class_level_config():
    class CustomView(ModelView):
        key = "custom-id"
        menu_label = "Custom label"
        display_name = "Custom name"

    model_view = CustomView(
        Other, key="other-id", menu_label="Other label", display_name="Other name"
    )
    assert model_view.key == "other-id"
    assert model_view.menu_label == "Other label"
    assert model_view.display_name == "Other name"


def test_user_fields_conversion():
    assert UserView(User).fields == [
        StringField("name", required=True, maxlength=100, help_text="user fullname"),
        TextAreaField("bio"),
        HasOne("document", key="document", orderable=False, searchable=False),
    ]


def test_attachment_fields_conversion():
    assert ModelView(Attachment).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        ImageField("image", orderable=False, searchable=False),
        ImageField("images", multiple=True, orderable=False, searchable=False),
        FileField("file", orderable=False, searchable=False),
        FileField("files", multiple=True, orderable=False, searchable=False),
        HasOne("document", key="document", orderable=False, searchable=False),
    ]


def test_document_fields_conversion():
    assert ModelView(Document).fields == [
        IntegerField(
            "int",
            required=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            help_text="This is the primary key",
        ),
        FloatField("float"),
        DecimalField("decimal"),
        BooleanField("bool"),
        DateTimeField("datetime"),
        DateField("date"),
        TimeField("time"),
        EnumField("enum", enum=Status),
        JSONField("json_field"),
        ListField(StringField("tags")),
        ListField(IntegerField("ints")),
        HasOne("user", key="user", orderable=False, searchable=False),
        HasMany("attachments", key="attachment", orderable=False, searchable=False),
    ]


def test_other_fields_conversion():
    assert ModelView(Other).fields == [
        UUIDField("uuid", exclude_from_create=True, exclude_from_edit=True),
        BooleanField("bit"),
        IntegerField("year", min=1901, max=2155),
        StringField("macaddr"),
        IPAddressField("inet", ipv4=True, ipv6=True),
        JSONField("hstore"),
        StringField("cp", exclude_from_edit=True, exclude_from_create=True),
    ]


def test_pk_field():
    assert ModelView(Document).pk_field == IntegerField(
        "int",
        required=True,
        exclude_from_create=True,
        exclude_from_edit=True,
        help_text="This is the primary key",
    )


def test_pk_field_excluded_from_fields():
    class DocumentView(ModelView):
        fields = ["float"]

    assert DocumentView(Document).pk_field == StringField("int")


def test_not_supported_array_columns():
    with pytest.raises(
        NotSupportedColumn, match="Column ARRAY with dimensions != 1 is not supported"
    ):

        class Doc(Base):
            __tablename__ = "doc"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            field: Mapped[list[str] | None] = mapped_column(ARRAY(String, dimensions=2))

        ModelView(Doc)


def test_fields_customisation():
    class CustomDocumentView(ModelView):
        fields = [
            "int",
            Document.bool,
            DecimalField("float", required=True),
            "datetime",
        ]
        exclude_fields_from_create = [Document.datetime]
        exclude_fields_from_detail = ["bool"]
        exclude_fields_from_edit = ["float"]

    assert CustomDocumentView(Document).fields == [
        IntegerField(
            "int",
            required=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            help_text="This is the primary key",
        ),
        BooleanField("bool", exclude_from_detail=True),
        DecimalField("float", required=True, exclude_from_edit=True),
        DateTimeField("datetime", exclude_from_create=True),
    ]


def test_invalid_field_list():
    with pytest.raises(ValueError, match="Can't find column with key 1"):

        class CustomDocumentView(ModelView):
            fields = [1]

        CustomDocumentView(Document)


def test_invalid_exclude_list():
    with pytest.raises(
        ValueError, match="Expected str or InstrumentedAttribute, got int"
    ):

        class CustomDocumentView(ModelView):
            exclude_fields_from_create = [1]

        CustomDocumentView(Document)


def test_invalid_fields_default_sort_list():
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Invalid argument, Expected Tuple[str | InstrumentedAttribute, bool]"
        ),
    ):

        class CustomDocumentView(ModelView):
            fields_default_sort = [Document.int, (Document.datetime, True), (1,)]

        CustomDocumentView(Document)


def test_invalid_model():
    with pytest.raises(
        InvalidModelError, match="Class CustomModel is not a SQLAlchemy model"
    ):

        class CustomModel:
            id = mapped_column(Integer, primary_key=True)

        ModelView(CustomModel)


def test_conversion_when_impl_callable() -> None:
    class CustomString(TypeDecorator):
        impl = String

    class CustomModel(Base):
        __tablename__ = "custom_model"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str | None] = mapped_column(CustomString)

    assert ModelView(CustomModel).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("name"),
    ]


def test_conversion_when_impl_not_callable() -> None:
    class CustomString(TypeDecorator):
        impl = String(length=100)

    class CustomModel2(Base):
        __tablename__ = "custom_model_2"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str | None] = mapped_column(CustomString)

    assert ModelView(CustomModel2).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("name"),
    ]


def test_conversion_for_nested_impl() -> None:
    class CustomStringType(String):
        pass

    class CustomString(TypeDecorator):
        impl = CustomStringType

    class CustomModel3(Base):
        __tablename__ = "custom_model_3"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str | None] = mapped_column(CustomString)

    assert ModelView(CustomModel3).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("name"),
    ]


def test_unsigned_int_conversion() -> None:
    class UnsignedModel(Base):
        __tablename__ = "usigned_model"

        id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True)

    assert ModelView(UnsignedModel).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True, min=0
        ),
    ]


@pytest.mark.asyncio
async def test_handle_exception_converts_sqlalchemy_file_validation_error() -> None:
    view = ModelView(Other)
    exc = FileValidationError("attachment", "invalid file")
    with pytest.raises(FormValidationError) as excinfo:
        await view.handle_exception(MagicMock(), exc)
    assert excinfo.value.errors == {"attachment": "invalid file"}
