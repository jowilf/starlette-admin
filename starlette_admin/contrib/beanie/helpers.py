import datetime
import inspect
import typing as t
from enum import Enum, EnumType
from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Type, Union
from uuid import UUID

import starlette_admin.fields as sa
from beanie import Link, PydanticObjectId
from pydantic import AnyUrl, BaseModel, EmailStr, NameEmail
from pydantic.typing import get_args, get_origin
from pymongo.errors import DuplicateKeyError
from starlette_admin.contrib.beanie._email import Email

# custom datatypes
from starlette_admin.contrib.beanie._file import File, FileGfs, Image
from starlette_admin.contrib.beanie._my_json import MyJson
from starlette_admin.contrib.beanie._password import Password
from starlette_admin.contrib.beanie._slug import Slug
from starlette_admin.contrib.beanie._telephone import Telephone
from starlette_admin.contrib.beanie.exceptions import NotSupportedField
from starlette_admin.contrib.beanie.fields import FileField, ImageField, PasswordField
from starlette_admin.contrib.beanie.pyd import Attr
from starlette_admin.exceptions import FormValidationError
from starlette_admin.helpers import slugify_class_name

bearnie_to_admin_map = {
    PydanticObjectId: sa.StringField,
    str: sa.StringField,
    int: sa.IntegerField,
    bool: sa.BooleanField,
    float: sa.FloatField,
    datetime.datetime: sa.DateTimeField,
    datetime.date: sa.DateField,
    datetime.time: sa.TimeField,
    datetime.timedelta: sa.IntegerField,
    dict: sa.JSONField,
    EmailStr: sa.EmailField,
    NameEmail: sa.StringField,
    AnyUrl: sa.URLField,
    UUID: sa.StringField,
    Enum: sa.EnumField,
    IPv4Address: sa.StringField,
    # custom datatypes
    FileGfs: FileField,
    Password: PasswordField,
}


