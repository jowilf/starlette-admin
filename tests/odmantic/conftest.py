import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine, SyncEngine
from pymongo import MongoClient

from tests.odmantic import MONGO_DATABASE, MONGO_URI


@pytest_asyncio.fixture
async def aio_engine(event_loop):
    client = AsyncIOMotorClient(MONGO_URI, io_loop=event_loop)
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
