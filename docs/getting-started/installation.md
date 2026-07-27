# Installation

Install **starlette-admin** using your preferred package manager.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin requires **Python 3.11 or later**.

The core package is backend agnostic. To build an admin interface for your application, install the appropriate integration for your data layer (such as SQLAlchemy, Beanie, MongoEngine, or Tortoise ORM) alongside the base package.

## Included dependencies

The base installation includes everything required to run the admin interface. No optional dependencies are installed by default.

| Dependency                                                     | Purpose                                          |
| -------------------------------------------------------------- | ------------------------------------------------ |
| [Starlette](https://www.starlette.io/)                         | ASGI framework that hosts the admin application  |
| [Jinja2](https://jinja.palletsprojects.com/)                   | Template engine for list, detail, and form pages |
| [python-multipart](https://github.com/Kludex/python-multipart) | Parses form submissions and file uploads         |
| [itsdangerous](https://itsdangerous.palletsprojects.com/)      | Signs cookies for CSRF tokens and flash messages                    |

Applications built with FastAPI require no additional integration because FastAPI is built on Starlette. Mount the admin on your existing FastAPI application.

## Optional dependencies

starlette-admin provides the following optional dependencies:

- `pdf`: PDF export ([reportlab](https://www.reportlab.com/)).
- `i18n`: Internationalization ([Babel](https://babel.pocoo.org/)).
- `tinymce`: Rich text editor support. Installs [nh3](https://nh3.readthedocs.io/), which sanitizes HTML submitted by `TinyMCEEditorField`.
- `s3`: S3-compatible object storage. Installs [aiobotocore](https://aiobotocore.readthedocs.io/) for asynchronous uploads to AWS S3 and compatible object storage services such as MinIO.

Install one or more optional dependencies together with starlette-admin:

=== "pip"

    ```bash
    # Install the `pdf` extra
    pip install "starlette-admin[pdf]"

    # Install multiple extras
    pip install "starlette-admin[i18n,pdf,s3]"
    ```

=== "uv"

    ```bash
    # Install the `excel` extra
    uv add "starlette-admin[excel]"

    # Install multiple extras
    uv add "starlette-admin[excel,pdf,s3]"
    ```

## Install from source

To use the latest unreleased changes, install directly from the GitHub repository.

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## What's next

- **[Quickstart](quickstart.md):** Build your first admin interface with real data.
- **[Concepts](concepts.md):** Learn the core architecture and design principles behind starlette-admin.
