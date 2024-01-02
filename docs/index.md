---
hide:
  - navigation
---

# Starlette-Admin

*Fast, beautiful, and extensible administrative interface framework for Starlette & FastApi applications*

<div align="center">
<a href="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml">
    <img src="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml/badge.svg" alt="Test suite">
</a>
<a href="https://github.com/jowilf/starlette-admin/actions">
    <img src="https://github.com/jowilf/starlette-admin/actions/workflows/publish.yml/badge.svg" alt="Publish">
</a>
<a href="https://codecov.io/gh/jowilf/starlette-admin">
    <img src="https://codecov.io/gh/jowilf/starlette-admin/branch/main/graph/badge.svg" alt="Codecov">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://badge.fury.io/py/starlette-admin.svg" alt="Package version">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://img.shields.io/pypi/pyversions/starlette-admin?color=2334D058" alt="Supported Python versions">
</a>
</div>
![Preview image](./images/preview.jpg)

## why starlette-admin?

FastAPI has emerged as a popular web framework for building APIs in Python. However, it lacks a mature admin interface
solution like Flask-Admin to quickly manage your data through a user-friendly interface. Although
solutions like Sqladmin and Fastapi-Admin exist, they only work with specific ORMs such as SQLAlchemy and Tortoise ORM.

Starlette-admin was born from the need for a FastAPI admin interface that works with various data layer. It aims
to provide a complete solution for CRUD interfaces regardless of the database backend. Starlette-admin works out of the
box with multiple ORM/ODMs and can also be used with a custom data layer.

## Getting started

* Check out [the quick start guide](https://jowilf.github.io/starlette-admin) to build your first admin interface
* Try
  the [live demo](https://starlette-admin-demo.jowilf.com/) to see it in
  action. ([Source code](https://github.com/jowilf/starlette-admin-demo))
* Browse the [/examples](https://github.com/jowilf/starlette-admin/tree/main/examples) to see sample usage with
  different ORM/ODMs
* For troubleshooting help, check out the [FAQ](#)
* If you find this project useful, [please star ⭐️ it on GitHub!](https://github.com/jowilf/starlette-admin)

## Features

- CRUD any data with ease
- Automatic form validation
- Advanced table widget with [Datatables](https://datatables.net/)
- Search and filtering
- Search highlighting
- Multi-column ordering
- Export data to CSV/EXCEL/PDF and Browser Print
- Authentication
- Authorization
- Manage Files
- Custom views
- Custom batch actions
- Supported ORMs
    * [SQLAlchemy](https://www.sqlalchemy.org/)
    * [SQLModel](https://sqlmodel.tiangolo.com/)
    * [MongoEngine](http://mongoengine.org/)
    * [ODMantic](https://github.com/art049/odmantic/)
    * Custom
      backend ([doc](https://jowilf.github.io/starlette-admin/advanced/base-model-view/), [example](https://github.com/jowilf/starlette-admin/tree/main/examples/custom-backend))
- Internationalization

## Installation

### PIP

```shell
$ pip install starlette-admin
```

### Poetry

```shell
$ poetry add starlette-admin
```

## Example

This is a simple example with SQLAlchemy model

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


# Define your model
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)


Base.metadata.create_all(engine)

app = Starlette()  # FastAPI()

# Create admin
admin = Admin(engine, title="Example: SQLAlchemy")

# Add view
admin.add_view(ModelView(Post))

# Mount admin to your app
admin.mount_to(app)
```

Access your admin interface in your browser at [http://localhost:8000/admin](http://localhost:8000/admin)

## Third party

*starlette-admin* is built with other open source projects:

- [Tabler](https://tabler.io/)
- [Datatables](https://datatables.net/)
- [jquery](https://jquery.com/)
- [Select2](https://select2.org/)
- [flatpickr](https://flatpickr.js.org/)
- [moment](http://momentjs.com/)
- [jsoneditor](https://github.com/josdejong/jsoneditor)
- [fontawesome](https://fontawesome.com/)
- [TinyMCE](https://www.tiny.cloud/)

## Contributing

Contributions are welcome and greatly appreciated! Before getting started, please read
[our contribution guidelines](https://github.com/jowilf/starlette-admin/blob/main/CONTRIBUTING.md)
