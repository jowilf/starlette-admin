from datetime import date, datetime, time
from typing import Any

from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterValidationError,
)
from starlette_admin.i18n import (
    get_database_tzinfo,
    get_tzinfo,
    is_timezone_conversion_enabled,
)
from starlette_admin.i18n import (
    lazy_gettext as _,
)
from starlette_admin.logging import get_logger

_log = get_logger(__name__)


def _parse_temporal(data_type: FilterDataType, raw: Any) -> date | datetime | time:
    """Parse an ISO-8601 string into the Python type matching `data_type` (`date`, `datetime`, or `time`): the format produced by the corresponding native `<input type="date|datetime-local|time">` widgets.

    When timezone conversion is enabled and `data_type` is `DATETIME`, the parsed naive datetime is assumed to be in the user's timezone and is converted to the database timezone (returned as a naive datetime), matching the conversion performed by `DateTimeField.parse_form_data`.
    """
    text = str(raw)
    parsed: date | time | datetime
    try:
        if data_type == FilterDataType.DATE:
            parsed = date.fromisoformat(text)
        elif data_type == FilterDataType.TIME:
            parsed = time.fromisoformat(text)
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError:
        raise FilterValidationError(
            _("%(raw)s is not a valid ISO-8601 %(type)s")
            % {"raw": repr(raw), "type": data_type.value}
        ) from None

    _log.debug(
        "Parsed temporal value data_type=%s raw=%r result=%s",
        data_type.value,
        raw,
        parsed,
    )

    if data_type != FilterDataType.DATETIME:
        return parsed

    if not is_timezone_conversion_enabled():
        return parsed

    assert isinstance(parsed, datetime)
    user_tz = get_tzinfo()
    database_tz = get_database_tzinfo()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=user_tz)
    converted = parsed.astimezone(database_tz).replace(tzinfo=None)
    _log.debug(
        "Converted datetime to database timezone: raw=%r user_tz=%s database_tz=%s result=%s",
        raw,
        user_tz,
        database_tz,
        converted,
    )
    return converted


class DateEqualFilter(BaseFilter):
    """`field == value`, for [DateField][starlette_admin.fields.DateField].

    [DateTimeEqualFilter][starlette_admin.filters.date.DateTimeEqualFilter] and [TimeEqualFilter][starlette_admin.filters.date.TimeEqualFilter] cover `DateTimeField`/`ArrowField` and `TimeField` respectively; they exhibit the same behavior, but with a different `data_type` (and thus a different input widget or parsed type).
    """

    name = "eq"
    label = _("Is on")
    data_type = FilterDataType.DATE

    def parse_value(self, raw: Any) -> date | datetime | time:
        return _parse_temporal(self.data_type, raw)


class DateTimeEqualFilter(DateEqualFilter):
    label = _("Is at")
    data_type = FilterDataType.DATETIME


class TimeEqualFilter(DateEqualFilter):
    label = _("Is at")
    data_type = FilterDataType.TIME


class DateBetweenFilter(BaseFilter):
    """`value <= field <= value2`, for
    [DateField][starlette_admin.fields.DateField]. See
    [DateEqualFilter][starlette_admin.filters.date.DateEqualFilter] for how
    [DateTimeBetweenFilter][starlette_admin.filters.date.DateTimeBetweenFilter]
    and [TimeBetweenFilter][starlette_admin.filters.date.TimeBetweenFilter]
    relate to it.
    """

    name = "between"
    label = _("Between")
    data_type = FilterDataType.DATE
    has_value2 = True

    def parse_value(self, raw: Any) -> date | datetime | time:
        return _parse_temporal(self.data_type, raw)


class DateTimeBetweenFilter(DateBetweenFilter):
    data_type = FilterDataType.DATETIME


class TimeBetweenFilter(DateBetweenFilter):
    data_type = FilterDataType.TIME


class DateInPastFilter(BaseFilter):
    """`field` is before now. This filter needs no value; the comparison point is always "now", evaluated by the backend at query time (e.g., SQL `NOW()`), so this filter applies unchanged to date, datetime, and time fields alike."""

    name = "in_past"
    label = _("Is in the past")
    data_type = FilterDataType.NONE


class DateInFutureFilter(BaseFilter):
    """`field` is after now. See
    [DateInPastFilter][starlette_admin.filters.date.DateInPastFilter].
    """

    name = "in_future"
    label = _("Is in the future")
    data_type = FilterDataType.NONE
