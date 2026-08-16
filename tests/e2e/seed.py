"""Seed data for the e2e test application.

14 books across 4 authors so the default page size (10) always yields a
second page, and a spread of genres/stock/ratings so search, sort, and
filter tests have something to bite into.
"""

from datetime import date, datetime

from sqlalchemy import Engine
from sqlalchemy.orm import Session


def reset_and_seed(engine: Engine) -> None:
    """Wipe both tables and reseed, isolating mutations between test modules."""
    from tests.e2e.app import Author, Book

    with Session(engine) as session:
        session.query(Book).delete()
        session.query(Author).delete()
        session.commit()
    seed_data(engine)


def seed_data(engine: Engine) -> None:
    from tests.e2e.app import Author, Book, Genre

    with Session(engine) as session:
        if session.query(Author).count() > 0:
            return

        ursula = Author(
            name="Ursula K. Le Guin",
            email="ursula@example.com",
            bio="American author of speculative fiction.",
            birth_date=date(1929, 10, 21),
            is_active=True,
        )
        isaac = Author(
            name="Isaac Asimov",
            email="isaac@example.com",
            bio="American writer and professor of biochemistry.",
            birth_date=date(1920, 1, 2),
            is_active=True,
        )
        austen = Author(
            name="Jane Austen",
            email="jane@example.com",
            bio="English novelist known for her wit and social commentary.",
            birth_date=date(1775, 12, 16),
            is_active=False,
        )
        octavia = Author(
            name="Octavia Butler",
            email="octavia@example.com",
            bio="American science fiction author.",
            birth_date=date(1947, 6, 22),
            is_active=True,
        )
        session.add_all([ursula, isaac, austen, octavia])
        session.flush()

        books = [
            Book(
                author=ursula,
                title="A Wizard of Earthsea",
                isbn="978-0547773742",
                genre=Genre.FICTION,
                price=12.99,
                rating=5,
                published_at=datetime(1968, 11, 1),
                in_stock=True,
            ),
            Book(
                author=ursula,
                title="The Left Hand of Darkness",
                isbn="978-0441478125",
                genre=Genre.SCIENCE_FICTION,
                price=14.50,
                rating=5,
                published_at=datetime(1969, 3, 1),
                in_stock=True,
            ),
            Book(
                author=ursula,
                title="The Dispossessed",
                isbn="978-0060512750",
                genre=Genre.SCIENCE_FICTION,
                price=13.25,
                rating=4,
                published_at=datetime(1974, 5, 1),
                in_stock=False,
            ),
            Book(
                author=isaac,
                title="Foundation",
                isbn="978-0553293357",
                genre=Genre.SCIENCE_FICTION,
                price=9.99,
                rating=5,
                published_at=datetime(1951, 6, 1),
                in_stock=True,
            ),
            Book(
                author=isaac,
                title="I, Robot",
                isbn="978-0553294385",
                genre=Genre.SCIENCE_FICTION,
                price=8.99,
                rating=4,
                published_at=datetime(1950, 12, 2),
                in_stock=True,
            ),
            Book(
                author=isaac,
                title="The Gods Themselves",
                isbn="978-0553288100",
                genre=Genre.SCIENCE_FICTION,
                price=10.50,
                rating=4,
                published_at=datetime(1972, 3, 1),
                in_stock=False,
            ),
            Book(
                author=isaac,
                title="Asimov's Guide to Science",
                isbn="978-0465028805",
                genre=Genre.NON_FICTION,
                price=19.99,
                rating=4,
                published_at=datetime(1960, 1, 1),
                in_stock=True,
            ),
            Book(
                author=austen,
                title="Pride and Prejudice",
                isbn="978-1503290563",
                genre=Genre.FICTION,
                price=8.99,
                rating=5,
                published_at=datetime(1813, 1, 28),
                in_stock=True,
            ),
            Book(
                author=austen,
                title="Sense and Sensibility",
                isbn="978-1512334886",
                genre=Genre.FICTION,
                price=7.99,
                rating=4,
                published_at=datetime(1811, 10, 30),
                in_stock=True,
            ),
            Book(
                author=austen,
                title="Emma",
                isbn="978-1517216212",
                genre=Genre.FICTION,
                price=9.50,
                rating=5,
                published_at=datetime(1815, 12, 23),
                in_stock=False,
            ),
            Book(
                author=austen,
                title="Persuasion",
                isbn="978-1503222963",
                genre=Genre.FICTION,
                price=6.99,
                rating=4,
                published_at=datetime(1817, 8, 1),
                in_stock=True,
            ),
            Book(
                author=octavia,
                title="Kindred",
                isbn="978-0807083697",
                genre=Genre.SCIENCE_FICTION,
                price=13.99,
                rating=5,
                published_at=datetime(1979, 6, 1),
                in_stock=True,
            ),
            Book(
                author=octavia,
                title="Parable of the Sower",
                isbn="978-1587155831",
                genre=Genre.SCIENCE_FICTION,
                price=12.50,
                rating=5,
                published_at=datetime(1993, 11, 1),
                in_stock=True,
            ),
            Book(
                author=octavia,
                title="Bloodchild and Other Stories",
                isbn="978-1583800989",
                genre=Genre.SCIENCE_FICTION,
                price=11.25,
                rating=4,
                published_at=datetime(1995, 6, 1),
                in_stock=False,
            ),
        ]
        session.add_all(books)
        session.commit()
