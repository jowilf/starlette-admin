import os
from contextlib import asynccontextmanager

import uvicorn
from libcloud.storage.base import StorageDriver
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError, Provider
from sqlalchemy import ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_file import FileField, ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView

DATABASE_FILE = "13_sqla_file.sqlite"
UPLOAD_DIR = "upload/"

engine = create_engine(
    "sqlite:///" + DATABASE_FILE,
    connect_args={"check_same_thread": False},
    echo=True,
)


# ── Models ──────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100))
    # sqlalchemy-file handles upload/storage; starlette-admin renders the field automatically
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )
    books: Mapped[list["Book"]] = relationship("Book", back_populates="author")

    def __admin_repr__(self, request) -> str:
        return self.name or f"Author #{self.id}"


class Book(Base):
    __tablename__ = "book"

    isbn: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    cover = mapped_column(
        ImageField(
            upload_storage="cover",
            thumbnail_size=(128, 128),
            validators=[SizeValidator("1M")],
        )
    )
    document = mapped_column(
        FileField(
            upload_storage="documents",
            validators=[
                SizeValidator("5M"),
                ContentTypeValidator(
                    allowed_content_types=[
                        "application/pdf",
                        "application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ]
                ),
            ],
        )
    )
    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(Author.id))
    author: Mapped["Author"] = relationship(Author, back_populates="books")

    def __admin_repr__(self, request) -> str:
        return self.title


class Dump(Base):
    """Demonstrates multiple-file fields with the default storage bucket."""

    __tablename__ = "dump"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    multiple_images = mapped_column(
        ImageField(
            multiple=True,
            validators=[SizeValidator("100k")],
        )
    )
    multiple_files = mapped_column(
        FileField(
            multiple=True,
            validators=[SizeValidator("100k")],
        )
    )


# ── Storage ─────────────────────────────────────────────────────────────────────


def _get_or_create_container(driver: StorageDriver, container_name: str):
    try:
        return driver.get_container(container_name)
    except ContainerDoesNotExistError:
        return driver.create_container(container_name)


def configure_storage():
    os.makedirs(UPLOAD_DIR, 0o777, exist_ok=True)
    cls = get_driver(Provider.LOCAL)
    driver = cls(UPLOAD_DIR)
    StorageManager.add_storage("default", _get_or_create_container(driver, "bin"))
    StorageManager.add_storage("cover", _get_or_create_container(driver, "book-cover"))
    StorageManager.add_storage(
        "documents", _get_or_create_container(driver, "book-docs")
    )
    StorageManager.add_storage("avatar", _get_or_create_container(driver, "avatars"))


# ── App ─────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    configure_storage()
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin →</a>'),
        )
    ],
)

admin = Admin(
    engine,
    title="Example: SQLAlchemy-file",
    secret_key="dev-only-change-me",
    debug=True,
)

admin.add_view(ModelView(Author, icon="fa fa-users"))
admin.add_view(ModelView(Book, icon="fa fa-book"))
admin.add_view(ModelView(Dump, icon="fa fa-dumpster"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
