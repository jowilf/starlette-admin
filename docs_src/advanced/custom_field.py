from dataclasses import dataclass
from typing import Any, Dict

from requests import Request
from starlette.datastructures import FormData
from starlette_admin import BaseField
from starlette_admin._types import RequestAction


@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
    display_template = "displays/custom.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name)

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return value

    def dict(self) -> Dict[str, Any]:
        return super().dict()
