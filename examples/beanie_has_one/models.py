from typing import List

from beanie import Document, Indexed, Link
from pydantic import BaseModel
from starlette.requests import Request
from starlette_admin.contrib.beanie import ModelView


class BeanieView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]


class Address(BaseModel):
    """example of composition, it is pydantic class"""

    street: str
    number: int


class Door(Document):
    """example to use as has_one"""

    height: int = 2
    width: int = 1

    def __admin_repr__(self, request: Request):
        return f"{self.__class__.__name__}[{self.height},{self.width}]"


class Window(Document):
    """example to use as has_many"""

    x: int = 10
    y: int = 10

    def __admin_repr__(self, request: Request):
        return f"{self.__class__.__name__}[{self.x},{self.y}]"


class House(Document):
    """example has_one, has_many, composition and index"""

    name: Indexed(str, unique=True)  # type: ignore
    windows: List[Link[Window]]
    door: Link[Door]
    address: Address
