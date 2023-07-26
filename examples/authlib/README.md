This example demonstrates how to secure your admin interface using OAuth2/OIDC (OpenID Connect).
In this example, we use Auth0 as the identity provider and Authlib as the OAuth2 client library.

Follow these steps to run the example:

1. Clone the repository:

```shell
git clone https://github.com/jowilf/starlette-admin.git
cd starlette-admin
```

2. Update the credentials in
   the [config.py](https://github.com/jowilf/starlette-admin/blob/main/examples/authlib/config.py) file:

```python
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")
```

Alternatively, you can set the credentials as environment variables.

3. Create and activate a virtual environment:

```shell
python3 -m venv env
source env/bin/activate
```

4. Install requirements:

```shell
pip install -r 'examples/authlib/requirements.txt'
```

5. Run the application:

```shell
uvicorn examples.authlib.app:app
```
