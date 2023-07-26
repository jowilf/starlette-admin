import os

DATABASE_FILE = "sample_db.sqlite"
ENGINE_URI = "sqlite:///" + DATABASE_FILE

SECRET = "1234567890"
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")
