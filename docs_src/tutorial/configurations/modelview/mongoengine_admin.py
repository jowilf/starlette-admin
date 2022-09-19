from starlette.applications import Starlette
from starlette_admin import TextAreaField
from starlette_admin.contrib.mongoengine import Admin, ModelView

from .mongoengine_model import Post


class PostView(ModelView, document=Post):
    fields = ["id", Post.title, TextAreaField("content"), "tags"]
    exclude_fields_from_list = [Post.content]
    searchable_fields = [Post.id, Post.title]
    sortable_fields = [Post.id, Post.title]
    export_fields = [Post.id, Post.content, Post.tags]
    export_types = ["csv", "excel"]
    page_size = 5
    page_size_options = [5, 10, 25, 50, -1]
    detail_template = "post_detail.html"


app = Starlette()

admin = Admin()
admin.add_view(PostView)
admin.mount_to(app)
