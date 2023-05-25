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
