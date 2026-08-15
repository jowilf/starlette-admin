"""Seed sample data for the 06-inline-forms example."""

from sqlalchemy import Engine
from sqlalchemy.orm import Session


def seed_data(engine: Engine) -> None:
    from app import Article, Comment, Order, OrderLine, Project, Task

    with Session(engine) as session:
        if session.query(Article).count() > 0:
            return

        # Articles with comments (Pattern 1: auto-detected FK)
        articles = [
            Article(
                title="Getting started with Starlette Admin",
                body=(
                    "Starlette Admin is a fast, flexible admin framework built on top "
                    "of Starlette. This post walks you through the basics: defining "
                    "models, registering views, and running the dev server."
                ),
                comments=[
                    Comment(author="Alice", body="Great intro, very clear!"),
                    Comment(author="Bob", body="Helped me set up my first project."),
                ],
            ),
            Article(
                title="SQLAlchemy relationships",
                body=(
                    "A practical guide to SQLAlchemy ORM relationships: one-to-many, "
                    "many-to-many, and self-referential patterns."
                ),
                comments=[
                    Comment(
                        author="Charlie", body="The lazy-loading tip saved me hours."
                    ),
                ],
            ),
            Article(
                title="Async Python in 2025",
                body="How asyncio, anyio, and ASGI frameworks fit together.",
                comments=[],
            ),
        ]
        session.add_all(articles)

        # Projects with tasks (Pattern 2: explicit fk_attr)
        projects = [
            Project(
                name="Admin Redesign",
                description="Redesign the admin interface for better UX.",
                tasks=[
                    Task(title="Wireframe new layout"),
                    Task(title="Implement inline forms", done=True),
                    Task(title="Write documentation"),
                ],
            ),
            Project(
                name="API v2",
                description="Next-generation REST API with OpenAPI support.",
                tasks=[
                    Task(title="Define schema"),
                    Task(title="Implement endpoints"),
                    Task(title="Add auth middleware"),
                ],
            ),
            Project(
                name="Mobile App",
                description="Cross-platform mobile client.",
                tasks=[
                    Task(title="Set up React Native project"),
                    Task(title="Integrate with API v2", done=True),
                ],
            ),
        ]
        session.add_all(projects)

        # Orders with lines (Pattern 3: composite FK)
        orders = [
            Order(
                store_id=1,
                seq=1,
                customer="Acme Corp",
                lines=[
                    OrderLine(
                        order_store_id=1,
                        order_seq=1,
                        line_no=1,
                        product="Widget A",
                        qty=10,
                    ),
                    OrderLine(
                        order_store_id=1,
                        order_seq=1,
                        line_no=2,
                        product="Widget B",
                        qty=5,
                    ),
                ],
            ),
            Order(
                store_id=1,
                seq=2,
                customer="Globex Inc",
                lines=[
                    OrderLine(
                        order_store_id=1,
                        order_seq=2,
                        line_no=1,
                        product="Gadget X",
                        qty=3,
                    ),
                    OrderLine(
                        order_store_id=1,
                        order_seq=2,
                        line_no=2,
                        product="Gadget Y",
                        qty=1,
                    ),
                ],
            ),
            Order(
                store_id=2,
                seq=1,
                customer="Initech",
                lines=[
                    OrderLine(
                        order_store_id=2,
                        order_seq=1,
                        line_no=1,
                        product="Doohickey",
                        qty=50,
                    ),
                ],
            ),
        ]
        session.add_all(orders)
        session.commit()
