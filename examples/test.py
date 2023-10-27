import uvicorn
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine(
    "sqlite:///test.db", connect_args={"check_same_thread": False}, echo=True
)


# Define your model
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column("title x", String)


Base.metadata.create_all(engine)

app = Starlette()  # FastAPI()

# Create admin
admin = Admin(engine, title="Example: SQLAlchemy", base_url="/")
view = ModelView(Post)
view.pk_attr = "id"

print("\n".join(map(str, view.fields)))
print("pk-attr", view.pk_attr)
# Add view
admin.add_view(view)

# Mount admin to your app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("test:app", reload=True, port=8081)
