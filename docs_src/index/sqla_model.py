from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)


class PostView(ModelView, model=Post):
    pass


Base.metadata.create_all(engine)
app = Starlette()

admin = Admin(engine)
admin.add_view(PostView)
admin.mount_to(app)
