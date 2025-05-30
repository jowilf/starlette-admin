# Beanie integration example

To run this example:

1. Clone the repository::

```shell
git clone https://github.com/jowilf/starlette-admin.git
cd starlette-admin
```

2. Create and activate a virtual environment:

```shell
python3 -m venv env
source env/bin/activate
```

3. Install requirements

```shell
pip install -r 'examples/beanie/requirements.txt'
```

4. Setup Database Connection
```shell
export MONGO_URI="mongodb://localhost:27017"
```

5. Run the application:

```shell
uvicorn examples.beanie.app:app
```
