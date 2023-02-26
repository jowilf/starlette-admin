import enum
import uuid

import pytest
import sqlalchemy_file
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
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
from sqlalchemy.dialects.postgresql import BIT, INET, MACADDR, UUID
from sqlalchemy.orm import declarative_base, relationship
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
    JSONField,
    ListField,
    StringField,
    TextAreaField,
    TimeField,
)
from starlette_admin.contrib.sqla.exceptions import (
    InvalidModelError,
    NotSupportedColumn,
)
from starlette_admin.contrib.sqla.fields import FileField, ImageField
from starlette_admin.contrib.sqla.view import ModelView

Base = declarative_base()


class Status(str, enum.Enum):
    NEW = "new"
    ONGOING = "ongoing"
    DONE = "done"


class User(Base):
    __tablename__ = "user"

    name = Column(String(100), primary_key=True, comment="user fullname")
    bio = Column(Text)
    document = relationship("Document", back_populates="user", uselist=False)


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, primary_key=True)
    image = Column(sqlalchemy_file.ImageField)
    images = Column(sqlalchemy_file.ImageField(multiple=True))
    file = Column(sqlalchemy_file.FileField)
    files = Column(sqlalchemy_file.FileField(multiple=True))
    document_id = Column(Integer, ForeignKey("document.int"))
    document = relationship("Document", back_populates="attachments")


class Document(Base):
    __tablename__ = "document"

    int = Column(Integer, primary_key=True, comment="This is the primary key")
    float = Column(Float)
    decimal = Column(Float(asdecimal=True))
    bool = Column(Boolean)
    datetime = Column(DateTime)
    date = Column(Date)
    time = Column(Time)
    enum = Column(Enum(Status))
    json_field = Column(JSON)
    tags = Column(ARRAY(String, dimensions=1))
    ints = Column(ARRAY(Integer, dimensions=1))
    user_name = Column(String(100), ForeignKey("user.name"))
    user = relationship("User", back_populates="document")
    attachments = relationship("Attachment", back_populates="document")


class Other(Base):
    __tablename__ = "other"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    bit = Column(BIT)
    year = Column(YEAR)
    macaddr = Column(MACADDR)
    inet = Column(INET)


class UserView(ModelView):
    form_include_pk = True


def test_user_fields_conversion():
    assert UserView(User).fields == [
        StringField("name", required=True, maxlength=100, help_text="user fullname"),
        TextAreaField("bio"),
        HasOne("document", identity="document", orderable=False, searchable=False),
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
        HasOne("document", identity="document", orderable=False, searchable=False),
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
        HasOne("user", identity="user", orderable=False, searchable=False),
        HasMany(
            "attachments", identity="attachment", orderable=False, searchable=False
        ),
    ]


def test_other_fields_conversion():
    assert ModelView(Other).fields == [
        StringField("uuid", exclude_from_create=True, exclude_from_edit=True),
        BooleanField("bit"),
        IntegerField("year", min=1901, max=2155),
        StringField("macaddr"),
        StringField("inet"),
    ]


def test_not_supported_array_columns():
    with pytest.raises(
        NotSupportedColumn, match="Column ARRAY with dimensions != 1 is not supported"
    ):

        class Doc(Base):
            __tablename__ = "doc"
            id = Column(Integer, primary_key=True)
            field = Column(ARRAY(String, dimensions=2))

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


def test_invalid_model():
    with pytest.raises(
        InvalidModelError, match="Class CustomModel is not a SQLAlchemy model"
    ):

        class CustomModel:
            id = Column(Integer, primary_key=True)

        ModelView(CustomModel)


def test_conversion_when_impl_callable() -> None:
    class CustomString(TypeDecorator):
        impl = String

    class CustomModel(Base):
        __tablename__ = "custom_model"

        id = Column(Integer, primary_key=True)
        name = Column(CustomString)

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

        id = Column(Integer, primary_key=True)
        name = Column(CustomString)

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

        id = Column(Integer, primary_key=True)
        name = Column(CustomString)

    assert ModelView(CustomModel3).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True
        ),
        StringField("name"),
    ]


def test_unsigned_int_conversion() -> None:
    class UnsignedModel(Base):
        __tablename__ = "usigned_model"

        id = Column(INTEGER(unsigned=True), primary_key=True)

    assert ModelView(UnsignedModel).fields == [
        IntegerField(
            "id", required=True, exclude_from_create=True, exclude_from_edit=True, min=0
        ),
    ]
