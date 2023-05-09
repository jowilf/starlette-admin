from enum import Enum
from typing import List

from pydantic import BaseModel


class SortOption(str, Enum):
    desc = "desc"
    asc = "asc"
    NONE = "NONE"


class SortBy(BaseModel):
    name: str
    by: SortOption

    def to_str(self) -> str:
        """return a str as you expect to receive beanie for sort"""
        if self.by == SortOption.asc or self.by == SortOption.NONE:
            return "+" + self.name
        return "-" + self.name

    @staticmethod
    def parse(value: str) -> "SortBy":
        """example value: 'first_name asc'"""
        vals = value.split()
        option = vals[1] if len(vals) == 2 else SortOption.NONE
        return SortBy(name=vals[0], by=option)


def build_order_clauses(options: List[str]) -> List[str]:
    """https://beanie-odm.dev/tutorial/finding-documents/#sorting"""
    if options is None:
        return []
    sort_list = []
    for item in options:
        sort_list.append(SortBy.parse(item).to_str())
    return sort_list
