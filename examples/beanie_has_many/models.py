from typing import List

from beanie import Document, Link
from starlette.requests import Request
from starlette_admin.contrib.beanie import ModelView


class BeanieView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]


class Window(Document):
    x: int = 10
    y: int = 10

    def __admin_repr__(self, request: Request):
        return f"[{self.x},{self.y}]"


class House(Document):
    name: str
    windows: List[Link[Window]]
