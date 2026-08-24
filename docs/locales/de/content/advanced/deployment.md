---
title: Deployment
description: Bewährte Methoden für das sichere und effiziente Deployen Ihrer FastAPI-
  und starlette-admin-Anwendung in die Produktion.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Das Betreiben des Admin-Panels hinter einem Reverse Proxy ändert zwei Dinge, die Sie in der lokalen Entwicklung sonst ignorieren können: Der Secret Key muss über Worker-Prozesse hinweg stabil sein, und generierte URLs müssen HTTPS widerspiegeln, obwohl Ihre App vom Proxy nur plain HTTP sieht.

!!! note "Framework-spezifische Deployment-Guides"
    Diese Seite behandelt nur, was spezifisch für `Admin` ist. Für die zugrunde liegende Anwendung und den ASGI Server siehe:

    * **FastAPI:** [FastAPI Deployment-Dokumentation](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Uvicorn Deployment-Dokumentation](https://www.uvicorn.org/deployment/)

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

```shell title="Betrieb hinter einem Reverse Proxy"
uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
```

## Secret Key

`Admin` generiert beim Start einen zufälligen `secret_key`, wenn Sie keinen übergeben. Das ist für einen einzelnen lokalen Prozess in Ordnung, aber jeder Worker-Prozess generiert seinen eigenen Key unabhängig, sodass ein von einem Worker signiertes CSRF-Token auf einem anderen nicht validiert wird. Setzen Sie `secret_key` aus einer Umgebungsvariable, bevor Sie mehr als einen Prozess ausführen. Unter [Sicherheit](../user-guide/security.md) finden Sie das vollständige Multi-Worker-Fehlerszenario und wie der Key verwendet wird.

## Reverse Proxy und HTTPS

`Admin` baut jeden internen Link (Listenseiten, Editierformulare, Exporte, den `/static` Mount, hochgeladene Dateien, die über `/_files/...` bereitgestellt werden), indem es `request.url_for(...)` aufruft, was dessen Scheme aus dem eingehenden Request ableitet. Wenn ein Proxy wie Nginx, Caddy oder Traefik TLS terminiert und plain HTTP an Ihre App weiterleitet, kann Starlette nicht erkennen, dass der ursprüngliche Request HTTPS war, es sei denn, der Proxy sendet `X-Forwarded-Proto` und Ihr ASGI Server vertraut ihm. Lassen Sie das unkonfiguriert, degradieren generierte Links zu `http://`, was Browser blockieren oder umschreiben, wenn die Seite selbst über HTTPS geladen wurde.

Beheben Sie das an zwei Stellen:

1. **Der Proxy** leitet den Header weiter:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** vertraut ihm, über `--proxy-headers` plus `--forwarded-allow-ips`, mit der IP des Proxys (oder `'*'`, wenn der Proxy nur aus Ihrem Netzwerk heraus erreichbar ist):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorns `uvicorn.workers.UvicornWorker` liest dieselben zwei Einstellungen aus `--forwarded-allow-ips`. Die vollständigen Optionen für Process Manager finden Sie in [Uvicorns Deployment-Dokumentation](https://www.uvicorn.org/deployment/).

!!! warning
    `--forwarded-allow-ips='*'` vertraut weitergeleiteten Headern aus **jeder** Quelle. Verwenden Sie es nur, wenn die App ausschließlich über Ihren Proxy erreichbar ist, etwa wenn sie an ein privates Netzwerk oder einen Unix Socket gebunden ist. Ist die App direkt erreichbar, beschränken Sie die Einstellung auf die tatsächliche IP des Proxys. Andernfalls kann ein Client `X-Forwarded-Proto` und `X-Forwarded-For` direkt fälschen.

## Statische Assets

Das CSS und JS des Admin-Panels werden im `starlette_admin` Paket mitgeliefert, und `Admin` stellt sie selbst über einen `/static` Mount unter `base_url` bereit, statt von einem separaten statischen Host. Mit `static_dir` können Sie lediglich einzelne Dateien überschreiben (siehe [Templates](templates.md)), es verlagert das Ausliefern der Assets nicht aus Ihrem App-Prozess heraus. Es gibt keine integrierte Option, diese Assets von einem CDN bereitzustellen. Wenn Sie eine brauchen, fügen Sie stattdessen auf der Proxy-Ebene eine cache-freundliche `Cache-Control`-Regel für `{base_url}/static/*` hinzu.

Hochgeladene Dateien sind anders: `LocalStorage` stellt sie ebenfalls durch die App bereit (`/_files/{storage}/{path}`, sodass die Auth-Middleware weiterhin greift), aber `S3Storage` und andere Remote-Backends können direkt vom Provider ausliefern. Siehe [Dateispeicher](../user-guide/file-storage.md).

---

## Was kommt als Nächstes

* **[Sicherheit](../user-guide/security.md):** Die `secret_key` Multi-Worker-Falle im Detail, plus alles andere, was die integrierten Schutzmechanismen abdecken und was nicht.
* **[Authentifizierung](../user-guide/auth.md):** Schränken Sie den Zugriff auf das Admin-Panel ein, bevor es in der Produktion erreichbar ist.
* **[Dateispeicher](../user-guide/file-storage.md):** Konfiguration von `S3Storage` und anderen Remote-Backends.
