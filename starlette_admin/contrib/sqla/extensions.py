from typing import Any, Dict, Type

from pydantic import ValidationError
from sqlmodel import SQLModel
from starlette.requests import Request
from starlette_admin.contrib.sqla.view import ModelView
from starlette_admin.exceptions import FormValidationError


class SQLModelView(ModelView):
    model: Type[SQLModel]

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        self.model.validate(data)

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            """Convert Pydantic Error to FormValidationError"""
            errors: Dict[str, str] = dict()
            for pydantic_error in exc.errors():
                errors[str(pydantic_error["loc"][-1])] = pydantic_error["msg"]
            raise FormValidationError(errors)
        return super().handle_exception(exc)  # pragma: no cover
