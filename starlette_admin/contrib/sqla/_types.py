from typing import Union

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session

ENGINE_TYPE = Union[Engine, AsyncEngine]
SESSION_TYPE = Union[Session, AsyncSession]
