---
title: Déploiement
description: Bonnes pratiques pour déployer votre application FastAPI et starlette-admin
  en production de manière sûre et efficace.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
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

Exécuter le panneau d'administration derrière un reverse proxy change deux choses que vous pouvez sinon ignorer en développement local : la clé secrète doit être stable entre les processus worker, et les URL générées doivent refléter HTTPS alors même que votre application ne voit que du HTTP simple provenant du proxy.

!!! note "Guides de déploiement spécifiques au framework"
    Cette page couvre uniquement ce qui est spécifique à `Admin`. Pour l'application sous-jacente et le serveur ASGI, consultez :

    * **FastAPI :** [Documentation de déploiement de FastAPI](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn :** [Documentation de déploiement d'Uvicorn](https://www.uvicorn.org/deployment/)

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

```shell title="Exécution derrière un reverse proxy"
uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
```

## Clé secrète

`Admin` génère une `secret_key` aléatoire au démarrage lorsque vous n'en passez pas. C'est acceptable pour un processus local unique, mais chaque processus worker génère sa propre clé de manière indépendante, de sorte qu'un jeton CSRF signé par un worker ne sera pas validé par un autre. Définissez `secret_key` à partir d'une variable d'environnement avant d'exécuter plus d'un processus. Consultez [Sécurité](../user-guide/security.md) pour connaître le mode de défaillance complet en multi-worker et la manière dont la clé est utilisée.

## Reverse proxy et HTTPS

`Admin` construit chaque lien interne (pages de liste, formulaires d'édition, exportations, le montage `/static`, fichiers téléversés servis via `/_files/...`) en appelant `request.url_for(...)`, qui déduit son schéma de la requête entrante. Lorsqu'un proxy tel que Nginx, Caddy ou Traefik termine TLS et transmet du HTTP simple à votre application, Starlette ne peut pas savoir que la requête d'origine était en HTTPS, sauf si le proxy envoie `X-Forwarded-Proto` et que votre serveur ASGI lui fait confiance. Si vous laissez cela non configuré, les liens générés rétrogradent en `http://`, ce que les navigateurs bloquent ou réécrivent lorsque la page elle-même a été chargée en HTTPS.

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

2. **Uvicorn** lui fait confiance, via `--proxy-headers` plus `--forwarded-allow-ips` désignant l'adresse IP du proxy (ou `'*'` si le proxy n'est accessible que depuis l'intérieur de votre réseau) :

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Le `uvicorn.workers.UvicornWorker` de Gunicorn lit ces deux mêmes paramètres depuis `--forwarded-allow-ips`. Consultez [la documentation de déploiement d'Uvicorn](https://www.uvicorn.org/deployment/) pour l'ensemble complet des options de gestionnaire de processus.

!!! warning
    `--forwarded-allow-ips='*'` fait confiance aux en-têtes transmis provenant de **n'importe quelle** source. Ne l'utilisez que lorsque l'application est inaccessible autrement que par votre proxy, par exemple lorsqu'elle est liée à un réseau privé ou à un socket Unix. Si l'application est directement accessible, restreignez ce paramètre à l'adresse IP réelle du proxy. Sinon, un client peut usurper `X-Forwarded-Proto` et `X-Forwarded-For` directement.

## Ressources statiques

Les CSS et JS du panneau d'administration sont livrés dans le package `starlette_admin`, et `Admin` les sert lui-même via un montage `/static` sous `base_url` plutôt que depuis un hôte statique séparé. `static_dir` vous permet uniquement de remplacer des fichiers individuels (voir [Templates](templates.md)), il ne déplace pas la diffusion des ressources hors du processus de votre application. Il n'existe aucune option intégrée pour servir ces ressources depuis un CDN. Si vous en avez besoin, ajoutez plutôt une règle `Cache-Control` adaptée à la mise en cache pour `{base_url}/static/*` au niveau du proxy.

Les fichiers téléversés sont différents : `LocalStorage` les sert également via l'application (`/_files/{storage}/{path}`, de sorte que le middleware d'authentification s'applique toujours), mais `S3Storage` et les autres backends distants peuvent les servir directement depuis le fournisseur. Consultez [Stockage de fichiers](../user-guide/file-storage.md).

---

## Et ensuite ?

* **[Sécurité](../user-guide/security.md) :** Le piège multi-worker de la `secret_key` en détail, ainsi que tout ce que les protections intégrées couvrent ou ne couvrent pas.
* **[Authentification](../user-guide/auth.md) :** Contrôlez l'accès au panneau d'administration avant qu'il ne soit accessible en production.
* **[Stockage de fichiers](../user-guide/file-storage.md) :** Configuration de `S3Storage` et des autres backends distants.
