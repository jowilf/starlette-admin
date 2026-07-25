"""JSON importer: parses a UTF-8 encoded ``.json`` array of objects."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from starlette_admin.importers.base import BaseImporter, ImportContext
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


class JsonImporter(BaseImporter):
    extension = "json"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any]]:
        _log.debug("JSON parse starting: %d bytes", len(ctx.content))
        data = json.loads(ctx.content.decode("utf-8"))
        if not isinstance(data, list):
            _log.warning(
                "JSON import rejected: root value is %s, expected array",
                type(data).__name__,
            )
            raise ValueError("JSON import expects a top-level array of objects.")
        _log.debug("JSON parse: %d item(s) in array", len(data))
        for item in data:
            yield dict(item)
