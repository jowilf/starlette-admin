from typing import Optional

from beanie import Document
from starlette_admin.contrib.beanie import ModelView
from starlette_admin.contrib.beanie._file import Image


class Author(Document):
    name: str
    avatar: Optional[Image]

    class Settings:
        use_revision = False


class BeanieView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]
