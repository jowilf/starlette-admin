beanie document integration examples.

To run this example:

1. Clone the repository::

```shell
git clone https://github.com/jowilf/starlette-admin.git
cd starlette-admin
```

2. Create and activate a virtual environment:

* Linux:

```shell
python3 -m venv .venv
source env/bin/activate
```

* Windows

```shell
python -m venv .venv
.venv\Scripts\activate
```

3. Install requirements

```shell
pip install -r examples/beanie_has_many/requirements.txt
```

4. Start mongo

```shell
docker run -d -p 27017:27017 --name test-mongo mongo:latest
```

5. Run the application:

```shell
uvicorn examples.beanie_has_many.app_fastapi:app --reload
```
