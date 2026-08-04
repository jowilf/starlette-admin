"""Seed sample employees for the custom fields application."""

import random

from faker import Faker
from sqlalchemy import Engine
from sqlalchemy.orm import Session

DEPARTMENTS = ["Engineering", "Design", "Sales", "Support", "Marketing"]
STATUSES = ["Online", "Busy", "Offline"]


def seed_employees(engine: Engine) -> None:
    """Seed 200 employees (via Faker) without avatars; upload one through the
    admin form to see `AvatarNameField` render it next to the name."""
    from app import Employee

    fake = Faker()

    with Session(engine) as session:
        if session.query(Employee).count() > 0:
            return

        rows = [
            Employee(
                name=fake.name(),
                city=fake.city(),
                start_date=fake.date_between(start_date="-8y", end_date="today"),
                department=random.choice(DEPARTMENTS),
                status=random.choice(STATUSES),
            )
            for _ in range(200)
        ]
        session.add_all(rows)
        session.commit()
