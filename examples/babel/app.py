from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.i18n import SUPPORTED_LOCALES

from .config import ENGINE_URI

Base = declarative_base()

engine = create_engine(ENGINE_URI, connect_args={"check_same_thread": False}, echo=True)


def init_database() -> None:
    Base.metadata.create_all(engine)


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[init_database],
)


# Create models
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String(120))
    text = Column(Text, nullable=False)
    date = Column(DateTime)

    user_id = Column(Integer(), ForeignKey(User.id))
    user = relationship(User, backref="posts")


# Create admin
admin = Admin(
    engine,
    title="Example: Babel",
    i18n_config=I18nConfig(default_locale="fr", language_switcher=SUPPORTED_LOCALES),
)

# Add views
admin.add_view(ModelView(User, icon="fa fa-users"))
admin.add_view(ModelView(Post, icon="fa fa-blog", label="Blog Posts"))

# Mount admin
admin.mount_to(app)
