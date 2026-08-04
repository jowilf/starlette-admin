import inspect
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField
    from starlette_admin.filters.base import BaseFilter


def filters(
    *field_types: type["BaseField"],
) -> Callable[
    [Callable[..., Sequence[type["BaseFilter"]]]],
    Callable[..., Sequence[type["BaseFilter"]]],
]:
    """Class method decorator that registers the decorated method as the
    source of filters for one or more `BaseField` subclasses.

    Apply it to a method on a `FilterRegistry` subclass. `FilterRegistry.__init__`
    scans the instance for methods carrying this marker and indexes each by
    the `field_types` passed here, so `filters_for` can look the method up
    later by field type.
    """

    def wrap(
        method: Callable[..., Sequence[type["BaseFilter"]]],
    ) -> Callable[..., Sequence[type["BaseFilter"]]]:
        method._filters_for = frozenset(field_types)  # ty: ignore[unresolved-attribute]
        return method

    return wrap


class FilterRegistry:
    """Maps `BaseField` subclasses to the `BaseFilter` classes available for
    them.

    A subclass declares one `@filters(FieldType, ...)`-decorated method per
    field type it supports. `filters_for` resolves a given field to its
    filters by walking `type(field).__mro__` and returning the first
    registered match, so a field type that has no entry of its own falls back
    to whatever its nearest registered ancestor declares.

    Each ORM contrib package owns one instance of this registry, populated
    with its own concrete `BaseFilter` subclasses, and hands it back from
    `ModelView.get_filter_registry()`. To change the filters offered for a
    field type, subclass the contrib registry and override just that one
    method rather than rebuilding the registry from scratch.
    """

    def __init__(
        self,
        filters: dict[type["BaseField"], Sequence[type["BaseFilter"]]] | None = None,
    ) -> None:
        # Collect every @filters-decorated method on this instance (including
        # inherited ones) and index it by the field types it was declared for.
        self._registry: dict[
            type[BaseField], Callable[[BaseField], list[type[BaseFilter]]]
        ] = {}
        for _name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "_filters_for"):
                for field_type in method._filters_for:
                    self._registry[field_type] = method

        # Plugin-registered filters (see `register_filters` in a backend's
        # filters module) sit between the class's own @filters methods and
        # the caller-supplied dict, so precedence is user > plugin > core.
        for field_type, filter_classes in self._external_filters().items():
            self.register(field_type, *filter_classes)

        # Imperative registrations passed to __init__ take priority over the
        # methods above, since they run after and register() replaces entries.
        for field_type, filter_classes in (filters or {}).items():
            self.register(field_type, *filter_classes)

    def _external_filters(
        self,
    ) -> dict[type["BaseField"], Sequence[type["BaseFilter"]]]:
        """Override in a backend's registry to merge in filters registered
        by plugins for that backend. Empty by default."""
        return {}

    def register(
        self, field_type: type["BaseField"], *filter_classes: type["BaseFilter"]
    ) -> None:
        """Set `filter_classes` as the filters available for `field_type`.

        This is the imperative counterpart to the declarative `@filters`
        methods, useful for registering filters at runtime rather than on a
        subclass. Calling it again for the same `field_type` replaces the
        previous registration outright; it does not merge with it.
        """
        self._registry[field_type] = lambda field: list(filter_classes)

    def filters_for(self, field: "BaseField") -> list[type["BaseFilter"]]:
        """Return the filter classes available for `field`.

        A field's own `filters` attribute, if set, takes precedence over
        anything registered here. Otherwise this walks `type(field).__mro__`
        from most to least specific and returns the filters registered for
        the first matching type. For example, `EmailField` (a `StringField`
        subclass) inherits `StringField`'s filters unless `EmailField` has its
        own registration. Returns an empty list if no type in the MRO is
        registered.
        """
        if field.filters is not None:
            return list(field.filters)
        for cls in type(field).__mro__:
            if cls in self._registry:
                return list(self._registry[cast(type["BaseField"], cls)](field))
        return []

    def get_filter(self, field: "BaseField", name: str) -> type["BaseFilter"] | None:
        """Return the filter class among `filters_for(field)` whose
        `BaseFilter.name` slug matches `name`, or `None` if none match.

        Two callers rely on this: request parsing uses it to validate a
        filter slug coming from the URL, and each backend uses it to resolve
        an already-parsed [FilterRule][starlette_admin.filters.FilterRule]
        back into the concrete filter class whose `apply()` builds the query
        fragment.
        """
        for cls in self.filters_for(field):
            if cls.name == name:
                return cls
        return None
