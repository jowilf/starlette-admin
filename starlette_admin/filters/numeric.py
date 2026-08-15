from typing import Any

from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterValidationError,
)
from starlette_admin.i18n import lazy_gettext as _


def _parse_number(raw: Any) -> int | float:
    """Parse a raw URL value into `int` (preferred) or `float`.

    Numeric `BaseField`s span `int`, `float` and `Decimal`; parsing into a
    plain Python number here and letting each backend's `apply()` coerce
    against the actual column type keeps these filters portable.
    """
    text = str(raw).strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise FilterValidationError(
            _("%(raw)s is not a valid number") % {"raw": repr(raw)}
        ) from None


class EqualFilter(BaseFilter):
    """`field == value` for numeric fields."""

    name = "eq"
    label = _("Equals")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class NotEqualFilter(BaseFilter):
    """`field != value` for numeric fields."""

    name = "neq"
    label = _("Not equal")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class GreaterThanFilter(BaseFilter):
    """`field > value`."""

    name = "gt"
    label = _("Greater than")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class LessThanFilter(BaseFilter):
    """`field < value`."""

    name = "lt"
    label = _("Less than")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class GreaterThanOrEqualFilter(BaseFilter):
    """`field >= value`."""

    name = "gte"
    label = _("Greater than or equal")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class LessThanOrEqualFilter(BaseFilter):
    """`field <= value`."""

    name = "lte"
    label = _("Less than or equal")
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)


class BetweenFilter(BaseFilter):
    """`value <= field <= value2`."""

    name = "between"
    label = _("Between")
    data_type = FilterDataType.NUMBER
    has_value2 = True

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)
