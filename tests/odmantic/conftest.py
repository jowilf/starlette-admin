import asyncio

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine, SyncEngine
from pymongo import MongoClient

from tests.odmantic import MONGO_DATABASE, MONGO_URI


@pytest_asyncio.fixture
async def aio_engine():
    client = AsyncIOMotorClient(MONGO_URI)
    client.get_io_loop = asyncio.get_event_loop
    sess = AIOEngine(client, MONGO_DATABASE)
    yield sess
    await client.drop_database(MONGO_DATABASE)
    client.close()


@pytest.fixture
def sync_engine():
    client = MongoClient(MONGO_URI)
    sess = SyncEngine(client, MONGO_DATABASE)
    yield sess
    client.drop_database(MONGO_DATABASE)
    client.close()
