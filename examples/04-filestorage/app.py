"""
04: File Storage Example

Demonstrates configuring and using file storage mechanisms in starlette-admin,
including handling ImageFields, FileFields, local storage configurations,
and file validation via magic bytes.
"""

from contextlib import asynccontextmanager

import filetype
import uvicorn
from sqlalchemy import JSON, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.fields import BaseField
from starlette_admin.storage import LocalStorage

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile
) -> None:
    """
    Validate document MIME type by inspecting the file's magic bytes.

    Prevents MIME-type spoofing by directly reading the file header rather
    than relying on the browser-provided Content-Type.
    """
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)
    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )


DATABASE_FILE = "04_file_storage.sqlite"
engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=True,
)

local_storage = LocalStorage(base_dir="uploads/", name="local")


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models in the file storage example."""


class Author(Base):
    """
    SQLAlchemy model representing an author.

    Includes an avatar field to demonstrate ImageField usage.
    """

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="author")

    async def __admin_repr__(self, request: Request) -> str:
        """String representation of the Author model."""
        return self.name


class Article(Base):
    """
    SQLAlchemy model representing an article.

    Includes fields for both cover images (ImageField) and
    attached documents (FileField).
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    document: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    author_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("authors.id"), nullable=True
    )

    author: Mapped["Author"] = relationship("Author", back_populates="articles")

    async def __admin_repr__(self, request: Request) -> str:
        """String representation of the Article model."""
        return self.title


class AuthorView(ModelView):
    """
    Admin interface for the Author model.

    Configures the avatar ImageField with its dedicated LocalStorage instance.
    """

    fields = [
        "id",
        "name",
        "bio",
        ImageField(
            "avatar",
            storage=local_storage,
            upload_folder="avatars",
            thumbnail_size=(512, 512),
        ),
        "articles",
    ]
    exclude_fields_from_list = ["bio", "articles"]


class ArticleView(ModelView):
    """
    Admin interface for the Article model.

    Configures ImageField and FileField, applying custom validation rules
    and size limits to document uploads.
    """

    fields = [
        "id",
        "title",
        "body",
        "author",
        ImageField(
            "cover",
            storage=local_storage,
            upload_folder="covers",
            thumbnail_size=(200, 200),
        ),
        FileField(
            "document",
            storage=local_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
            max_size=5 * 1024 * 1024,
            validators=[validate_document_type],
        ),
    ]
    exclude_fields_from_list = ["body"]


@asynccontextmanager
async def lifespan(app: Starlette):
    """Manage application lifecycle, ensuring database tables are created."""
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>File Storage example</h2>"
                "<p>Upload images and documents through the admin interface.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(
    engine, title="File Storage example", secret_key="dev-only-change-me", debug=True
)
admin.add_view(AuthorView(Author, icon="fa fa-users"))
admin.add_view(ArticleView(Article, icon="fa fa-newspaper"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
