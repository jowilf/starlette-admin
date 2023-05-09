import mongoengine
import pytest
from gridfs import GridFS
from motor.motor_asyncio import AsyncIOMotorClient

from tests.beanie import MONGO_COL_GRIDFS, MONGO_DATABASE, MONGO_URI


@pytest.fixture()
def cli():
    return AsyncIOMotorClient(MONGO_URI)


@pytest.fixture()
def db(cli):
    return cli[MONGO_DATABASE]


@pytest.fixture()
def fs():
    db = mongoengine.connect(
        db=MONGO_DATABASE,
        host=MONGO_URI,
        alias=MONGO_DATABASE,
        uuidrepresentation="standard",
    )
    return GridFS(database=db[MONGO_DATABASE], collection=MONGO_COL_GRIDFS)
