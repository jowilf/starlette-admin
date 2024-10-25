from enum import Enum
from typing import Optional

from pydantic import EmailStr

from odmantic import EmbeddedModel, Field, Model, Reference


class Address(EmbeddedModel):
    street: str = Field(min_length=3)
    city: str = Field(min_length=3)
    state: Optional[str]
    zipcode: Optional[str]


class Author(Model):
    first_name: str = Field(min_length=3)
    last_name: str = Field(min_length=3)
    email: Optional[EmailStr]
    addresses: list[Address] = Field(default_factory=list)


class BookFormat(str, Enum):
    Hardcover = "hardcover"
    Graphic = "graphic"
    Paperback = "paperback"
    Mass_market_paperback = "mass_market_paperback"


class Book(Model):
    title: str = Field(min_length=5)
    format: BookFormat
    year: int = Field(ge=1900, le=2022)
    awards: list[str] = Field(default_factory=list, min_length=3)
    author: Author = Reference()
