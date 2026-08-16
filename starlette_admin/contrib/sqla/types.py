from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

AsyncSessionProvider = AsyncEngine | async_sessionmaker[AsyncSession]
SyncSessionProvider = Engine | sessionmaker[Session]
SessionProvider = AsyncSessionProvider | SyncSessionProvider
