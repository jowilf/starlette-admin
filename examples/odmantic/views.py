from typing import Any

from starlette.requests import Request
from starlette_admin.contrib.odmantic import ModelView

from .models import Author


class AuthorView(ModelView):
    exclude_fields_from_list = [Author.addresses]

    async def repr(self, obj: Any, request: Request) -> str:
        assert isinstance(obj, Author)
        return obj.first_name + " " + obj.last_name
