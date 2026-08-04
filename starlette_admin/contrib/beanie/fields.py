from dataclasses import dataclass

from starlette_admin.fields import StringField


@dataclass
class BeanieObjectIdField(StringField):
    """StringField subclass used for Beanie's PydanticObjectId fields.

    Kept as a distinct type so the filter registry can register ObjectId-aware
    filters (eq/neq/in/not-in with ObjectId parsing) without colliding with the
    string filters registered for plain StringField.
    """

    copy_to_clipboard: bool | None = True
