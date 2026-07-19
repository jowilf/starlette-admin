from datetime import UTC, datetime, timedelta

from models import Article, ArticleStatus, Author, Category, Comment, Role
from sqlalchemy.orm import Session


def seed(session: Session) -> None:
    # Authors
    alice = Author(
        full_name="Alice Martin",
        email="alice@example.com",
        role=Role.ADMIN,
        avatar_color="#4e79a7",
        bio="Editor-in-chief with 10 years of experience in tech journalism.",
        created_at=datetime.now(UTC) - timedelta(days=90),
    )
    bob = Author(
        full_name="Bob Chen",
        email="bob@example.com",
        role=Role.EDITOR,
        avatar_color="#f28e2b",
        bio="Senior editor covering open-source and developer tooling.",
        created_at=datetime.now(UTC) - timedelta(days=60),
    )
    carol = Author(
        full_name="Carol Dupont",
        email="carol@example.com",
        role=Role.WRITER,
        avatar_color="#59a14f",
        bio="Freelance writer specialising in Python and web frameworks.",
        created_at=datetime.now(UTC) - timedelta(days=30),
    )
    session.add_all([alice, bob, carol])
    session.flush()

    # Categories
    python_cat = Category(
        name="Python",
        description="Python language, ecosystem, and best practices.",
    )
    web_cat = Category(
        name="Web Dev",
        description="Full-stack web development, frameworks, and APIs.",
    )
    devops_cat = Category(
        name="DevOps",
        description="CI/CD, containers, infrastructure, and deployment.",
    )
    session.add_all([python_cat, web_cat, devops_cat])
    session.flush()

    # Articles
    a1 = Article(
        title="Getting Started with SQLModel",
        content=(
            "SQLModel combines SQLAlchemy and Pydantic to give you a single model "
            "class that serves as both your ORM layer and your data-validation schema. "
            "In this guide we build a small REST API from scratch."
        ),
        tags=["sqlmodel", "python", "orm"],
        status=ArticleStatus.PUBLISHED,
        views=1240,
        published_at=datetime.now(UTC) - timedelta(days=20),
        created_at=datetime.now(UTC) - timedelta(days=25),
        author=alice,
        category=python_cat,
    )
    a2 = Article(
        title="Starlette Admin: A Tour",
        content=(
            "Starlette Admin is a fast, extensible admin framework built on top of "
            "Starlette. This article walks through its key features: model views, "
            "custom actions, inline forms, and event hooks."
        ),
        tags=["starlette", "admin", "python"],
        status=ArticleStatus.PUBLISHED,
        views=876,
        published_at=datetime.now(UTC) - timedelta(days=10),
        created_at=datetime.now(UTC) - timedelta(days=15),
        author=bob,
        category=web_cat,
    )
    a3 = Article(
        title="Docker Compose for Python Developers",
        content=(
            "Docker Compose lets you define multi-container applications in a single "
            "YAML file. We cover the essential patterns every Python developer needs: "
            "live-reload mounts, secret management, and health checks."
        ),
        tags=["docker", "devops", "python"],
        status=ArticleStatus.DRAFT,
        views=0,
        created_at=datetime.now(UTC) - timedelta(days=5),
        author=carol,
        category=devops_cat,
    )
    a4 = Article(
        title="Async SQLAlchemy Patterns",
        content=(
            "SQLAlchemy 2.0 ships first-class async support via asyncio. "
            "We compare lazy vs eager loading, session scoping, and connection "
            "pool sizing under realistic concurrency."
        ),
        tags=["sqlalchemy", "async", "python"],
        status=ArticleStatus.DRAFT,
        views=0,
        created_at=datetime.now(UTC) - timedelta(days=2),
        author=alice,
        category=python_cat,
    )
    a5 = Article(
        title="Building REST APIs with FastAPI",
        content=(
            "FastAPI is a modern, high-performance web framework for building APIs "
            "with Python 3.8+ based on standard Python type hints."
        ),
        tags=["fastapi", "rest", "python"],
        status=ArticleStatus.ARCHIVED,
        views=3100,
        published_at=datetime.now(UTC) - timedelta(days=180),
        created_at=datetime.now(UTC) - timedelta(days=200),
        author=bob,
        category=web_cat,
    )
    session.add_all([a1, a2, a3, a4, a5])
    session.flush()

    # Comments
    session.add_all(
        [
            Comment(
                author_name="Dave",
                email="dave@example.com",
                body="Great intro! The relationship examples were especially clear.",
                approved=True,
                created_at=datetime.now(UTC) - timedelta(days=18),
                article=a1,
            ),
            Comment(
                author_name="Eve",
                email="eve@example.com",
                body="Would love a follow-up on async sessions with SQLModel.",
                approved=True,
                created_at=datetime.now(UTC) - timedelta(days=17),
                article=a1,
            ),
            Comment(
                author_name="Frank",
                body="The action system is my favourite part of starlette-admin.",
                approved=True,
                created_at=datetime.now(UTC) - timedelta(days=8),
                article=a2,
            ),
            Comment(
                author_name="Grace",
                email="grace@example.com",
                body="Spam link removed.",
                approved=False,
                created_at=datetime.now(UTC) - timedelta(days=7),
                article=a2,
            ),
        ]
    )
    session.commit()
