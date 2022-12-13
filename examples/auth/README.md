This example shows how you can secure your admin interface with user authentication & authorization

Users:

- Admin
    - username: `admin`
    - password: `password`
    - Roles: Can do everything
- John Doe
    - username: `johndoe`
    - password: `password`
    - Roles: Can view, create and edit articles. He can also use `make_published` action
- Viewer
    - username: `viewer`
    - password: `password`
    - Roles: Can only view articles

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

3. Install requirements

```shell
pip install -r 'examples/auth/requirements.txt'
```

4. Run the application:

```shell
uvicorn examples.auth.app:app
```

The first time you run this example, a sample sqlite database gets populated automatically
