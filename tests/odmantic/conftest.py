import asyncio

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine, SyncEngine
from pymongo import MongoClient

from tests.odmantic import MONGO_DATABASE, MONGO_URI


@pytest_asyncio.fixture(scope="session")
def event_loop():
    asyncio.get_event_loop().close()
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def aio_engine(event_loop):
    client = AsyncIOMotorClient(MONGO_URI, io_loop=event_loop)
    sess = AIOEngine(client, MONGO_DATABASE)
    yield sess
    await client.drop_database(MONGO_DATABASE)
    client.close()


@pytest.fixture(scope="function")
def sync_engine():
    client = MongoClient(MONGO_URI)
    sess = SyncEngine(client, MONGO_DATABASE)
    yield sess
    client.drop_database(MONGO_DATABASE)
    client.close()
