This example shows how you can easily use [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file)
to upload and validate files in your admin interface.

It uses local storage to save uploaded files, but you can easily switch to any
other [storage providers](https://libcloud.readthedocs.io/en/stable/storage/supported_providers.html) supported
by the [apache-libloud](https://github.com/apache/libcloud) library.

To run this example:

1. Clone the repository::

```shell
git clone https://github.com/jowilf/starlette-admin.git
cd starlette-admin
```

2. Create and activate a virtual environment::

```shell
python3 -m venv env
source env/bin/activate
```

3. Install requirements

```shell
pip install -r 'examples/sqla_files/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.sqla_files.app:app
```
