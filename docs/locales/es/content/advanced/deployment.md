---
title: Despliegue
description: Buenas prácticas para desplegar su aplicación FastAPI y starlette-admin
  en producción de forma segura y eficiente.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# Despliegue

Ejecutar el panel de administración detrás de un proxy inverso cambia dos cosas que puede ignorar en el desarrollo local: la clave secreta debe ser estable entre los procesos worker, y las URL generadas deben reflejar HTTPS aunque su aplicación solo reciba HTTP sin cifrar desde el proxy.

!!! note "Guías de despliegue específicas del framework"
    Esta página cubre únicamente lo específico de `Admin`. Para la aplicación subyacente y el servidor ASGI, consulte:

    * **FastAPI:** [Documentación de despliegue de FastAPI](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Documentación de despliegue de Uvicorn](https://www.uvicorn.org/deployment/)

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

## Clave secreta

`Admin` genera una `secret_key` aleatoria al arrancar cuando usted no proporciona una. Esto es aceptable para un único proceso local, pero cada proceso worker genera su propia clave de forma independiente, por lo que un token CSRF firmado por un worker no se validará en otro. Defina `secret_key` mediante una variable de entorno antes de ejecutar más de un proceso. Consulte [Seguridad](../user-guide/security.md) para conocer en detalle el modo de fallo con múltiples workers y cómo se utiliza la clave.

## Proxy inverso y HTTPS

`Admin` construye cada enlace interno (páginas de lista, formularios de edición, exportaciones, el montaje `/static`, los archivos subidos servidos a través de `/_files/...`) llamando a `request.url_for(...)`, que deriva el esquema de la solicitud entrante. Cuando un proxy como Nginx, Caddy o Traefik termina TLS y reenvía HTTP sin cifrar a su aplicación, Starlette no puede saber que la solicitud original era HTTPS a menos que el proxy envíe `X-Forwarded-Proto` y su servidor ASGI confíe en él. Si deja esto sin configurar, los enlaces generados degradan a `http://`, lo cual los navegadores bloquean o reescriben cuando la página misma se cargó por HTTPS.

Corrija esto en dos lugares:

1. **El proxy** reenvía la cabecera:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** confía en ella, mediante `--proxy-headers` junto con `--forwarded-allow-ips` indicando la IP del proxy (o `'*'` si el proxy solo es accesible desde dentro de su red):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

El `uvicorn.workers.UvicornWorker` de Gunicorn lee estas dos mismas opciones de `--forwarded-allow-ips`. Consulte la [documentación de despliegue de Uvicorn](https://www.uvicorn.org/deployment/) para ver el conjunto completo de opciones para gestores de procesos.

!!! warning
    `--forwarded-allow-ips='*'` confía en las cabeceras reenviadas de **cualquier** origen. Úselo únicamente cuando la aplicación sea inaccesible salvo a través de su proxy, por ejemplo cuando está vinculada a una red privada o a un socket Unix. Si la aplicación es directamente accesible, restrinja esta opción a la IP real del proxy. De lo contrario, un cliente puede falsificar `X-Forwarded-Proto` y `X-Forwarded-For` directamente.

## Recursos estáticos

Los CSS y JS del panel de administración se incluyen dentro del paquete `starlette_admin`, y `Admin` los sirve él mismo mediante un montaje `/static` bajo `base_url` en lugar de hacerlo desde un host estático separado. `static_dir` solo permite sobrescribir archivos individuales (consulte [Plantillas](templates.md)); no traslada el servicio de recursos fuera del proceso de su aplicación. No existe una opción integrada para servir estos recursos desde un CDN. Si necesita una, añada en la capa del proxy una regla de `Cache-Control` favorable al almacenamiento en caché para `{base_url}/static/*`.

Los archivos subidos son distintos: `LocalStorage` también los sirve a través de la aplicación (`/_files/{storage}/{path}`, de modo que el middleware de autenticación sigue aplicándose), pero `S3Storage` y otros backends remotos pueden servirlos directamente desde el proveedor. Consulte [Almacenamiento de archivos](../user-guide/file-storage.md).

---

## Próximos pasos

* **[Seguridad](../user-guide/security.md):** El problema de la `secret_key` con múltiples workers en detalle, además de todo lo que las protecciones integradas cubren y no cubren.
* **[Autenticación](../user-guide/auth.md):** Restrinja el acceso al panel de administración antes de que sea accesible en producción.
* **[Almacenamiento de archivos](../user-guide/file-storage.md):** Configuración de `S3Storage` y otros backends remotos.
