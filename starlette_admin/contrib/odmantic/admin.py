from typing import Any, Dict, Union

from odmantic import AIOEngine, SyncEngine
from starlette.middleware import Middleware
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.odmantic.middleware import EngineMiddleware


class Admin(BaseAdmin):
    def __init__(
        self,
        engine: Union[AIOEngine, SyncEngine],
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(**kwargs)  # type: ignore
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        self.middlewares.insert(0, Middleware(EngineMiddleware, engine=engine))
