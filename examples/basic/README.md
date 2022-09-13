This example shows how you can easily extend BaseModelView to write you custom logic.

It used in memory database represented by a simple python dict object and which will be reset when you restart the server.

The SearchBuilder is disabled for this example, only full text search is available.

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
pip install -r 'examples/basic/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.basic.app:app
```
