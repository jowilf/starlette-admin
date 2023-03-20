from typing import Optional, Sequence, Union

from odmantic import AIOEngine, SyncEngine
from starlette.middleware import Middleware
from starlette_admin.auth import AuthProvider
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.odmantic.middleware import EngineMiddleware
from starlette_admin.i18n import I18nConfig
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.views import CustomView


class Admin(BaseAdmin):
    def __init__(
        self,
        engine: Union[AIOEngine, SyncEngine],
        title: str = _("Admin"),
        base_url: str = "/admin",
        route_name: str = "admin",
        logo_url: Optional[str] = None,
        login_logo_url: Optional[str] = None,
        templates_dir: str = "templates",
        statics_dir: Optional[str] = None,
        index_view: Optional[CustomView] = None,
        auth_provider: Optional[AuthProvider] = None,
        middlewares: Optional[Sequence[Middleware]] = None,
        debug: bool = False,
        i18n_config: Optional[I18nConfig] = None,
    ) -> None:
        super().__init__(
            title=title,
            base_url=base_url,
            route_name=route_name,
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            templates_dir=templates_dir,
            statics_dir=statics_dir,
            index_view=index_view,
            auth_provider=auth_provider,
            middlewares=middlewares,
            debug=debug,
            i18n_config=i18n_config,
        )
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        self.middlewares.insert(0, Middleware(EngineMiddleware, engine=engine))
