"""Unit tests for starlette_admin.plugins: BasePlugin registration wiring,
namespace enforcement, and template/static override precedence."""

import sys
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin
from starlette_admin.plugins import BasePlugin, PluginError
from starlette_admin.views import Link

_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "data" / "plugin_fixtures"
if str(_FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR))


@pytest.fixture(autouse=True, scope="session")
def _compile_i18n_plugin_mo():
    """Compile the fixture plugin's admin.po into admin.mo so that
    register_translation_catalog can load it at test time."""
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po

    po = (
        _FIXTURES_DIR
        / "sa_i18n_plugin"
        / "translations"
        / "en"
        / "LC_MESSAGES"
        / "admin.po"
    )
    mo = po.with_suffix(".mo")
    with open(po, "rb") as f:
        catalog = read_po(f)
    with open(mo, "wb") as f:
        write_mo(f, catalog)
    yield
    mo.unlink(missing_ok=True)


class _NoopMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)


async def _plugin_endpoint(request: Request) -> PlainTextResponse:
    return PlainTextResponse("hello from plugin route")


class _TestPlugin(BasePlugin):
    name = "testplugin"
    package = "sa_test_plugin"

    def __init__(self):
        self.setup_called_with = None

    def css_links(self, request):
        return ["/static/plugins/testplugin/css/x.css"]

    def js_links(self, request):
        return ["/static/plugins/testplugin/js/hello.js"]

    def middlewares(self):
        return [Middleware(_NoopMiddleware)]

    def routes(self):
        return [Route("/hello", _plugin_endpoint, name="hello")]

    def views(self):
        return [Link(menu_label="Plugin Link", url="/somewhere")]

    def template_globals(self):
        return {"config": {"zoom": 5}}

    def template_filters(self):
        return {"shout": lambda s: s.upper()}

    def setup(self, admin):
        self.setup_called_with = admin


class _BadNamespacePlugin(BasePlugin):
    name = "badplugin"
    package = "sa_bad_plugin"


def test_plugin_registers_and_wires_everything():
    plugin = _TestPlugin()
    admin = BaseAdmin(secret_key="test", plugins=[plugin])

    assert admin.plugins == {"testplugin": plugin}
    assert plugin.setup_called_with is admin

    # css/js links exposed as template globals
    assert admin.templates.env.globals["plugin_css_links"](None) == [
        "/static/plugins/testplugin/css/x.css"
    ]
    assert admin.templates.env.globals["plugin_js_links"](None) == [
        "/static/plugins/testplugin/js/hello.js"
    ]

    # template globals/filters auto-prefixed with "<name>_"
    assert admin.templates.env.globals["testplugin_config"] == {"zoom": 5}
    assert admin.templates.env.filters["testplugin_shout"]("hi") == "HI"

    # static package registered under the shared /static mount
    assert ("sa_test_plugin", "static") in admin._plugin_static_packages

    # menu-visible view registered through add_view()
    assert any(
        isinstance(v, Link) and v.menu_label == "Plugin Link" for v in admin._views
    )

    # middleware contributed
    assert any(getattr(m, "cls", None) is _NoopMiddleware for m in admin.middlewares)


def test_plugin_template_resolves_by_plain_and_prefixed_path():
    admin = BaseAdmin(secret_key="test", plugins=[_TestPlugin()])

    plain = admin.templates.env.get_template("plugins/testplugin/hello.html")
    prefixed = admin.templates.env.get_template("@testplugin/hello.html")

    assert plain.render().strip() == "hello from testplugin"
    assert prefixed.render().strip() == "hello from testplugin"


def test_user_templates_dir_overrides_plugin_template(tmp_path):
    override_dir = tmp_path / "plugins" / "testplugin"
    override_dir.mkdir(parents=True)
    (override_dir / "hello.html").write_text("overridden by user")

    admin = BaseAdmin(
        secret_key="test",
        templates_dir=str(tmp_path),
        plugins=[_TestPlugin()],
    )

    plain = admin.templates.env.get_template("plugins/testplugin/hello.html")
    prefixed = admin.templates.env.get_template("@testplugin/hello.html")

    assert plain.render().strip() == "overridden by user"
    # The @<name> prefix bypasses the user's templates_dir, so a user
    # override can safely `{% extends "@testplugin/hello.html" %}`.
    assert prefixed.render().strip() == "hello from testplugin"


