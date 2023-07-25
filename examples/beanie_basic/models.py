from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from starlette_admin.contrib.beanie import ModelView
from starlette_admin.contrib.beanie._file import Image
from starlette_admin.contrib.beanie._password import Password


class Country(str, Enum):
    Argentina = "Argentina"
    USA = "USA"


class Address(BaseModel):
    Street: str = Field(..., max_length=10, description="Street Name")
    Number: int
    Floor: int
    Apartment: Optional[str]
    PostalCode: Optional[str]
    Country: Country


class Author(Document):
    first_name: str = Field(..., max_length=10, description="Your first name")
    last_name: str
    age: int
    weight: float
    active: bool
    avatar: Optional[Image]
    address: Address

    class Settings:
        use_revision = False


class User(Document):
    email: EmailStr
    password: Password


class BeanieView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]
