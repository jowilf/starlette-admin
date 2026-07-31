from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from starlette.requests import Request
from starlette_admin.exceptions import StarletteAdminException
from starlette_admin.helpers import static_url


class ThemeError(StarletteAdminException):
    """Raised when a theme is misconfigured."""


class IconSet:
    """A named icon library: semantic names -> concrete markup classes.

    Icons are referenced in templates by a semantic key (`icon('list.new')`),
    never by a library class. An `IconSet` maps those keys to a concrete
    library so swapping the library is swapping the `IconSet`, with no
    template changes.

    `icons` maps this set's semantic names to the library's classes.
    `css_links` supplies the library's stylesheet, injected by
    `base.html`'s `icon_css` block.
    """

    icons: ClassVar[dict[str, str]] = {}

    def css_links(self, request: Request) -> list[str]:
        return []


class CoreIcons(IconSet):
    """The FontAwesome baseline for every semantic name core draws.

    A theme's `IconSet` overrides the names it maps; any name it leaves
    unmapped falls through to this default.
    """

    icons: ClassVar[dict[str, str]] = {
        # List page toolbar
        "list.new": "fa-solid fa-plus",
        "list.search": "fa-solid fa-magnifying-glass",
        "list.filter": "fa-solid fa-filter",
        "list.columns": "fa-solid fa-table-columns",
        "list.import": "fa-solid fa-file-import",
        "list.export": "fa-solid fa-file-export",
        "list.row_actions": "fa-solid fa-ellipsis-vertical",
        # Default row/detail actions
        "default_actions.view": "fa-solid fa-eye",
        "default_actions.edit": "fa-solid fa-edit",
        "default_actions.delete": "fa-solid fa-trash",
        # Pagination
        "pagination.prev": "fa-solid fa-chevron-left",
        "pagination.next": "fa-solid fa-chevron-right",
        # Column sorting
        "sort.none": "fa-solid fa-sort",
        "sort.asc": "fa-solid fa-sort-up",
        "sort.desc": "fa-solid fa-sort-down",
        # Auth / global nav
        "auth.logout": "fa fa-sign-out",
        "nav.language": "fa-solid fa-language",
        "nav.world": "fa-solid fa-earth-americas",
        "nav.user": "fa-solid fa-user",
        # Flash messages
        "flash.success": "fa-solid fa-circle-check",
        "flash.warning": "fa-solid fa-triangle-exclamation",
        "flash.error": "fa-solid fa-circle-exclamation",
        "flash.info": "fa-solid fa-circle-info",
        # Generic actions
        "action.close": "fa fa-close",
        "action.copy": "fa-solid fa-copy",
        "action.copy_done": "fa-solid fa-check",
        # Fields
        "field.boolean_true": "fa-solid fa-check-circle",
        "field.boolean_false": "fa-solid fa-times-circle",
        "list_field.add": "fa fa-add",
        # Inline forms
        "inline.add_row": "fa fa-plus",
        "inline.delete_row": "fa fa-trash",
        # Inline cell editing (list page popover)
        "inline_edit.save": "fa-solid fa-check",
        "inline_edit.cancel": "fa-solid fa-xmark",
        # Collapsible panels (inline formsets, panel widget)
        "panel.collapse_toggle": "fa-solid fa-chevron-down",
        # Filter bar / builder
        "filter.remove_chip": "fa-solid fa-xmark",
        "filter_builder.add_condition": "fa-solid fa-plus",
        "filter_builder.add_group": "fa-solid fa-layer-group",
        "filter_builder.remove": "fa-solid fa-trash",
        # Import modal
        "import.preview": "fa-solid fa-eye",
        # Create/edit form footer
        "form.cancel": "fa-solid fa-xmark",
        "form.save": "fa-solid fa-arrow-right",
    }

    def css_links(self, request: Request) -> list[str]:
        return [static_url(request, "css/vendor/fontawesome.min.css", v="7.2.0")]


class ClassMap:
    """Semantic component roles -> CSS class strings.

    Templates render class attributes through `cls('role.name')`. A theme
    maps the roles it restyles; unmapped roles fall through to
    `CoreClasses`, so a partial map is always safe.
    """

    classes: ClassVar[dict[str, str]] = {}


