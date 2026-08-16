from datetime import UTC, datetime, timedelta

from models import Book, Genre, Loan, LoanStatus, Member, MembershipType


async def seed() -> None:
    # Genres
    fiction = await Genre(
        name="Fiction",
        color="#4e79a7",
        description="Imaginative narratives and invented stories.",
    ).create()
    sci_fi = await Genre(
        name="Science Fiction",
        color="#59a14f",
        description="Speculative fiction based on scientific concepts.",
    ).create()
    mystery = await Genre(
        name="Mystery",
        color="#f28e2b",
        description="Fiction involving a crime or puzzle to be solved.",
    ).create()
    history = await Genre(
        name="History",
        color="#e15759",
        description="Non-fiction exploring past events and civilisations.",
    ).create()
    tech = await Genre(
        name="Technology",
        color="#76b7b2",
        description="Books on software, engineering, and computing.",
    ).create()
    biography = await Genre(
        name="Biography",
        color="#edc948",
        description="Accounts of people's lives written by others.",
    ).create()

    # Books
    b1 = await Book(
        title="Dune",
        isbn="9780441013593",
        synopsis=(
            "Set in the distant future, Dune follows Paul Atreides as his family "
            "accepts stewardship of the desert planet Arrakis, the only source of "
            "the most valuable substance in the universe."
        ),
        published_year=1965,
        page_count=412,
        total_copies=3,
        featured=True,
        tags=["classic", "space opera", "ecology"],
        genres=[sci_fi, fiction],
        created_at=datetime.now(UTC) - timedelta(days=120),
    ).create()

    b2 = await Book(
        title="The Name of the Rose",
        isbn="9780156001311",
        synopsis=(
            "A historical murder mystery set in a 14th-century Italian monastery, "
            "where a Franciscan friar must solve a series of unexplained deaths."
        ),
        published_year=1980,
        page_count=502,
        total_copies=2,
        featured=False,
        tags=["medieval", "detective", "italy"],
        genres=[mystery, history],
        created_at=datetime.now(UTC) - timedelta(days=100),
    ).create()

    b3 = await Book(
        title="Clean Code",
        isbn="9780132350884",
        synopsis=(
            "A handbook of agile software craftsmanship. Robert C. Martin presents "
            "best practices for writing clean, readable, and maintainable code."
        ),
        published_year=2008,
        page_count=431,
        total_copies=4,
        featured=True,
        tags=["programming", "best practices", "refactoring"],
        genres=[tech],
        created_at=datetime.now(UTC) - timedelta(days=80),
    ).create()

    b4 = await Book(
        title="Sapiens: A Brief History of Humankind",
        isbn="9780062316097",
        synopsis=(
            "A groundbreaking narrative of humanity's creation and evolution, "
            "tracking the full story of human beings from ancient foragers to "
            "the cognitive, agricultural, and scientific revolutions."
        ),
        published_year=2011,
        page_count=443,
        total_copies=5,
        featured=True,
        tags=["anthropology", "evolution", "civilisation"],
        genres=[history, biography],
        created_at=datetime.now(UTC) - timedelta(days=60),
    ).create()

    b5 = await Book(
        title="Foundation",
        isbn="9780553293357",
        synopsis=(
            "Isaac Asimov's classic tale of the fall of the Galactic Empire and "
            "the efforts of a mathematician to preserve human knowledge through "
            "a dark age spanning thousands of years."
        ),
        published_year=1951,
        page_count=255,
        total_copies=2,
        featured=False,
        tags=["classic", "galactic empire", "psychohistory"],
        genres=[sci_fi, fiction],
        created_at=datetime.now(UTC) - timedelta(days=40),
    ).create()

    # Members
    alice = await Member(
        full_name="Alice Moreau",
        email="alice@example.com",
        phone="+33 6 12 34 56 78",
        membership_type=MembershipType.PREMIUM,
        notes="Prefers science fiction and technology titles.",
        joined_at=datetime.now(UTC) - timedelta(days=200),
    ).create()

    bob = await Member(
        full_name="Bob Nguyen",
        email="bob@example.com",
        phone="+1 555 234 5678",
        membership_type=MembershipType.BASIC,
        joined_at=datetime.now(UTC) - timedelta(days=90),
    ).create()

    carol = await Member(
        full_name="Carol Ibáñez",
        email="carol@example.com",
        membership_type=MembershipType.STUDENT,
        notes="Graduate student in history. Eligible for extended loan periods.",
        joined_at=datetime.now(UTC) - timedelta(days=45),
    ).create()

    # Loans
    await Loan(
        book=b1,
        member=alice,
        loan_date=datetime.now(UTC) - timedelta(days=10),
        due_date=datetime.now(UTC) + timedelta(days=4),
        status=LoanStatus.ACTIVE,
    ).create()

    await Loan(
        book=b3,
        member=alice,
        loan_date=datetime.now(UTC) - timedelta(days=30),
        due_date=datetime.now(UTC) - timedelta(days=16),
        returned_at=datetime.now(UTC) - timedelta(days=17),
        status=LoanStatus.RETURNED,
    ).create()

    await Loan(
        book=b4,
        member=bob,
        loan_date=datetime.now(UTC) - timedelta(days=25),
        due_date=datetime.now(UTC) - timedelta(days=11),
        status=LoanStatus.OVERDUE,
        notes="Member notified by email on 2026-06-17.",
    ).create()

    await Loan(
        book=b2,
        member=carol,
        loan_date=datetime.now(UTC) - timedelta(days=5),
        due_date=datetime.now(UTC) + timedelta(days=9),
        status=LoanStatus.ACTIVE,
    ).create()

    await Loan(
        book=b5,
        member=bob,
        loan_date=datetime.now(UTC) - timedelta(days=60),
        due_date=datetime.now(UTC) - timedelta(days=46),
        returned_at=datetime.now(UTC) - timedelta(days=48),
        status=LoanStatus.RETURNED,
    ).create()
