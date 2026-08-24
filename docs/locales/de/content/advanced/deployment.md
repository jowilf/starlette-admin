---
title: Deployment
description: Best Practices für den sicheren und effizienten Einsatz Ihrer FastAPI-
  und starlette-admin-Anwendung in der Produktion.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# Deployment

Der Betrieb des Admin-Interfaces hinter einem Reverse Proxy verändert zwei Dinge, die Sie in der lokalen Entwicklung sonst ignorieren können: Der Secret Key muss über alle Worker-Prozesse hinweg stabil sein, und generierte URLs müssen HTTPS widerspiegeln, obwohl Ihre Anwendung vom Proxy ausschließlich plain HTTP sieht.

!!! note "Framework-spezifische Deployment-Anleitungen"
    Diese Seite behandelt nur das, was für `Admin` spezifisch ist. Für die zugrunde liegende Anwendung und den ASGI-Server siehe:

    * **FastAPI:** [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Uvicorn Deployment Documentation](https://www.uvicorn.org/deployment/)

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

## Secret Key

`Admin` erzeugt beim Start einen zufälligen `secret_key`, wenn Sie keinen übergeben. Das ist für einen einzelnen lokalen Prozess unproblematisch, aber jeder Worker-Prozess erzeugt seinen eigenen Key unabhängig voneinander – ein von einem Worker signiertes CSRF-Token wird daher auf einem anderen nicht validiert. Setzen Sie `secret_key` aus einer Umgebungsvariable, bevor Sie mehr als einen Prozess betreiben. Unter [Security](../user-guide/security.md) finden Sie das vollständige Fehlerbild bei mehreren Workern sowie eine Erläuterung, wie der Key verwendet wird.

## Reverse Proxy und HTTPS

`Admin` baut jeden internen Link (Listenansichten, Bearbeitungsformulare, Exporte, den `/static`-Mount, hochgeladene Dateien unter `/_files/...`) durch den Aufruf von `request.url_for(...)` auf, dessen Schema sich aus der eingehenden Anfrage ableitet. Wenn ein Proxy wie Nginx, Caddy oder Traefik TLS terminiert und plain HTTP an Ihre Anwendung weiterleitet, kann Starlette nicht erkennen, dass die ursprüngliche Anfrage per HTTPS erfolgte – es sei denn, der Proxy sendet `X-Forwarded-Proto` und Ihr ASGI-Server vertraut diesem Header. Lassen Sie dies unkonfiguriert, degradieren generierte Links zu `http://`, was Browser blockieren oder umschreiben, wenn die Seite selbst über HTTPS geladen wurde.

Beheben Sie dies an zwei Stellen:

1. **Der Proxy** leitet den Header weiter:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** vertraut ihm, mittels `--proxy-headers` plus `--forwarded-allow-ips` mit der IP des Proxys (oder `'*'`, wenn der Proxy nur aus Ihrem internen Netzwerk erreichbar ist):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorns `uvicorn.workers.UvicornWorker` liest dieselben beiden Einstellungen aus `--forwarded-allow-ips`. Die vollständige Palette der Optionen für Process Manager finden Sie in [Uvicorn's deployment docs](https://www.uvicorn.org/deployment/).

!!! warning
    `--forwarded-allow-ips='*'` vertraut weitergeleiteten Headern aus **jeder** Quelle. Verwenden Sie dies nur, wenn die Anwendung ausschließlich über Ihren Proxy erreichbar ist, etwa wenn sie an ein privates Netzwerk oder einen Unix-Socket gebunden ist. Ist die Anwendung direkt erreichbar, beschränken Sie die Einstellung auf die tatsächliche IP des Proxys. Andernfalls kann ein Client `X-Forwarded-Proto` und `X-Forwarded-For` direkt fälschen.

## Statische Assets

Das CSS und JS des Admin-Interfaces werden innerhalb des Pakets `starlette_admin` ausgeliefert, und `Admin` stellt sie selbst über einen `/static`-Mount unterhalb von `base_url` bereit statt über einen separaten statischen Host. Mit `static_dir` können Sie lediglich einzelne Dateien überschreiben (siehe [Templates](templates.md)); die Auslieferung der Assets wird damit nicht aus Ihrem Anwendungsprozess herausverlagert. Eine eingebaute Option, diese Assets über ein CDN bereitzustellen, gibt es nicht. Falls Sie dies benötigen, ergänzen Sie stattdessen eine Cache-freundliche `Cache-Control`-Regel für `{base_url}/static/*` auf der Proxy-Ebene.

Hochgeladene Dateien sind ein anderer Fall: `LocalStorage` stellt sie ebenfalls über die Anwendung bereit (`/_files/{storage}/{path}`, sodass Auth-Middleware weiterhin greift), während `S3Storage` und andere Remote-Backends sie direkt beim Provider ausliefern können. Siehe [File Storage](../user-guide/file-storage.md).

---

## Was kommt als Nächstes?

* **[Security](../user-guide/security.md):** Die `secret_key`-Falle bei mehreren Workern im Detail, dazu alles Weitere, was die eingebauten Schutzmechanismen abdecken – und was nicht.
* **[Authentication](../user-guide/auth.md):** Sperren Sie den Zugriff auf das Admin-Interface ab, bevor es in der Produktion erreichbar ist.
* **[File Storage](../user-guide/file-storage.md):** Konfiguration von `S3Storage` und anderen Remote-Backends.
