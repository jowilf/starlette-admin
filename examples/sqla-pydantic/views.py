from typing import Any, Dict

from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.helpers import pydantic_error_to_form_validation_errors

from .schemas import PostSchema, UserSchema


class UserView(ModelView):
    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        try:
            UserSchema(**data)
        except ValidationError as error:
            raise pydantic_error_to_form_validation_errors(error) from error


class PostView(ModelView):
    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        try:
            PostSchema(**data)
        except ValidationError as error:
            raise pydantic_error_to_form_validation_errors(error) from error
