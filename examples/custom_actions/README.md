This example shows how to use custom batch actions.

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

3. Install requirements

```shell
pip install -r 'examples/custom_actions/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.custom_actions.app:app
```
