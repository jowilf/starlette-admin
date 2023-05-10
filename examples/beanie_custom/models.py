from beanie import Document
from pydantic import Field
from starlette_admin.contrib.beanie import ModelView

# custom datatypes
from starlette_admin.contrib.beanie._email import Email
from starlette_admin.contrib.beanie._my_json import MyJson
from starlette_admin.contrib.beanie._slug import Slug
from starlette_admin.contrib.beanie._telephone import Telephone


class Custom(Document):
    email: Email
    metadata: MyJson
    identify: Slug = Field(..., description="slug format automatic convert")
    phone: Telephone


class BeanieView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]
