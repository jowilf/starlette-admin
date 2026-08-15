from starlette_admin.plugins import BasePlugin


class MinimalPlugin(BasePlugin):
    """A plugin that overrides no hooks, used to test BasePlugin's defaults:
    `resolved_package()` falling back to this module, and empty css/js links.
    """

    name = "minimalplugin"