class CoreClasses(ClassMap):
    """Tabler defaults for every role core templates render.

    Three kinds of roles: buttons (one role per site, the value is the
    button's whole class attribute), Tabler-specific component classes a
    Bootstrap based theme must swap, and classes core JS applies at
    runtime. Bootstrap substrate chrome stays literal in templates and has
    no role here.
    """

    classes: ClassVar[dict[str, str]] = {
        # Create/edit form footer buttons
        "form.cancel_button": "btn btn-danger btn-animate-icon btn-animate-icon-rotate",
        "form.save_button": "btn btn-primary btn-animate-icon",
        "form.save_add_button": "btn",
        "form.save_continue_button": "btn",
        # List page toolbar buttons
        "list.search_button": "btn",
        "list.create_button": "btn btn-primary btn-block ms-2",
        "list.import_button": "btn",
        "list.columns_toggle": "btn dropdown-toggle",
        "list.columns_apply_button": "btn btn-sm btn-primary",
        "list.columns_reset_button": "btn btn-sm btn-link",
        "list.goto_page_button": "btn",
        # Filter bar / builder buttons
        "filter.toggle_button": "btn dropdown-toggle",
        "filter.add_condition_button": "btn btn-sm",
        "filter.add_group_button": "btn btn-sm",
        "filter.remove_button": "btn btn-sm btn-action",
        "filter.reset_button": "btn btn-sm text-primary btn-link",
        "filter.apply_button": "btn btn-sm btn-primary",
        # Action buttons and modal
        "action.button": "btn",
        "action.dropdown_toggle": "btn dropdown-toggle",
        "action.dropdown_item": "dropdown-item",
        "action.row_item": "btn",
        "action.row_item_edit": "btn btn-primary",
        "action.row_item_delete": "btn btn-danger",
        "action.row_dropdown_toggle": "btn dropdown-toggle",
        "action.row_kebab_toggle": "btn btn-icon btn-ghost-primary btn-sm",
        "action.modal_confirm_button": "btn btn-primary",
        "action.modal_confirm_button_delete": "btn btn-danger",
        "action.modal_cancel_button": "btn btn-link link-secondary me-auto",
        # Row delete modal buttons
        "delete.confirm_button": "btn btn-danger w-100",
        "delete.cancel_button": "btn w-100",
        # Import modal footer buttons
        "import.back_button": "btn btn-link",
        "import.submit_button": "btn btn-primary",
        "import.submit_button_done": "btn btn-secondary",
        # Inline formset buttons
        "inline.add_row_button": "btn btn-outline-primary btn-sm mt-2",
        "inline.delete_button": "btn btn-danger btn-sm",
        # Inline cell editing buttons (list page popover)
        "inline_edit.save_button": "btn btn-primary btn-icon",
        "inline_edit.cancel_button": "btn btn-icon",
        # Field value buttons
        "field.copy_button": "btn btn-action btn-sm",
        # Tabler-specific component classes
        "list.table": "table table-vcenter card-table",
        "detail.table": "table table-bordered table-vcenter table-mobile-md",
        "filter.chip": "badge bg-primary-lt text-decoration-none d-inline-flex align-items-center gap-1",
        "modal.base": "modal modal-blur fade",
        "steps.container": "steps steps-counter mb-4",
        "steps.item": "step-item",
        # Classes core JS applies at runtime
        "alert.success": "alert-success",
        "alert.warning": "alert-warning",
        "alert.error": "alert-danger",
        "alert.info": "alert-info",
        "import.status_badge": "badge",
        "import.status_new": "text-bg-success",
        "import.status_update": "text-bg-primary",
        "import.status_error": "text-bg-danger",
    }


TablerMode = Literal["light", "dark"]

TablerBase = Literal["slate", "gray", "zinc", "neutral", "stone", "pink"]

TablerPrimary = Literal[
    "blue",
    "azure",
    "indigo",
    "purple",
    "pink",
    "red",
    "orange",
    "yellow",
    "lime",
    "green",
    "teal",
    "cyan",
    "inverted",
]

TablerRadius = float  # Valid values: 0, 0.5, 1, 1.5, 2.