def test_plugin_route_mounted_and_named():
    admin = BaseAdmin(secret_key="test", plugins=[_TestPlugin()])
    app = Starlette()
    admin.mount_to(app)
    client = TestClient(app)

    resp = client.get("/admin/plugins/testplugin/hello")
    assert resp.status_code == 200
    assert resp.text == "hello from plugin route"

    # Nested route names are dot-prefixed by each enclosing Mount's own
    # `name`, so from outside the admin mount the full path is
    # "<admin.route_name>:plugin:<plugin.name>:<route.name>".
    url = app.url_path_for(f"{admin.route_name}:plugin:testplugin:hello")
    assert url == "/admin/plugins/testplugin/hello"


def test_on_mount_dispatched_with_app_reachable():
    calls = []

    class _MountPlugin(BasePlugin):
        name = "mountplugin"
        package = "sa_empty_plugin"

        def on_mount(self, admin):
            calls.append(admin.app)

    admin = BaseAdmin(secret_key="test", plugins=[_MountPlugin()])
    app = Starlette()
    admin.mount_to(app)

    assert calls == [admin.app]


def test_reserved_plugin_name_rejected():
    class _CorePlugin(BasePlugin):
        name = "core"

    with pytest.raises(PluginError, match="reserved"):
        BaseAdmin(secret_key="test", plugins=[_CorePlugin()])


def test_duplicate_plugin_name_rejected():
    with pytest.raises(PluginError, match="Duplicate"):
        BaseAdmin(secret_key="test", plugins=[_TestPlugin(), _TestPlugin()])


def test_missing_plugin_name_rejected():
    class _NoNamePlugin(BasePlugin):
        pass

    with pytest.raises(PluginError, match="must define a 'name'"):
        BaseAdmin(secret_key="test", plugins=[_NoNamePlugin()])


def test_plugin_namespace_violation_rejected():
    with pytest.raises(PluginError, match="must live under"):
        BaseAdmin(secret_key="test", plugins=[_BadNamespacePlugin()])


def test_no_plugins_leaves_admin_unaffected():
    admin = BaseAdmin(secret_key="test")
    assert admin.plugins == {}
    assert admin.templates.env.globals["plugin_css_links"](None) == []
    assert admin.templates.env.globals["plugin_js_links"](None) == []


def test_default_hooks_are_empty():
    """A plugin that overrides nothing still resolves its package from its
    own module, and contributes no css/js links, by default."""
    from sa_empty_plugin import MinimalPlugin

    plugin = MinimalPlugin()
    admin = BaseAdmin(secret_key="test", plugins=[plugin])

    assert plugin.resolved_package() == "sa_empty_plugin"
    assert admin.templates.env.globals["plugin_css_links"](None) == []
    assert admin.templates.env.globals["plugin_js_links"](None) == []


class _I18nPlugin(BasePlugin):
    """Plugin that ships a translations/ folder with a single en catalog."""

    name = "i18nplugin"
    package = "sa_i18n_plugin"


def test_plugin_with_translations_merges_catalog():
    """A plugin that ships translations/ has its MO catalog merged into the
    active i18n catalogs during Admin construction."""
    from starlette_admin.i18n import gettext

    admin = BaseAdmin(secret_key="test", plugins=[_I18nPlugin()])

    assert ("sa_i18n_plugin", "admin") in admin._plugin_translation_catalogs
    assert gettext("test_plugin_greeting") == "Hello from test plugin"


def test_register_catalog_noop_without_translations_dir():
    """register_translation_catalog silently returns when the package has no
    translations/ folder."""
    from starlette_admin.i18n import register_translation_catalog, translations

    snapshot = dict(translations.items())
    register_translation_catalog("os")
    assert {loc: type(t).__name__ for loc, t in translations.items()} == {
        loc: type(t).__name__ for loc, t in snapshot.items()
    }


def test_register_catalog_replaces_null_translations():
    """When the active catalog for a locale is a NullTranslations (not a full
    Translations), register_translation_catalog replaces it entirely instead
    of merging."""
    from babel.support import NullTranslations
    from babel.support import Translations as BabelTranslations
    from starlette_admin.i18n import register_translation_catalog, translations

    saved = translations["en"]
    translations["en"] = NullTranslations()
    try:
        register_translation_catalog("sa_i18n_plugin")
        result = translations["en"]
        assert isinstance(result, BabelTranslations)
        assert result.gettext("test_plugin_greeting") == "Hello from test plugin"
    finally:
        translations["en"] = saved
