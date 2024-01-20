import enum
import re
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
from sqlalchemy.orm import column_property, declarative_base, relationship
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
    cp = column_property(macaddr + ";" + inet)


class UserView(ModelView):
    form_include_pk = True


def test_view_meta_info():
    model_view = ModelView(
        Other, identity="other-id", label="Other label", name="Other name"
    )
    assert model_view.identity == "other-id"
    assert model_view.label == "Other label"
    assert model_view.name == "Other name"


def test_view_meta_info_with_class_level_config():
    class CustomView(ModelView):
        identity = "custom-id"
        label = "Custom label"
        name = "Custom name"

    model_view = CustomView(Other)
    assert model_view.identity == "custom-id"
    assert model_view.label == "Custom label"
    assert model_view.name == "Custom name"


def test_view_meta_info_with_overridden_class_level_config():
    class CustomView(ModelView):
        identity = "custom-id"
        label = "Custom label"
        name = "Custom name"

    model_view = CustomView(
        Other, identity="other-id", label="Other label", name="Other name"
    )
    assert model_view.identity == "other-id"
    assert model_view.label == "Other label"
    assert model_view.name == "Other name"


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
