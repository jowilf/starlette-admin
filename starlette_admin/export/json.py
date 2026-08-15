"""JSON exporter: produces a UTF-8 encoded ``.json`` array."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette_admin.export.base import BaseExporter
from starlette_admin.helpers import json_dumps

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField


class JsonExporter(BaseExporter):
    content_type = "application/json"
    extension = "json"

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        output = [
            {(f.label or f.name): row.get(f.name, "") for f in fields} for row in rows
        ]
        return json_dumps(output, ensure_ascii=False).encode("utf-8")
