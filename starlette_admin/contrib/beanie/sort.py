from enum import Enum
from typing import List, Optional, Tuple, Union

from beanie.odm.enums import SortDirection
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
        option = SortOption(vals[1]) if len(vals) == 2 else SortOption.NONE
        return SortBy(name=vals[0], by=option)


# def build_order_clauses(options: Optional[List[str]]) -> List[str]:
def build_order_clauses(
    options: Optional[List[str]],
) -> Union[None, str, List[Tuple[str, SortDirection]], List]:
    """https://beanie-odm.dev/tutorial/finding-documents/#sorting"""
    if options is None:
        return []
    sort_list = []
    for item in options:
        sort_list.append(SortBy.parse(item).to_str())
    return sort_list
