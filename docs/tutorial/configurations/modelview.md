# ModelView Configurations

Multiple options are available to customize your ModelView. For a complete list, have a look at the API documentation for
[BaseModelView()][starlette_admin.views.BaseModelView]. Here are some of the most commonly used options:

## Fields

Use `fields` property to customize which fields to include in admin view.

```Python hl_lines="21"
from sqlalchemy import JSON, Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin import TagsField
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    tags = Column(JSON)
    content = Column(Text)


class PostView(ModelView):
    fields = ["id", "title", Post.content, TagsField("tags", label="Tags")]


app = Starlette()

admin = Admin(engine)
admin.add_view(PostView(Post, icon="fa fa-blog"))
admin.mount_to(app)
```

## Exclusions

There are several options to help you exclude some fields from certain part of admin interface.

The options are:

* `exclude_fields_from_list`: List of fields to exclude in List page.
* `exclude_fields_from_detail`: List of fields to exclude in Detail page.
* `exclude_fields_from_create`: List of fields to exclude from creation page.
* `exclude_fields_from_edit`: List of fields to exclude from editing page.

```Python
class PostView(ModelView):
    exclude_fields_from_list = [Post.content, Post.tags]
```

## Searching & Sorting

Two options are available to specify which fields can be sorted or searched.

* `searchable_fields` for list of searchable fields
* `sortable_fields` for list of orderable fields

!!! Usage
    ```Python
    class PostView(ModelView):
        sortable_fields = [Post.id, "title"]
        searchable_fields = [Post.id, Post.title, "tags"]
    ```

## Exporting

You can export your data from list page. The export options can be set per model and includes the following options:

* `export_fields`:  List of fields to include in exports.
* `export_types`: A list of available export filetypes. Available
exports are `['csv', 'excel', 'pdf', 'print']`. By default, All of them are activated by default.

!!! Example
    ```Python
    from starlette_admin import ExportType

    class PostView(ModelView):
        export_fields = [Post.id, Post.content, Post.tags]
        export_types = [ExportType.CSV, ExportType.EXCEL]
    ```

## Pagination

The pagination options in the list page can be configured. The available options are:

* `page_size`: Default number of items to display in List page pagination.
            Default value is set to `10`.
* `page_size_options`: Pagination choices displayed in List page.  Default value is set to `[10, 25, 50, 100]`.
     Use `-1`to display All


!!! Example
    ```Python
    class PostView(ModelView):
        page_size = 5
        page_size_options = [5, 10, 25, 50, -1]
    ```

## Templates
The template files are built using Jinja2 and can be completely overridden in the configurations. The pages available are:

* `list_template`: List view template. Default is `list.html`.
* `detail_template`: Details view template. Default is `detail.html`.
* `create_template`: Edit view template. Default is `create.html`.
* `edit_template`: Edit view template. Default is `edit.html`.

!!! Example
    ```Python
    class PostView(ModelView):
        detail_template = "post_detail.html"
    ```
