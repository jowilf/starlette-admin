"""Plugin API: `BasePlugin` and the namespace rules enforced when a plugin
is registered through `Admin(plugins=[...])`.

Registration itself (`BaseAdmin._register_plugins`) lives in `base.py`,
since it needs direct access to the admin instance being built. Themes are
a separate concept: see `starlette_admin.theme`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette_admin.exceptions import StarletteAdminException

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

    from starlette_admin.base import BaseAdmin
    from starlette_admin.views import BaseView


class PluginError(StarletteAdminException):
    """Raised when a plugin is misconfigured: a missing/duplicate/reserved
    `name`, or a `templates/`/`static/` folder with files outside its
    `plugins/<name>/` namespace."""


#: These back the core template prefixes (`@core` and its `@starlette-admin`
#: alias), so a plugin cannot shadow them.
RESERVED_PLUGIN_NAMES = frozenset({"core", "starlette-admin"})


class BasePlugin:
    """Base class for starlette-admin plugins.

    Subclasses override only the hooks they need. All hooks are called
    exactly once, during `Admin` construction, in the order documented in
    `BaseAdmin._register_plugins`.
    """

    #: Unique kebab-case identifier. Doubles as the templates/static
    #: namespace: everything the plugin ships lives under "plugins/<name>/".
    name: ClassVar[str]

    #: Import package holding the plugin's templates/, static/, and
    #: translations/ folders. Defaults to the plugin class's top-level
    #: package, so a plugin laid out conventionally never sets it.
    package: ClassVar[str | None] = None

    #: Gettext domain under which the plugin's MO catalogs are compiled
    #: (``<package>/translations/<locale>/LC_MESSAGES/<domain>.mo``). Matches
    #: the core ``admin`` domain so plugin messages merge into the same
    #: catalog.
    translation_domain: ClassVar[str] = "admin"

    # -- Declarative hooks (return data, admin wires it) ---------------------
    #
    # Templates, static files, and translation catalogs are NOT hooks: they
    # are discovered by convention from `package` (see `validate_plugin_namespace`
    # and `BaseAdmin._register_plugins`). Hooks remain only for things a
    # folder cannot express.

    def css_links(self, request: Request) -> Sequence[str]:
        """Stylesheets injected into every admin page (layout.html)."""
        return []

    def js_links(self, request: Request) -> Sequence[str]:
        """Scripts injected into every admin page, after core scripts."""
        return []

    def middlewares(self) -> Sequence[Middleware]:
        return []

    def routes(self) -> Sequence[Route | Mount]:
        """Mounted under /plugins/<name>/ inside the admin app."""
        return []

    def views(self) -> Sequence[BaseView]:
        """Views registered through admin.add_view()."""
        return []

    def template_globals(self) -> dict[str, Any]:
        """Jinja globals, auto-prefixed '<name>_' to avoid collisions."""
        return {}

    def template_filters(self) -> dict[str, Callable]:
        """Jinja filters, auto-prefixed '<name>_'."""
        return {}

    # -- Imperative hook -------------------------------------------------

    def setup(self, admin: BaseAdmin) -> None:
        """Everything that is a call into an existing registry: storage
        backends, converters, filters, import/export formats, event
        subscribers. Runs after the declarative hooks are applied."""

    # -- Lifecycle -------------------------------------------------------

    def on_mount(self, admin: BaseAdmin) -> None:
        """Called at the end of mount_to(). The built Starlette
        sub-application is reachable as `admin.app`."""

    # -- Internal ----------------------------------------------------------

    def resolved_package(self) -> str:
        """The import package holding this plugin's templates/static/
        translations folders: `package` if set, else the plugin class's
        top-level import package."""
        if self.package is not None:
            return self.package
        return type(self).__module__.split(".", 1)[0]


def _iter_relative_files(root: Traversable, prefix: str = "") -> list[str]:
    """Posix-style relative paths of every file under `root`."""
    paths: list[str] = []
    for entry in root.iterdir():
        rel = f"{prefix}{entry.name}"
        if entry.is_dir():
            paths.extend(_iter_relative_files(entry, f"{rel}/"))
        else:
            paths.append(rel)
    return paths


def validate_plugin_namespace(
    folder: Traversable, plugin_name: str, folder_kind: str
) -> None:
    """Raise `PluginError` if `folder` (a plugin's `templates/` or `static/`
    directory) contains anything outside `plugins/<plugin_name>/`.

    This namespace is what makes the shared template loader and `/static`
    mount collision-free: a plugin can never ship a bare `layout.html` that
    shadows core, and two plugins can never collide with each other.
    """
    required_prefix = f"plugins/{plugin_name}/"
    for rel_path in _iter_relative_files(folder):
        if not rel_path.startswith(required_prefix):
            raise PluginError(
                f"Plugin {plugin_name!r}: {folder_kind}/{rel_path} must live "
                f"under {folder_kind}/{required_prefix}"
            )