def convert_beanie_field_to_admin_field(  # noqa: C901
    field: Any, annotation: Type[Any], attr: Attr, field_meta=None, identity=None
) -> sa.BaseField:
    name = field
    admin_field: Optional[sa.BaseField] = None
    _origin = get_origin(annotation)

    if hasattr(annotation, "__mro__"):
        types = inspect.getmro(annotation)

    # si es del tipo 'Indexed'...empieza con Indexed....
    # ejemplo por un 'str': 'Indexed str'
    if hasattr(annotation, "__name__") and annotation.__name__.startswith("Indexed"):
        annotation.__name__[8:]
        # busco si esta definida esa class
        if hasattr(annotation, "__mro__"):
            types = inspect.getmro(annotation)
            for _type in types:
                if issubclass(_type, Enum):
                    admin_field = sa.EnumField(name, enum=_type)
                    return admin_field
                if bearnie_to_admin_map.get(_type) is not None:
                    admin_field = bearnie_to_admin_map.get(_type)(name)  # type: ignore
                    admin_field.required = True
                    return admin_field

    if _origin is Union:
        return convert_beanie_field_to_admin_field(
            field, get_args(annotation)[0], attr, field_meta, identity
        )

    if _origin is not None:
        if _origin in bearnie_to_admin_map:
            admin_field = bearnie_to_admin_map.get(_origin)(name)  # type: ignore

        elif issubclass(_origin, Link):
            identity = None
            if hasattr(attr.model_class, "__name__"):
                identity = slugify_class_name(attr.model_class.__name__)
            # busco la identidad para class con composition
            has_many_or_one = "LIST"  # default
            if field in attr.linked:
                identity = slugify_class_name(attr.linked[field].model_class.__name__)
                has_many_or_one = attr.linked[field].link_type

            # choice has_many or has_one
            if has_many_or_one == "LIST":
                admin_field = sa.HasMany(field, identity=identity)
            else:
                admin_field = sa.HasOne(field, identity=identity)
            return admin_field

        elif _origin in (list, set):
            # es una lista...
            child_field = convert_beanie_field_to_admin_field(
                field, get_args(annotation)[0], attr, field_meta, identity
            )
            if isinstance(child_field, sa.EnumField):
                child_field.multiple = True
                return child_field
            if isinstance(child_field, sa.HasMany):
                return child_field
            admin_field = sa.ListField(child_field)
            return admin_field

    if bearnie_to_admin_map.get(type(field), None) is None:
        raise NotSupportedField(f"Field {field.__class__.__name__} is not supported")

    # los que son de pydantic....y si estan en la tabla de conversion...
    if hasattr(field_meta, "type_") and bearnie_to_admin_map.get(
        (field_meta.type_), None
    ):
        admin_field = bearnie_to_admin_map.get(field_meta.type_)(name)

    if annotation is not None:
        if isinstance(annotation, EnumType):
            admin_field = sa.EnumField(name, enum=annotation)

        elif issubclass(annotation, Email):
            admin_field = sa.EmailField(name=str(name))

        elif issubclass(annotation, MyJson):
            admin_field = sa.JSONField(name=str(name))

        elif issubclass(annotation, Slug):
            admin_field = sa.StringField(name=str(name))

        elif issubclass(annotation, Telephone):
            admin_field = sa.PhoneField(name=str(name))

        elif issubclass(annotation, File):
            admin_field = FileField(name=str(name))

        elif issubclass(annotation, Image):
            admin_field = ImageField(name=str(name))

        elif issubclass(annotation, BaseModel):
            _fields = []

            tmp = annotation.__annotations__.items()
            for key in annotation.__fields__:
                # value es un ModelField de pydantic
                value = annotation.__fields__[key]

                # get the type, i have a problem when field is 'const'
                # example: Street: str = Field(..., max_length=10, description="Stree Name")
                # in this case type is 'ConstrainedStrValue'
                # i: (
                #     'Street',
                #     <class 'str'>,
                # ) (tuple) len=2
                for i in tmp:
                    if i[0] == value.name:
                        new_type = i[1]

                attr = Attr(
                    name=value.name,
                    required=getattr(value, "required", False),
                    description=value.field_info.description,
                    min_length=value.field_info.min_length,
                    max_length=value.field_info.max_length,
                    model_class=annotation,
                )

                exist = bearnie_to_admin_map.get((value.type_), None)
                if exist is None:
                    _fields.append(
                        convert_beanie_field_to_admin_field(
                            value.name, new_type, attr, None, identity
                        )
                    )
                else:
                    _fields.append(
                        convert_beanie_field_to_admin_field(
                            value.name, value.type_, attr, None, identity
                        )
                    )
            admin_field = sa.CollectionField(name, fields=_fields)

        else:
            if annotation is not None:
                admin_field = bearnie_to_admin_map.get(annotation)(name)

    if admin_field is not None:
        admin_field.required = attr.required
        admin_field.help_text = attr.description
        admin_field.minlength = attr.min_length
        admin_field.maxlength = attr.max_length

    return admin_field


def normalize_list(
    arr: t.Optional[t.Sequence[t.Any]], is_default_sort_list: bool = False
) -> t.Optional[t.Sequence[str]]:
    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, str):
            _new_list.append(v)
        elif (
            isinstance(v, tuple) and is_default_sort_list
        ):  # Support for fields_default_sort:
            if len(v) == 2 and isinstance(v[1], bool):
                pass
            else:
                raise ValueError(
                    "Invalid argument, Expected Tuple[str | FieldProxy, bool]"
                )
        else:
            raise ValueError(f"Expected str or FieldProxy, got {type(v).__name__}")
    return _new_list


def pymongo_error_to_form_validation_errors(
    exc: DuplicateKeyError,
) -> FormValidationError:
    """Convert pymongo Error to FormValidationError"""

    assert isinstance(exc, DuplicateKeyError)
    errors: Dict[Union[str, int], Any] = {}
    field_name = list(exc.details["keyValue"].keys())[0]
    errors = {field_name: "duplicate key error"}
    return FormValidationError(errors)
