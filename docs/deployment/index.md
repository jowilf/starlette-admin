# Deployment

Whether you're using Starlette-Admin with FastAPI or Starlette, there are already well-documented resources to guide you
through the deployment process. It is strongly recommended to refer to these resources as they offer detailed
information and best practices:

* [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
* [Uvicorn Deployment Documentation](https://www.uvicorn.org/deployment)

However, When running your application behind a proxy server such as Traefik or Nginx, you may encounter an
issue where static files are not rendered as HTTPS links.
To address this issue, follow the steps below:

1. Ensure that your proxy server is properly configured to handle HTTPS traffic.
2. When starting your application with Uvicorn, include the `--forwarded-allow-ips` and `--proxy-headers` options.
   These options enable Uvicorn to correctly handle forwarded headers from the proxy server.

```shell title="Example"
uvicorn app.main:app --forwarded-allow-ips='*' --proxy-headers
```

If you cannot modify your proxy (for example, running your FastAPI application in Cloud Run), you will have to enable middleware to properly authenticate the HTTP links. This is addressed as below:

```shel title="Example"
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class CloudProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/healthz", "/"]:
            return await call_next(request)

        forwarded_proto = request.headers.get("X-Forwarded-Proto")

        if forwarded_proto == "https":
            request.scope["scheme"] = "https"

        return await call_next(request)

app.add_middleware(CloudProxyMiddleware)
```

This middleware will break the application during local hosting however, so only activate it in the production environment as shown above.
