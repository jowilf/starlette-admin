# ModelView Configurations

There are multiple options available to customize your ModelView. For a complete list, please refer to the API
documentation for [BaseModelView()][starlette_admin.views.BaseModelView].

Here are some of the most commonly used options:

## Fields

You can use the `fields` property of the ModelView class to customize which fields are included in the admin view.

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

There are several options available for customizing which fields are displayed in different parts of the admin
view. These options include:

* `exclude_fields_from_list`: List of fields to exclude from the List page.
* `exclude_fields_from_detail`: List of fields to exclude from the Detail page.
* `exclude_fields_from_create`: List of fields to exclude from the creation page.
* `exclude_fields_from_edit`: List of fields to exclude from the editing page.\

```Python
class PostView(ModelView):
    exclude_fields_from_list = [Post.content, Post.tags]
```

!!! note
    For more advanced use cases, you can override
    the [ModelView.get_fields_list()][starlette_admin.views.BaseModelView.get_fields_list] function.

## Searching & Sorting

Several options are available to specify which fields can be sorted or searched.

* `searchable_fields` for list of searchable fields
* `sortable_fields` for list of orderable fields
* `fields_default_sort` for initial order (sort) to apply to the table

!!! Usage
    ```Python
    class PostView(ModelView):
        sortable_fields = [Post.id, "title"]
        searchable_fields = [Post.id, Post.title, "tags"]
        fields_default_sort = ["title", ("price", True)]
    ```

## Exporting

One of the powerful features of Starlette-admin is the ability to export data from the list page.

You can specify the export options for each ModelView using the following attributes:

* `export_fields`:  List of fields to include in the export.
* `export_types`: A list of available export filetypes. Available
  exports are `['csv', 'excel', 'pdf', 'print']`. By default, only `pdf` is disabled.

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

## Datatables Extensions

*starlette-admin* includes some datatable extensions by default. You can disable any of these extensions
in your `ModelView` by overridden following options:

* `column_visibility`: Enable/Disable [column visibility](https://datatables.net/extensions/buttons/built-in#Column-visibility) extension
* `search_builder`: Enable/Disable [search builder](https://datatables.net/extensions/searchbuilder/) extension
* `responsive_table`: Enable/Disable [responsive](https://datatables.net/extensions/responsive/) extension

!!! Example
    ```python
    class PostView(ModelView):
        column_visibility = False
        search_builder = False
        responsive_table = True
    ```

## Object Representation

*starlette-admin* provides two methods for customizing how objects are represented in the admin interface:

### `__admin_repr__`

It is a special method that can be defined in a model class to customize the object representation in the admin
interface. By default, only the value of the object's primary key attribute is displayed. However, by implementing
`__admin_repr__`, you can return a string that better represents the object in the admin interface.

For example, the following implementation for a `User` model will display the user's full name instead of their primary
key in the admin interface:

```python
class User:
    id: int
    first_name: str
    last_name: str

    def __admin_repr__(self, request: Request):
        return f"{self.last_name} {self.first_name}"
```

### `__admin_select2_repr__`

This method is similar to `__admin_repr__`, but it returns an HTML string that is used to display the object in
a `select2` widget. By default, all the object's attributes allowed for detail page are used except relation and file
fields.

!!! note
    The returned value should be valid HTML.

!!! danger
    Escape your database value to avoid Cross-Site Scripting (XSS) attack.
    You can use Jinja2 Template render with `autoescape=True`.
    For more information, visit [OWASP website](https://owasp.org/www-community/attacks/xss/)
    ```python
    from jinja2 import Template
    Template("Hello {{name}}", autoescape=True).render(name=name)
    ```

Here is an example implementation for a `User` model that includes the user's name and photo:

```python
class User:
    id: int
    name: str
    photo_url: str

    def __admin_select2_repr__(self, request: Request) -> str:
        return f'<div><img src="{escape(photo_url)}"><span>{escape(self.name)}</span></div>'
```
