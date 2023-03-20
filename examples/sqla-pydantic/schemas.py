import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, IPvAnyAddress, validator


class UserSchema(BaseModel):
    id: Optional[int]
    uuid: Optional[uuid.UUID]
    full_name: str = Field(min_length=3)
    website: HttpUrl
    email: EmailStr
    ip_address: IPvAnyAddress

    @validator("full_name")
    def validate_full_name(cls, v: str):
        if " " not in v:
            raise ValueError("Full name must contain a space (ex. John Doe)")
        if v.count(" ") > 1:
            raise ValueError(
                "They must me only one space between the first name and last name (ex. John Doe)"
            )
        return v


class PostSchema(BaseModel):
    id: Optional[int]
    title: str = Field(min_length=3)
    text: str = Field(min_length=5)
    date: datetime
