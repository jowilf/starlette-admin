"""Seed sample blog posts for the quickstart application."""

from datetime import UTC, datetime

from sqlalchemy import Engine
from sqlalchemy.orm import Session

POSTS = [
    (
        "Getting Started with Starlette Admin",
        "getting-started-with-starlette-admin",
        (
            "Starlette Admin is a fast, flexible admin framework built on top of "
            "Starlette. This post walks you through the basics: defining models, "
            "registering views, and running the dev server. You will have a working "
            "admin interface in under five minutes."
        ),
        "PUBLISHED",
        342,
        datetime(2025, 3, 1, 10, 0, tzinfo=UTC),
        datetime(2025, 3, 1, 9, 30, tzinfo=UTC),
    ),
    (
        "Customizing List Views",
        "customizing-list-views",
        (
            "The list view is where your users spend most of their time. "
            "Learn how to configure sortable columns, search fields, pagination, "
            "and row actions to match the way your team actually works."
        ),
        "PUBLISHED",
        198,
        datetime(2025, 4, 14, 8, 0, tzinfo=UTC),
        datetime(2025, 4, 13, 17, 45, tzinfo=UTC),
    ),
    (
        "Computed Fields and Virtual Columns",
        "computed-fields-and-virtual-columns",
        (
            "Sometimes the value you want to display is not stored directly in the "
            "database. ComputedField lets you derive a column on the fly using any "
            "Python callable: perfect for word counts, formatted prices, or "
            "relationship summaries."
        ),
        "DRAFT",
        0,
        None,
        datetime(2025, 5, 20, 11, 0, tzinfo=UTC),
    ),
    (
        "Authentication and Permissions",
        "authentication-and-permissions",
        (
            "Starlette Admin ships with a pluggable auth backend. This post covers "
            "the built-in session-based provider, role-based access control, and how "
            "to write your own backend to integrate with an existing user store."
        ),
        "DRAFT",
        0,
        None,
        datetime(2025, 6, 3, 14, 20, tzinfo=UTC),
    ),
    (
        "Migrating from Flask-Admin",
        "migrating-from-flask-admin",
        (
            "Already running Flask-Admin? This guide maps the key concepts "
            "(ModelView, form overrides, column formatters) to their Starlette Admin "
            "equivalents and highlights what you can drop entirely."
        ),
        "ARCHIVED",
        87,
        datetime(2024, 11, 5, 9, 0, tzinfo=UTC),
        datetime(2024, 11, 4, 16, 0, tzinfo=UTC),
    ),
]


def seed_posts(engine: Engine) -> None:
    from app import Post, PostStatus

    with Session(engine) as session:
        if session.query(Post).count() > 0:
            return

        rows = [
            Post(
                title=title,
                slug=slug,
                content=content,
                status=PostStatus(status),
                views=views,
                published_at=published_at,
                created_at=created_at,
            )
            for title, slug, content, status, views, published_at, created_at in POSTS
        ]
        session.add_all(rows)
        session.commit()
