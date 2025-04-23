import os
from pathlib import Path
from typing import List

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, TypeAdapter

from .models import Category, Manager, Product, Store

ALL_MODELS = [Product, Store, Manager]

MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE: str = os.environ.get("MONGO_DATABASE", "exampledb")
RECREATE_DB: bool = os.environ.get("RECREATE_DB", "False").lower() == "true"

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

mongo_client = AsyncIOMotorClient(MONGO_URI)


async def seed_db() -> None:
    with open(DATA_DIR / "products.json") as file:
        products_data = file.read()
    with open(DATA_DIR / "stores.json") as file:
        stores_data = file.read()
    with open(DATA_DIR / "managers.json") as file:
        managers_data = file.read()

    products_adapter = TypeAdapter(List[Product])
    products: List[Product] = products_adapter.validate_json(products_data)
    products = [await Product.insert(p) for p in products]

    stores_adapter = TypeAdapter(List[Store])
    stores: List[Store] = stores_adapter.validate_json(stores_data)
    bestbuy: Store = next([store for store in stores if store.name == "Best Buy"])
    bestbuy.products.extend([p for p in products if p.category == Category.ELECTRONICS])
    bestbuy = await Store.insert(bestbuy)

    walgreens: Store = next([store for store in stores if store.name == "Walgreens"])
    walgreens.products = [
        p
        for p in products
        if p.category in [Category.BEAUTY, Category.HOME, Category.FASHION]
    ]
    walgreens = await Store.insert(walgreens)

    managers_adapter = TypeAdapter(List[Manager])
    manager: Manager = managers_adapter.validate_json(managers_data)[0]

    manager.store = bestbuy
    manager = await manager.insert()


async def create_db_and_tables() -> List[BaseModel]:
    if RECREATE_DB:
        await mongo_client.drop_database(MONGO_DATABASE)
    await init_beanie(
        database=mongo_client.get_database(MONGO_DATABASE),
        document_models=ALL_MODELS,
    )
    if RECREATE_DB:
        await seed_db()

    return ALL_MODELS
