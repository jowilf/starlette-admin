---
title: Déploiement
description: Bonnes pratiques pour déployer votre application FastAPI et starlette-admin
  en production de manière sûre et efficace.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# Déploiement

Exécuter l'admin derrière un reverse proxy change deux points que vous pouvez sinon ignorer en développement local : la secret key doit être stable entre les processus worker, et les URL générées doivent refléter HTTPS même si votre application ne voit jamais que du HTTP simple en provenance du proxy.

!!! note "Guides de déploiement spécifiques aux frameworks"
    Cette page couvre uniquement ce qui est spécifique à `Admin`. Pour l'application sous-jacente et le serveur ASGI, consultez :

    * **FastAPI :** [Documentation de déploiement FastAPI](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn :** [Documentation de déploiement Uvicorn](https://www.uvicorn.org/deployment/)

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

`Admin` génère une `secret_key` aléatoire au démarrage lorsque vous n'en fournissez pas. C'est acceptable pour un processus local unique, mais chaque processus worker génère sa propre clé de manière indépendante ; un jeton CSRF signé par un worker ne sera donc pas validable par un autre. Définissez `secret_key` à partir d'une variable d'environnement avant d'exécuter plusieurs processus. Consultez [Security](../user-guide/security.md) pour le détail complet des défaillances en mode multi-worker et pour comprendre comment la clé est utilisée.

## Reverse proxy et HTTPS

`Admin` construit chaque lien interne (pages de liste, formulaires d'édition, exports, le mount `/static`, fichiers téléversés servis via `/_files/...`) en appelant `request.url_for(...)`, dont le schéma est déduit de la requête entrante. Lorsqu'un proxy tel que Nginx, Caddy ou Traefik termine TLS et transmet du HTTP simple à votre application, Starlette ne peut pas savoir que la requête d'origine était en HTTPS, sauf si le proxy envoie `X-Forwarded-Proto` et que votre serveur ASGI lui fait confiance. Sans cette configuration, les liens générés rétrogradent en `http://`, ce que les navigateurs bloquent ou réécrivent lorsque la page elle-même a été chargée en HTTPS.

Corrigez cela à deux endroits :

1. **Le proxy** transmet l'en-tête :

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** lui fait confiance, via `--proxy-headers` accompagné de `--forwarded-allow-ips` désignant l'IP du proxy (ou `'*'` si le proxy n'est joignable que depuis l'intérieur de votre réseau) :

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Le worker `uvicorn.workers.UvicornWorker` de Gunicorn lit les deux mêmes paramètres depuis `--forwarded-allow-ips`. Consultez la [documentation de déploiement d'Uvicorn](https://www.uvicorn.org/deployment/) pour l'ensemble des options relatives aux gestionnaires de processus.

!!! warning
    `--forwarded-allow-ips='*'` fait confiance aux en-têtes transmis provenant de **n'importe quelle** source. N'utilisez cette option que si l'application est inaccessibile autrement que via votre proxy, par exemple lorsqu'elle est liée à un réseau privé ou à un socket Unix. Si l'application est directement accessible, restreignez ce paramètre à l'adresse IP réelle du proxy. Dans le cas contraire, un client peut usurper directement `X-Forwarded-Proto` et `X-Forwarded-For`.

## Fichiers statiques

Les CSS et JS de l'admin sont livrés au sein du package `starlette_admin`, et `Admin` les sert lui-même via un mount `/static` sous `base_url` plutôt que depuis un hôte statique distinct. Le paramètre `static_dir` permet uniquement de remplacer certains fichiers (voir [Templates](templates.md)), il ne déplace pas la distribution des assets hors du processus de votre application. Aucune option intégrée ne permet de servir ces fichiers depuis un CDN. Si vous en avez besoin, ajoutez plutôt une règle `Cache-Control` adaptée à la mise en cache pour `{base_url}/static/*` au niveau du proxy.

Les fichiers téléversés fonctionnent différemment : `LocalStorage` les sert également via l'application (`/_files/{storage}/{path}`, de sorte que le middleware d'authentification reste appliqué), mais `S3Storage` et autres backends distants peuvent être servis directement par le fournisseur. Consultez [File Storage](../user-guide/file-storage.md).

---

## Et ensuite ?

* **[Security](../user-guide/security.md) :** Le piège de la `secret_key` en multi-worker en détail, ainsi que tout ce que les protections intégrées couvrent — et ne couvrent pas.
* **[Authentication](../user-guide/auth.md) :** Contrôlez l'accès à l'admin avant qu'il ne soit accessible en production.
* **[File Storage](../user-guide/file-storage.md) :** Configuration de `S3Storage` et des autres backends distants.
