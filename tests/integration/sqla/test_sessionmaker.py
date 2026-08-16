"""Admin() accepting a sessionmaker / async_sessionmaker instead of an engine.

Covers the multi-bind case: a single sessionmaker/async_sessionmaker routes
each model to its own database (e.g. horizontal partitioning), which a plain
``engine=`` argument cannot express. ``sqla_backend`` provides the primary
database (sqlite/mysql/postgres); the secondary database is always a scratch
sqlite file since the point under test is the routing, not the backend.
"""

from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.integration.sqla.utils import get_async_test_engine, get_test_engine
from tests.utils import csrf_async_client


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "sessionmaker_article"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))


class Comment(Base):
    __tablename__ = "sessionmaker_comment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(String(100))


class ArticleView(ModelView):
    fields = ["id", "title"]


class CommentView(ModelView):
    fields = ["id", "body"]


def _make_client(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return csrf_async_client(app)


async def test_sync_sessionmaker_multi_bind(sqla_backend, tmp_path):
    """Article lives on the primary (parametrized) DB, Comment on a second one."""
    primary_engine = get_test_engine()
    secondary_engine = create_engine(f"sqlite:///{tmp_path / 'secondary.db'}")
    Base.metadata.create_all(primary_engine, tables=[Article.__table__])
    Base.metadata.create_all(secondary_engine, tables=[Comment.__table__])
    try:
        session_maker = sessionmaker(
            binds={Article: primary_engine, Comment: secondary_engine}
        )

        admin = Admin(session_maker)
        admin.add_view(ArticleView(Article))
        admin.add_view(CommentView(Comment))

        async with _make_client(admin) as client:
            response = await client.post(
                "/admin/article/create",
                data={"title": "Hello"},
                follow_redirects=False,
            )
            assert response.status_code == 303
            response = await client.post(
                "/admin/comment/create",
                data={"body": "Nice post"},
                follow_redirects=False,
            )
            assert response.status_code == 303

        with Session(primary_engine) as s:
            assert s.query(Article).filter_by(title="Hello").one() is not None
        with Session(secondary_engine) as s:
            assert s.query(Comment).filter_by(body="Nice post").one() is not None
    finally:
        Base.metadata.drop_all(primary_engine, tables=[Article.__table__])
        Base.metadata.drop_all(secondary_engine, tables=[Comment.__table__])


async def test_async_sessionmaker_multi_bind(sqla_backend, tmp_path):
    """Same routing as above, exercised through async_sessionmaker."""
    primary_engine = get_async_test_engine()
    secondary_engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'secondary_async.db'}"
    )
    async with primary_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Article.__table__])
    async with secondary_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Comment.__table__])
    try:
        session_maker = async_sessionmaker(
            binds={Article: primary_engine, Comment: secondary_engine},
            expire_on_commit=False,
        )

        admin = Admin(session_maker)
        admin.add_view(ArticleView(Article))
        admin.add_view(CommentView(Comment))

        async with _make_client(admin) as client:
            response = await client.post(
                "/admin/article/create",
                data={"title": "World"},
                follow_redirects=False,
            )
            assert response.status_code == 303
            response = await client.post(
                "/admin/comment/create",
                data={"body": "Great read"},
                follow_redirects=False,
            )
            assert response.status_code == 303

        async with AsyncSession(primary_engine) as s:
            result = await s.execute(select(Article).filter_by(title="World"))
            assert result.scalar_one().id is not None
        async with AsyncSession(secondary_engine) as s:
            result = await s.execute(select(Comment).filter_by(body="Great read"))
            assert result.scalar_one().id is not None
    finally:
        async with primary_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all, tables=[Article.__table__])
        async with secondary_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all, tables=[Comment.__table__])
        await primary_engine.dispose()
        await secondary_engine.dispose()
