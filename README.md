# starlette-admin

*An extensible administrative interface framework for FastAPI and Starlette applications.*

<p align="center">
<a href="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml">
    <img src="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml/badge.svg" alt="Tests">
</a>
<a href="https://codecov.io/gh/jowilf/starlette-admin">
    <img src="https://codecov.io/gh/jowilf/starlette-admin/branch/main/graph/badge.svg" alt="Coverage">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://badge.fury.io/py/starlette-admin.svg" alt="PyPI version">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://img.shields.io/pypi/pyversions/starlette-admin?color=2334D058" alt="Python versions">
</a>
</p>

![Admin panel](./docs/assets/images/list-preview.png)

## Installation
```sh
# Using uv
uv add starlette-admin

# Using pip
pip install starlette-admin
```

## Quickstart

Get a fully functional administrative dashboard up and running in minutes. This example demonstrates an integration with FastAPI and SQLAlchemy.

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Run with `fastapi dev` and open [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

## Features

- Generated CRUD pages for your models
- Pagination, sorting, search, and shareable URLs
- Nested AND/OR filter builder
- Inline editing for related models
- Bulk actions and custom row actions
- CSV, Excel, JSON, and PDF export
- CSV, JSON and Excel import with dry-run validation
- Local and S3-compatible file storage (Amazon S3, MinIO, ...)
- Event hooks before and after CRUD operations
- Pluggable authentication, storage, fields, actions, and model views
- Theme customization, dark mode, internationalization, and timezone support



## Supported ORMs & Backends

`starlette-admin` is built to be agnostic. It ships with built-in support for popular ORMs and databases:

| Backend | Package Path |
| --- | --- |
| **SQLAlchemy** | `starlette_admin.contrib.sqla` |
| **SQLModel** | `starlette_admin.contrib.sqlmodel` |
| **Tortoise ORM** | `starlette_admin.contrib.tortoise` |
| **Beanie (MongoDB)** | `starlette_admin.contrib.beanie` |
| **MongoEngine** | `starlette_admin.contrib.mongoengine` |
| **Custom Data Sources** | Subclass `BaseModelView` |

---

## Documentation & Resources

* **[Full Documentation](https://jowilf.github.io/starlette-admin)**
* **[Quickstart Guide](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)**
* **[User Guide](https://jowilf.github.io/starlette-admin/user-guide/views/)** (Covers views, fields, filters, actions, and auth)
* **[API Reference](https://jowilf.github.io/starlette-admin/api/admin/)**

## Live Demo

Explore the interface in action: **[starlette-admin-demo.jowilf.com](https://starlette-admin-demo.jowilf.com/)**

## Contributing

Contributions are always welcome! Whether it is reporting a bug, discussing improvements, or submitting a pull request, your input helps make this project better.

Please review our **[CONTRIBUTING.md](https://github.com/jowilf/starlette-admin/blob/main/CONTRIBUTING.md)** guidelines before opening a pull request.

## License

This project is licensed under the **MIT License**.
