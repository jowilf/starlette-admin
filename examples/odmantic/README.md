This example shows how you can easily extend BaseModelView to use *Starlette-Admin*
with [odmantic](https://github.com/art049/odmantic)

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
pip install -r 'examples/odmantic/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.odmantic.app:app
```
