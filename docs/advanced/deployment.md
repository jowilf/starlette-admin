# Deployment

Running the admin behind a reverse proxy changes two things you can otherwise ignore in local development: the secret key must be stable across worker processes, and generated URLs must reflect HTTPS even though your app only ever sees plain HTTP from the proxy.

```python
import os

from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine(os.environ["DATABASE_URL"])
app = Starlette()

admin = Admin(
    engine,
    title="My Admin",
    base_url="/admin",
    secret_key=os.environ["ADMIN_SECRET_KEY"],
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

```shell title="Running behind a reverse proxy"
uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
```

## Secret key

`Admin` generates a random `secret_key` at startup when you don't pass one. That's fine for a single local process, but every worker process would generate its own key independently, so a CSRF token signed by one worker won't validate on another. Set `secret_key` from an environment variable before running more than one process. See [Security](../user-guide/security.md) for the full multi-worker failure mode and how the key is used.

## Reverse proxy and HTTPS

`Admin` builds every internal link (list pages, edit forms, exports, the `/static` mount, uploaded files served through `/_files/...`) by calling `request.url_for(...)`, which derives its scheme from the incoming request. When a proxy such as Nginx, Caddy, or Traefik terminates TLS and forwards plain HTTP to your app, Starlette has no way to know the original request was HTTPS unless the proxy sends `X-Forwarded-Proto` and your ASGI server is told to trust it. Left unconfigured, generated links downgrade to `http://`, which browsers block or rewrite when the page itself was loaded over HTTPS.

Fix this in two places:

1. **The proxy** forwards the header:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** trusts it, via `--proxy-headers` plus `--forwarded-allow-ips` naming the proxy's IP (or `'*'` if the proxy is only reachable from inside your network):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorn's `uvicorn.workers.UvicornWorker` reads the same two settings from `--forwarded-allow-ips`; consult [Uvicorn's deployment docs](https://www.uvicorn.org/deployment/) for the full set of process-manager options.

!!! warning
    `--forwarded-allow-ips='*'` trusts forwarded headers from **any** source. Only use it when the app is unreachable except through your proxy (e.g. bound to a private network or a Unix socket). If the app is directly reachable, restrict it to the proxy's actual IP, otherwise a client can spoof `X-Forwarded-Proto`/`X-Forwarded-For` directly.

## Static assets

The admin's CSS and JS ship inside the `starlette_admin` package and are served by `Admin` itself through a `/static` mount under `base_url`, not from a separate static host. `static_dir` only lets you override individual files (see [Templates](templates.md)); it doesn't move asset serving off your app process. There's no built-in option to serve these from a CDN, if you need that, put a cache-friendly `Cache-Control` rule for `{base_url}/static/*` at the proxy layer instead.

Uploaded files are different: `LocalStorage` serves them through the app too (`/_files/{storage}/{path}`, so auth middleware still applies), but `S3Storage` and other remote backends can serve directly from the provider. See [File Storage](../user-guide/file-storage.md).

---

## What's next

* [Security](../user-guide/security.md): the `secret_key` multi-worker footgun in full, plus everything else the built-in protections do and don't cover
* [Authentication](../user-guide/auth.md): gate access to the admin before it's reachable in production
* [File Storage](../user-guide/file-storage.md): configuring `S3Storage` and other remote backends
