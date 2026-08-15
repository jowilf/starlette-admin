"""Seed 50 products across categories with varied prices, statuses, and dates."""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import Engine
from sqlalchemy.orm import Session

PRODUCTS = [
    # (name, price, status, tags) noqa: ERA001
    # Electronics
    (
        "Wireless Headphones Pro",
        "149.99",
        "ACTIVE",
        ["electronics", "audio", "wireless"],
    ),
    ("Bluetooth Speaker", "79.99", "ACTIVE", ["electronics", "audio"]),
    ("USB-C Hub 7-in-1", "49.99", "ACTIVE", ["electronics", "accessories"]),
    ("Mechanical Keyboard", "119.00", "ACTIVE", ["electronics", "peripherals"]),
    ("4K Webcam", "89.99", "OUT_OF_STOCK", ["electronics", "video"]),
    (
        "Noise-Cancelling Earbuds",
        "199.99",
        "ACTIVE",
        ["electronics", "audio", "wireless"],
    ),
    ("Portable Charger 20000mAh", "39.99", "ACTIVE", ["electronics", "accessories"]),
    ("Smart LED Strip", "24.99", "DISCONTINUED", ["electronics", "lighting"]),
    ("Wireless Mouse", "34.99", "ACTIVE", ["electronics", "peripherals"]),
    ("External SSD 1TB", "109.99", "ACTIVE", ["electronics", "storage"]),
    # Kitchen
    ("Stainless Steel Water Bottle", "29.99", "ACTIVE", ["kitchen", "drinkware"]),
    ("Electric Kettle 1.7L", "44.99", "ACTIVE", ["kitchen", "appliances"]),
    ("Non-stick Frying Pan 28cm", "39.99", "ACTIVE", ["kitchen", "cookware"]),
    ("French Press Coffee Maker", "34.99", "OUT_OF_STOCK", ["kitchen", "coffee"]),
    ("Silicone Spatula Set", "12.99", "ACTIVE", ["kitchen", "utensils"]),
    ("Digital Kitchen Scale", "19.99", "ACTIVE", ["kitchen", "tools"]),
    ("Bamboo Cutting Board", "22.99", "ACTIVE", ["kitchen", "tools", "eco"]),
    ("Vacuum Insulated Mug", "27.99", "ACTIVE", ["kitchen", "drinkware"]),
    ("Air Fryer 4L", "89.99", "ACTIVE", ["kitchen", "appliances"]),
    ("Herb Garden Kit", "18.99", "DISCONTINUED", ["kitchen", "garden"]),
    # Clothing
    ("Merino Wool Beanie", "24.99", "ACTIVE", ["clothing", "winter"]),
    ("Organic Cotton T-Shirt", "29.99", "ACTIVE", ["clothing", "basics", "eco"]),
    ("Waterproof Rain Jacket", "89.99", "ACTIVE", ["clothing", "outerwear"]),
    ("Compression Running Socks", "14.99", "OUT_OF_STOCK", ["clothing", "sports"]),
    ("Fleece Pullover", "59.99", "ACTIVE", ["clothing", "outerwear"]),
    ("UV-Protection Cap", "19.99", "ACTIVE", ["clothing", "accessories"]),
    ("Thermal Base Layer", "44.99", "OUT_OF_STOCK", ["clothing", "winter", "sports"]),
    ("Bamboo Yoga Pants", "54.99", "ACTIVE", ["clothing", "sports", "eco"]),
    ("Denim Work Apron", "49.99", "DISCONTINUED", ["clothing", "work"]),
    ("Reflective Running Vest", "32.99", "ACTIVE", ["clothing", "sports", "safety"]),
    # Sports & Outdoors
    ("Foam Yoga Mat 6mm", "34.99", "ACTIVE", ["sports", "yoga"]),
    ("Resistance Band Set", "22.99", "ACTIVE", ["sports", "fitness"]),
    ("Hydration Running Belt", "27.99", "ACTIVE", ["sports", "running"]),
    ("Adjustable Dumbbell 20kg", "119.99", "ACTIVE", ["sports", "weights"]),
    ("Camping Headlamp 400lm", "29.99", "ACTIVE", ["sports", "outdoor", "camping"]),
    ("Trekking Pole Set", "54.99", "OUT_OF_STOCK", ["sports", "hiking"]),
    ("Waterproof Dry Bag 20L", "19.99", "ACTIVE", ["sports", "outdoor"]),
    ("Silicone Swim Goggles", "16.99", "ACTIVE", ["sports", "swimming"]),
    ("Jump Rope Speed", "12.99", "ACTIVE", ["sports", "fitness"]),
    (
        "Foldable Camping Chair",
        "44.99",
        "DISCONTINUED",
        ["sports", "outdoor", "camping"],
    ),
    # Books & Stationery
    ("Dotted Notebook A5", "9.99", "ACTIVE", ["stationery", "notebooks"]),
    ("Fountain Pen Set", "39.99", "ACTIVE", ["stationery", "writing"]),
    ("Desk Organiser Bamboo", "29.99", "ACTIVE", ["stationery", "desk", "eco"]),
    ("Sticky Notes 5-Pack", "5.99", "ACTIVE", ["stationery", "office"]),
    ("Watercolour Pencil Set 36", "24.99", "OUT_OF_STOCK", ["stationery", "art"]),
    ("Leather Journal Hardcover", "34.99", "ACTIVE", ["stationery", "notebooks"]),
    ("Whiteboard Marker Set", "8.99", "ACTIVE", ["stationery", "office"]),
    ("Washi Tape Collection 10pc", "11.99", "ACTIVE", ["stationery", "craft"]),
    ("Blueprint Graph Paper Pad", "7.99", "DISCONTINUED", ["stationery", "drawing"]),
    ("Ergonomic Pen Grip Pack", "6.99", "ACTIVE", ["stationery", "writing"]),
]


def _spread_dates(n: int) -> list[datetime]:
    """Return n datetimes spread across the last ~90 days, biased toward recent."""
    now = datetime.utcnow()
    dates = []
    for _ in range(n):
        # ~30 % this month, ~40 % last month, ~30 % older
        r = random.random()
        if r < 0.30:
            days_back = random.randint(0, 29)
        elif r < 0.70:
            days_back = random.randint(30, 59)
        else:
            days_back = random.randint(60, 90)
        offset = timedelta(
            days=days_back, hours=random.randint(0, 23), minutes=random.randint(0, 59)
        )
        dates.append(now - offset)
    return dates


def seed_products(engine: Engine) -> None:
    from app import Product, ProductStatus

    with Session(engine) as session:
        if session.query(Product).count() > 0:
            return

        random.seed(42)
        dates = _spread_dates(len(PRODUCTS))

        rows = []
        for (name, price, status_str, tags), created_at in zip(PRODUCTS, dates):
            rows.append(
                Product(
                    name=name,
                    price=Decimal(price),
                    status=ProductStatus(status_str),
                    tags=tags,
                    created_at=created_at,
                )
            )

        session.add_all(rows)
        session.commit()
