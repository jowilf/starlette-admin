SQLAlchemy model with Pydantic validation example.

To run this example:

1. Clone the repository:

```shell
git clone https://github.com/jowilf/starlette-admin.git
cd starlette-admin
```

2. Create and activate a virtual environment:

```shell
python3 -m venv env
source env/bin/activate
```

3. Install requirements:

```shell
pip install -r 'examples/sqla-pydantic/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.sqla-pydantic.app:app
```
