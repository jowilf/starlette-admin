from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Union

from starlette.requests import Request
from starlette_admin.exceptions import StarletteAdminException

if TYPE_CHECKING:
    from starlette_admin.views import BaseModelView


class FilterDataType(StrEnum):
    """The kind of value a [BaseFilter][starlette_admin.filters.BaseFilter] operates on. This informs the filter builder UI which input widget to render for the filter's value(s), and indicates when no input is needed for value-less filters.

    Attributes:
        STRING: Plain text input.
        NUMBER: Numeric input.
        DATE: Date picker (`<input type="date">`) (for `DateField`).
        DATETIME: Date and time picker (`<input type="datetime-local">`) (for `DateTimeField`/`ArrowField`).
        TIME: Time picker (`<input type="time">`) (for `TimeField`).
        BOOLEAN: True/false toggle.
        ENUM: Single or multi-select dropdown.
        ARRAY: Free-text tag input (Select2 tags) (for list or array fields such as `TagsField`). The value is parsed as a comma-separated list.
        NONE: No input (for filters that do not require a value, e.g., "is null").
    """

    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    BOOLEAN = "boolean"
    ENUM = "enum"
    ARRAY = "array"
    NONE = "none"


class FilterValidationError(StarletteAdminException):
    """Raised by [BaseFilter.parse_value][starlette_admin.filters.BaseFilter.parse_value]
    when a raw value isn't acceptable for that filter (wrong format, out of
    range, ...). `_parse_list_params` catches this and rejects the request with
    `HTTP 400` before any ORM code runs.
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


@dataclass
class FilterApplyContext:
    """All the arguments an [apply][starlette_admin.filters.BaseFilter.apply] implementation will ever need, bundled to ensure that adding new context (e.g., `locale`, `timezone`) later is a backwards-compatible change. Existing subclasses that ignore the new attributes will continue to function unchanged.

    Attributes:
        query: The ORM-specific query or filter object being constructed (e.g., a SQLAlchemy `Select`, a PyMongo filter `dict`).
        field_name: The name of the field or column to filter on.
        value: The parsed (not raw) primary value, as returned by [parse_value][starlette_admin.filters.BaseFilter.parse_value].
        value2: The parsed secondary value. This is only meaningful when `has_value2` is `True` (e.g., the upper bound of a "between" filter).
        request: The current request, available for user or locale-aware filters.
        view: The view performing the query.
    """

    query: Any
    field_name: str
    value: Any
    value2: Any = None
    request: Request | None = None
    view: Optional["BaseModelView"] = None


class BaseFilter(ABC):
    """Base class for all filters.

    A filter is responsible for three things:

    1. Declaring what kind of value it needs (`data_type`, `has_value2`) so the filter builder UI can render the appropriate input(s).
    2. Parsing the raw (string) value from the URL into the value `apply()` will receive (`parse_value`), raising [FilterValidationError][starlette_admin.filters.FilterValidationError] if it is not acceptable.
    3. Applying itself to a query (`apply`). Given a [FilterApplyContext][starlette_admin.filters.FilterApplyContext] with all necessary context, it returns the modified query. It never reads global state, which ensures its portability across backends. Each ORM contrib package provides concrete subclasses that implement `apply` for its own query representation (see `get_filter_registry()` on the relevant `ModelView`).

    Attributes:
        name: A slug identifying this filter, e.g., `"eq"`, `"contains"`, `"gt"`. Used in the serialized filter JSON and for registry lookups.
        label: A human-readable label shown in the filter builder dropdown.
        data_type: The kind of value this filter operates on. This informs the filter builder UI which input widget to render for the value(s). [FilterDataType.NONE][starlette_admin.types.FilterDataType] means the filter requires no value at all (e.g., "is null" or "is true"), so the UI renders no input, and `_parse_list_params` does not require a `value` in the rule.
        has_value2: `True` for filters that require a second value, e.g., "between".
    """

    name: ClassVar[str]
    label: ClassVar[str]
    data_type: ClassVar[FilterDataType]
    has_value2: ClassVar[bool] = False

    def parse_value(self, raw: str) -> Any:
        """Parse the raw string value from the URL into the value `apply()` will receive as `ctx.value` (or `ctx.value2`).

        Override this method to convert values into richer types, e.g., `Decimal`, `date`, etc. The default implementation passes the raw string through unchanged.
        """
        return raw

    def get_choices(self, request: Request) -> Sequence[tuple[Any, str]] | None:
        """Optional `(value, label)` pairs for this filter's value picker, independent of the field's own choices ([EnumField][starlette_admin.fields.EnumField] is the only field that supplies choices on its own).

        Override this for a filter whose value should come from a dynamic, per-request list rather than a typed-in string, e.g. an "is one of" filter over a relation field where the value is a foreign key but the picker should show a human-readable label. A non-empty result here makes the filter builder render this filter's value input as a dropdown seeded with these pairs, taking precedence over the field's own choices.

        The default implementation returns `None`, leaving the value input as the plain input the filter's `data_type` implies (or the field's own choices, for a field like `EnumField` that supplies them).
        """
        return None

    @abstractmethod
    def apply(self, ctx: FilterApplyContext) -> Any:
        """Apply this filter to a query.

        This method receives a [FilterApplyContext][starlette_admin.filters.FilterApplyContext] with all necessary information and must return the modified query object. Implementations must not mutate `ctx.query` in place for dict-based backends (e.g., PyMongo); instead, they should return a new or updated copy.
        """
        raise NotImplementedError()


@dataclass
class FilterRule:
    """A single `{field, filter, value}` leaf in a filter tree, as deserialized from the `filter` query parameter JSON (see [FilterGroup][starlette_admin.filters.FilterGroup]).

    Attributes:
        field: The name of the field to filter on.
        filter: The slug of the [BaseFilter][starlette_admin.filters.BaseFilter] to apply (e.g., `"contains"`, `"gte"`).
        value: The raw value as received from the client; this is replaced with the parsed value once `_parse_list_params` validates the rule.
        value2: The raw secondary value; only present for filters with `has_value2`.
    """

    field: str
    filter: str
    value: Any = None
    value2: Any = None


@dataclass
class FilterGroup:
    """A node in the filter tree: either a leaf [FilterRule][starlette_admin.filters.FilterRule] or a nested AND/OR group of rules or sub-groups, mirroring the JSON the filter builder serialises into the `filter` query parameter:

    ```json
    {
      "logic": "and",
      "rules": [
        {"field": "name", "filter": "contains", "value": "john"},
        {
          "logic": "or",
          "rules": [
            {"field": "age", "filter": "gte", "value": "18"},
            {"field": "verified", "filter": "is_true"}
          ]
        }
      ]
    }
    ```

    Attributes:
        logic: How `rules` combine: `"and"` or `"or"`.
        rules: The child rules or groups. Empty groups apply no filtering.
    """

    logic: str = "and"
    rules: list[Union["FilterGroup", FilterRule]] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Returns True if this group (recursively) contributes no filtering."""
        return not self.rules
