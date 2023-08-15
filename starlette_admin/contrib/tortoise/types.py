from typing import *
from tortoise.models import Model as TortoiseModel

Where = Optional[Union[Dict[str, Any], str]]
OrderBy = Optional[List[str]]
Pk = int
Pks = Sequence[Pk]
