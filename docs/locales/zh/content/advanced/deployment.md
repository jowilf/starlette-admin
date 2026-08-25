---
title: 部署
description: 将 FastAPI 与 starlette-admin 应用安全高效地部署到生产环境的最佳实践。
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# 部署

在反向代理后面运行 admin 会带来两件在本地开发中通常可以忽略的事情：密钥必须在各个工作进程之间保持一致；生成的 URL 必须体现 HTTPS，即使应用从代理那里看到的始终只是纯 HTTP。

!!! note "框架特定的部署指南"
    本页只介绍特定于 `Admin` 的内容。关于底层应用和 ASGI 服务器，请参阅：

    * **FastAPI:** [FastAPI 部署文档](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Uvicorn 部署文档](https://www.uvicorn.org/deployment/)

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

## 密钥

如果不传入 `secret_key`，`Admin` 会在启动时生成一个随机值。这对单个本地进程没有问题，但每个工作进程都会独立生成自己的密钥，因此由某个工作进程签署的 CSRF 令牌无法在其他工作进程上通过验证。在运行多个进程之前，请从环境变量设置 `secret_key`。完整的多工作进程故障模式以及密钥的使用方式，请参见[安全](../user-guide/security.md)。

## 反向代理与 HTTPS

`Admin` 通过调用 `request.url_for(...)` 来构建每一个内部链接（列表页、编辑表单、导出、`/static` 挂载，以及通过 `/_files/...` 提供的上传文件），其协议取自传入的请求。当 Nginx、Caddy 或 Traefik 等代理终结 TLS 并将纯 HTTP 转发给应用时，Starlette 无法得知原始请求是 HTTPS，除非代理发送 `X-Forwarded-Proto` 并且你的 ASGI 服务器信任它。如果不做此配置，生成的链接会降级为 `http://`，而当页面本身是通过 HTTPS 加载时，浏览器会阻止或重写这些链接。

需要在两处修复：

1. **代理**转发该请求头：

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** 信任它：通过 `--proxy-headers` 加上指定代理 IP 的 `--forwarded-allow-ips`（如果代理只能从内部网络访问，则使用 `'*'`）：

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorn 的 `uvicorn.workers.UvicornWorker` 同样从 `--forwarded-allow-ips` 读取这两项设置。完整的进程管理器选项请参见 [Uvicorn 部署文档](https://www.uvicorn.org/deployment/)。

!!! warning
    `--forwarded-allow-ips='*'` 会信任来自**任意**来源的转发请求头。只有当应用除了通过代理之外无法被访问时才可使用它，例如应用绑定到私有网络或 Unix 套接字时。如果应用可以被直接访问，请将该设置限制为代理的实际 IP。否则，客户端可以直接伪造 `X-Forwarded-Proto` 和 `X-Forwarded-For`。

## 静态资源

admin 的 CSS 和 JS 随 `starlette_admin` 包一起发布，由 `Admin` 自己通过 `base_url` 下的 `/static` 挂载提供服务，而不是来自独立的静态主机。`static_dir` 仅允许覆盖个别文件（参见[模板](templates.md)），并不能把资源服务从你的应用进程中移走。没有内置选项可以从 CDN 提供这些资源。如有需要，请改为在代理层为 `{base_url}/static/*` 添加一条对缓存友好的 `Cache-Control` 规则。

上传文件的情况有所不同：`LocalStorage` 同样通过应用提供文件（路径为 `/_files/{storage}/{path}`，因此认证中间件仍然生效），但 `S3Storage` 及其他远程后端可以直接由服务提供商提供文件。参见[文件存储](../user-guide/file-storage.md)。

---

## 下一步

* **[安全](../user-guide/security.md)：** 完整讲解 `secret_key` 多工作进程陷阱，以及内置防护措施的各项覆盖与未覆盖之处。
* **[认证](../user-guide/auth.md)：** 在 admin 于生产环境中可被访问之前，为其设置访问门槛。
* **[文件存储](../user-guide/file-storage.md)：** 配置 `S3Storage` 及其他远程后端。
