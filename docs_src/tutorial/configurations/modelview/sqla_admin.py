from starlette.applications import Starlette
from starlette_admin import TagsField
from starlette_admin.contrib.sqla import Admin, ModelView

from .sqla_model import Post, engine


class PostAdmin(ModelView, model=Post):
    fields = ["id", "title", Post.content, TagsField("tags", label="Tags")]


app = Starlette()

admin = Admin(engine)
admin.add_view(PostAdmin)
admin.mount_to(app)
