from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy_file import FileField, ImageField
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator

Base = declarative_base()


class Author(Base):
    __tablename__ = "author"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    avatar = Column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "book"

    isbn = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    cover = Column(
        ImageField(
            upload_storage="cover",
            thumbnail_size=(128, 128),
            validators=[SizeValidator("1M")],
        )
    )
    document = Column(
        FileField(
            upload_storage="document",
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
    author_id = Column(Integer, ForeignKey(Author.id))
    author = relationship(Author, back_populates="books")


class Dump(Base):
    __tablename__ = "dump"

    id = Column(Integer, primary_key=True)

    """
    When upload_storage is not specified, sqlalchemy-file use the first added storage
    >>> StorageManager.add_storage("default", get_or_create_container(driver, "bin"))
    """
    multiple_images = Column(
        ImageField(
            multiple=True,
            validators=[SizeValidator("100k")],
        )
    )
    multiple_files = Column(
        FileField(
            multiple=True,
            validators=[SizeValidator("100k")],
        )
    )
