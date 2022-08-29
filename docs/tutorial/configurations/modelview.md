# ModelView Configurations

Multiple options are available to customise your ModelView. This page will give you a basic introduction and for all the
details you can visit [API Reference][starlette_admin.views.BaseModelView].

Let's say you've defined your models like this:

=== "SQLAlchemy"
    ```python
    from sqlalchemy import Column, Integer, String, create_engine, Text, JSON
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    engine = create_engine(
        "sqlite:///example.db", connect_args={"check_same_thread": False}
    )
    
    
    class Post(Base):
        __tablename__ = "posts"
    
        id = Column(Integer, primary_key=True)
        title = Column(String)
        content = Column(Text)
        tags = Column(JSON)
    
    
    Base.metadata.create_all(engine)
    ```
=== "MongoEngine"

    ```python
    import mongoengine
    from mongoengine import connect
    
    connect("example")
    
    
    class Post(mongoengine.Document):
        title = mongoengine.StringField()
        content = mongoengine.StringField()
        tags = mongoengine.ListField(mongoengine.StringField())

    ```
and your admin views like this

=== "SQLAlchemy"
    ```Python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView
    
    
    class PostAdmin(ModelView, model=Post):
        pass
    
    
    app = Starlette()
    
    admin = Admin(engine)
    admin.add_view(PostAdmin)
    admin.mount_to(app)
    ```
=== "MongoEngine"

    ```Python
    from starlette.applications import Starlette
    from starlette_admin.contrib.mongoengine import Admin, ModelView
    
    
    class PostAdmin(ModelView, document=Post):
        pass
    
    
    app = Starlette()
    
    admin = Admin()
    admin.add_view(PostAdmin)
    admin.mount_to(app)
    ```
## Metadata

The metadata for the model. The options are:

* `name`: Display name for this model. Default value is the class name.
* `label`: Display name in menu structure for this model. Default value is class name + s.
* `icon`: Icon to be displayed for this model in the admin. Only FontAwesome names are supported.

!!! Example
    ```Python
    class PostView(ModelView, model=Post):
        name = "Post"
        label = "Blog Posts"
        icon = "fa fa-blog"
    ```
## Fields

Use `fields` property to customize which fields to include in admin view. You can use directly [Starlette-Admin Field][starlette_admin.fields.BaseField]
or give the attribute, and it will automatically convert into StarletteAdmin Field.

=== "SQLAlchemy"

    ```Python hl_lines="9"
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
    ```

=== "MongoEngine"

    ```Python hl_lines="9"
    from starlette.applications import Starlette
    from starlette_admin import TextAreaField
    from starlette_admin.contrib.mongoengine import Admin, ModelView
    
    from .mongoengine_model import Post
    
    
    class PostAdmin(ModelView, document=Post):
        fields = ["id", Post.title, TextAreaField("content"), "tags"]
    
    
    app = Starlette()
    
    admin = Admin()
    admin.add_view(PostAdmin)
    admin.mount_to(app)

    ```


## Exclusions

There are several options to help you exclude some fields from certain part of admin interface.

The options are:

* `exclude_fields_from_list`: List of fields to exclude in List page.
* `exclude_fields_from_detail`: List of fields to exclude in Detail page.
* `exclude_fields_from_create`: List of fields to exclude from creation page.
* `exclude_fields_from_edit`: List of fields to exclude from editing page.

!!! Example
    ```Python
    class PostAdmin(ModelView, model=Post):
        exclude_fields_from_list = [Post.content]
    ```

## Search & Sort

Two options are available to specify which fields can be sorted or searched.

* `searchable_fields` for list of searchable fields
* `sortable_fields` for list of orderable fields

!!! Example
    ```Python
    class PostAdmin(ModelView, model=Post):
        sortable_fields = [Post.id, Post.title]
        searchable_fields = [Post.id, Post.title, Post.tags]
    ```

## Exports

You can export your data from list page. The export options can be set per model and includes the following options:

* `export_fields`:  List of fields to include in exports.
* `export_types`: A list of available export filetypes. Available 
exports are `['csv', 'excel', 'pdf', 'print']`. All of them are activated by default.

!!! Example
    ```Python
    class PostAdmin(ModelView, model=Post):
        export_fields = [Post.id, Post.content, Post.tags]
        export_types = ["csv", "excel"]
    ```

## Pagination

The pagination options in the list page can be configured. The available options include:

* `page_size`: Default number of items to display in List page pagination.
            Default value is set to `10`.
* `page_size_options`: Pagination choices displayed in List page.  Default value is set to `[10, 25, 50, 100]`. 
     Use `-1`to display All


!!! Example
    ```Python
    class PostAdmin(ModelView, model=Post):
        page_size = 5
        page_size_options = [5, 10, 25, 50, -1]
    ```

## Templates
The template files are built using Jinja2 and can be completely overridden in the configurations. The pages available are:

* `list_template`: List view template. Default is `list.html`.
* `detail_template`: Details view template. Default is `details.html`.
* `create_template`: Edit view template. Default is `edit.html`.
* `edit_template`: Edit view template. Default is `edit.html`.

!!! Example
    ```Python
    class PostAdmin(ModelView, model=Post):
        detail_template = "post_detail.html"
    ```