@dataclass
class TablerSettings:
    """Controls the Tabler theme attributes rendered on the `<html>` element.

    Example:
        ```python
        TablerSettings(
            base="stone",
            primary="purple",
            radius=2,
            mode="light",
        )
        ```

        renders as:

        ```html
        <html data-bs-theme-base="stone"
              data-bs-theme-primary="purple"
              data-bs-theme-radius="2"
              data-bs-theme="light">
        ```

    Parameters:
        base: Neutral color palette used for backgrounds, borders, and text.
            `None` omits the `data-bs-theme-base` attribute, falling back to
            the CSS default.
        primary: Accent color used for links, buttons, and other interactive
            elements. `None` omits the `data-bs-theme-primary` attribute.
        radius: Corner rounding scale applied to buttons, cards, and inputs.
            `None` omits the `data-bs-theme-radius` attribute.
        mode: Color scheme rendered on the page, `"light"` or `"dark"`.
    """

    base: TablerBase | None = "stone"
    primary: TablerPrimary | None = "blue"
    radius: TablerRadius | None = 1
    mode: TablerMode = "light"

    def html_attrs(self) -> dict[str, str]:
        """Build the `data-bs-theme-*` attribute dict for the `<html>` tag.

        Omits an attribute entirely when the corresponding field is `None`.
        """
        attrs: dict[str, str] = {"data-bs-theme": self.mode}
        if self.base is not None:
            attrs["data-bs-theme-base"] = self.base
        if self.primary is not None:
            attrs["data-bs-theme-primary"] = self.primary
        if self.radius is not None:
            attrs["data-bs-theme-radius"] = str(self.radius)
        return attrs


class BaseTheme:
    """A theme owns the admin layout and styling.

    A theme is not a plugin: it ships through `Admin(theme=...)`, not
    `plugins=`, and its surface is intentionally small. It may replace any
    template at its bare path (`base.html`, `layout.html`, `list.html`,
    `index.html`, ...) so every page inherits its chrome through Jinja's
    bare-name resolution, and it sits above plugins in the loader chain so
    it can restyle their templates too. Exactly one theme is active at a
    time.

    A theme's surface is: the `templates/`, `static/`, and `translations/`
    folders under its `package`, an `IconSet` swapping the icon library the
    whole admin renders through, and template variables exposed to every page.
    """

    #: Identifier used for logging. Unlike a plugin name, it does not
    #: namespace templates or static files: a theme owns the global templates.
    name: ClassVar[str]

    #: Import package holding the theme's `templates/`, `static/`, and
    #: `translations/` folders. Defaults to the theme class's top-level
    #: package.
    package: ClassVar[str | None] = None

    #: Gettext domain under which the theme's MO catalogs are compiled
    #: (``<package>/translations/<locale>/LC_MESSAGES/<domain>.mo``). Matches
    #: the core ``admin`` domain so theme messages merge into the same
    #: catalog.
    translation_domain: ClassVar[str] = "admin"

    @abstractmethod
    def get_icon_set(self) -> IconSet:
        """Icon library the whole admin renders through.

        The sole source of the admin's icon vocabulary: every semantic name
        a template resolves through `icon()` must be mapped here.
        """

    def get_class_map(self) -> ClassMap:
        """Visual classes for the roles this theme restyles. Unmapped roles
        fall through to `CoreClasses`."""
        return ClassMap()

    def html_attrs(self, request: Request) -> dict[str, str]:
        """Attributes rendered on the `<html>` element of every page."""
        return {}  # pragma: no cover

    def template_globals(self) -> dict[str, Any]:
        """Jinja globals exposed to every template, unprefixed."""
        return {}

    def resolved_package(self) -> str:
        """The import package holding this theme's `templates/`/`static/`
        folders: `package` if set, else the theme class's top-level import
        package."""
        if self.package is not None:
            return self.package
        return type(self).__module__.split(".", 1)[0]


class DefaultTheme(BaseTheme):
    """starlette-admin's default theme: Tabler CSS framework, FontAwesome icons.

    Its `templates/` and `static/` are starlette-admin's own, so it needs no
    extra assets beyond the `TablerSettings` palette it renders as
    `data-bs-theme-*` attributes.
    """

    name = "core"
    package = "starlette_admin"

    def __init__(self, settings: TablerSettings | None = None) -> None:
        self.settings = settings or TablerSettings()

    def get_icon_set(self) -> IconSet:
        return CoreIcons()

    def html_attrs(self, request: Request) -> dict[str, str]:
        return self.settings.html_attrs()
