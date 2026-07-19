import random

from faker import Faker
from models import Post, Status, User
from sqlalchemy import Engine
from sqlalchemy.orm import Session


def seed_data(engine: Engine) -> None:
    """Seed 100 users (via Faker) each with 0-5 random posts."""
    fake = Faker()
    Faker.seed(42)

    with Session(engine) as session:
        if session.query(User).first() is not None:
            return

        statuses = list(Status)
        users: list[User] = []

        for _ in range(100):
            users.append(
                User(
                    name=fake.name(),
                    email=fake.unique.email(),
                    created_at=fake.date_time_between(
                        start_date="-90d", end_date="now"
                    ),
                )
            )

        session.add_all(users)
        session.flush()

        posts: list[Post] = []
        for user in users:
            for _ in range(random.randint(0, 5)):
                posts.append(
                    Post(
                        title=fake.sentence(nb_words=6).rstrip("."),
                        body=fake.paragraph(nb_sentences=4),
                        status=random.choice(statuses),
                        views=random.randint(0, 5000),
                        created_at=fake.date_time_between(
                            start_date=user.created_at, end_date="now"
                        ),
                        author=user,
                    )
                )

        session.add_all(posts)
        session.commit()
