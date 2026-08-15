"""Custom filter implementations for the filters example."""

from datetime import datetime
from typing import Any

from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


class ActiveThisMonthFilter(BaseFilter):
    """Products created on or after the first day of the current month."""

    name = "this_month"
    label = "Created this month"
    data_type = FilterDataType.NONE  # no value input: the range is derived from now()

    def apply(self, ctx: FilterApplyContext) -> Any:
        now = datetime.utcnow()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        col = getattr(ctx.view.model, ctx.field_name)
        return col.between(start, now)
