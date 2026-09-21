---
title: Sécurité
description: Découvrez les fonctionnalités de sécurité intégrées à starlette-admin,
  notamment la protection CSRF, la sécurité des téléversements de fichiers et le contrôle
  d'accès.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# Sécurité

`starlette-admin` inclut des garde-fous contre les risques liés à l'exploitation d'un panneau d'administration. La protection contre la falsification de requête intersites (CSRF) ainsi que les limites sur la taille des charges utiles d'export et d'import sont actives dès l'instanciation de la classe `Admin`.

Ces valeurs par défaut renforcent l'interface contre les attaques courantes, mais ne remplacent pas les mesures de sécurité standard du déploiement. Vous restez responsable de la sécurité de la couche transport (HTTPS/TLS), du contrôle d'accès réseau, de l'authentification des utilisateurs (voir [Authentication](auth.md)), des mises à jour des dépendances et des revues de sécurité. Cette page présente les protections automatiques, celles que vous configurez, ainsi que le paramètre `secret_key` dont vous avez besoin en production.

## Ce que vous obtenez automatiquement

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

Même sans aucun paramètre de sécurité, l'instance d'administration se défend contre plusieurs vulnérabilités courantes :

* **Protection CSRF :** active sur chaque formulaire et chaque appel jQuery AJAX, y compris les actions sur les lignes et les boîtes de dialogue de confirmation.
* **Messages flash :** transportés dans un cookie signé, ce qui vous dispense de `SessionMiddleware`.
* **Assainissement des noms de fichiers :** appliqué à tout téléversement de fichier passant par un backend de stockage.
* **Vérification du contenu des images :** valide les téléversements `ImageField` au niveau des octets avec Pillow, lorsque celui-ci est installé.
* **Limites d'export :** plafonnées à 100 000 lignes par requête, afin de prévenir l'épuisement des ressources et les dénis de service.
* **Limites d'import :** plafonnées à 10 Mo par requête, afin de limiter l'épuisement de la mémoire.

Une protection supplémentaire est disponible mais désactivée par défaut : l'échappement qui prévient l'injection de formules dans les feuilles de calcul lors des exports CSV et tableur (XLSX, XLS, ODS). Voir [Injection de formules](#formula-injection).

Les sections ci-dessous expliquent ces protections et comment ajuster les seuils que vous contrôlez.

## La clé secrète

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

La `secret_key` est la racine cryptographique utilisée pour signer deux cookies : le jeton CSRF et le cookie des messages flash. Les deux reposent sur [itsdangerous](https://itsdangerous.palletsprojects.com/) : les clients peuvent lire ces cookies, mais ne peuvent ni forger ni altérer leur contenu sans la clé.

!!! warning "Définissez toujours une clé secrète explicite en production"
    Si vous omettez `secret_key`, l'instance `Admin` génère une clé aléatoire au démarrage et émet un `UserWarning`. C'est acceptable pour une démonstration locale, mais cela casse dans un déploiement multi-workers. Lorsque vous exécutez plusieurs workers, comme avec `uvicorn --workers 4`, Gunicorn ou plusieurs conteneurs, chaque processus génère sa propre clé. Un jeton CSRF signé par le worker qui a servi le formulaire échoue alors à la validation lorsqu'un autre worker traite la soumission, ce qui produit des erreurs de jeton CSRF invalide sur une fraction apparemment aléatoire des requêtes. Définissez explicitement `secret_key` avant de passer à l'échelle au-delà d'un seul processus.

## Protection CSRF

`CSRFMiddleware` utilise un motif de cookie à double soumission signé pour prévenir la falsification de requête intersites. Il émet un cookie `starlette_admin_csrftoken` sur les méthodes HTTP sûres (`GET`, `HEAD`, `OPTIONS` et `TRACE`). Pour les requêtes mutantes, il valide ce cookie contre soit un en-tête `X-CSRFToken`, soit un champ de formulaire masqué `csrftoken`.

Chaque modèle intégré du back-office (`create`, `edit` et `login`) affiche le champ masqué pour vous :

```jinja
{{ csrf_input(request) }}

```

Le JavaScript fourni attache également cet en-tête à chaque appel jQuery AJAX ; les actions sur les lignes et les autres interactions asynchrones sont donc protégées sans code supplémentaire. N'appelez vous-même `csrf_input(request)` que lorsque vous construisez des formulaires personnalisés en dehors des modèles par défaut. Voir [Custom Views](custom-views.md).

## Téléversement de fichiers

Tout téléversement passant par un backend de [stockage](file-storage.md) est assaini avec `secure_filename`. Les composants de chemin permettant la traversée de répertoires sont supprimés, et les caractères extérieurs à `[A-Za-z0-9_.-]` deviennent des underscores (`_`). Vous ne pouvez pas désactiver ce comportement.

Définissez les restrictions de type et de taille de contenu champ par champ avec `accept` et `max_size` :

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Sans elles, un `FileField` accepte n'importe quel type et taille de fichier. `ImageField` fait exception : il utilise par défaut `accept="image/*"`, et lorsque Pillow est installé, il ajoute un validateur en amont qui ouvre le téléversement avec `PIL.Image` pour vérifier que les octets décodent bien comme une image, plutôt que de se fier aux métadonnées fournies par le navigateur.

!!! important "Appliquez les limites de taille des requêtes au niveau du serveur web"
    Ne vous fiez pas uniquement à `max_size`. Cette vérification au niveau applicatif n'intervient qu'après réception complète de la charge utile de la requête par le serveur. Pour prévenir les attaques par déni de service (DoS), plafonnez la taille du corps de la requête dans la configuration de votre serveur web, comme `client_max_body_size` sous NGINX ou le paramètre équivalent de votre répartiteur de charge.

!!! warning "Extensions de fichiers et en-têtes Content-Type peuvent être falsifiés"
    L'attribut `accept` repose sur l'extension du nom de fichier et sur l'en-tête `Content-Type` fourni par le navigateur, et un attaquant peut falsifier les deux. Un fichier ressemblant à `invoice.pdf` peut transporter une charge exécutable.

    Pour les fichiers autres que des images, associez `accept` à un validateur personnalisé qui inspecte les magic bytes du fichier. Des bibliothèques telles que [`filetype`](https://github.com/h2non/filetype.py) et [`python-magic`](https://github.com/ahupp/python-magic) vérifient le format réel du fichier :

    ```python
    import filetype
    from starlette.datastructures import UploadFile
    from starlette.requests import Request
    from starlette_admin.fields import BaseField

    ALLOWED_DOCUMENT_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }


    def validate_document_type(
        request: Request, field: BaseField, upload: UploadFile, form_values: dict
    ) -> None:
        upload.file.seek(0)
        try:
            header = upload.file.read(2048)
            kind = filetype.guess(header)
            detected = kind.mime if kind else "application/octet-stream"
        finally:
            upload.file.seek(0)

        if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
            raise ValueError(
                f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
            )
    ```

    Appliquez le validateur avec `FileField(..., validators=[validate_document_type])`. Pour une implémentation complète, voir [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

## Limites d'export

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribut | Valeur par défaut | Description |
| --- | --- | --- |
| `max_rows` | `100_000` | Nombre maximal de lignes par requête d'export. Au-delà de la limite, un message flash d'erreur s'affiche et l'utilisateur est ramené à la vue en liste. Définissez `None` pour supprimer la limite. |
| `restrict_url_download` | `True` | S'applique aux références de fichiers exclusivement par URL. Restreint l'archive ZIP d'export aux fichiers dont l'origine correspond au `base_url` du back-office. |
| `max_download_size` | `20 MB` | Taille maximale d'un téléchargement par URL inclus dans une archive ZIP d'export. Les fichiers plus volumineux sont ignorés et journalisés avec un avertissement. |
| `safe_download_url` | `None` | Une fonction de rappel personnalisée de signature `(url, request) -> str`. |

Pour savoir comment l'archive ZIP est construite, voir [Export & Import](export-import.md).

### Injection de formules {#formula-injection}

Les logiciels tableurs interprètent toute valeur de cellule commençant par `=`, `+`, `-` ou `@` comme une formule. Si un utilisateur non fiable enregistre une charge utile telle que `=HYPERLINK(...)` dans un champ exporté, l'application tableur l'exécute lorsqu'un administrateur ouvre le fichier. On parle alors d'injection CSV, ou d'injection de formules.

Comme les valeurs exportées sont écrites exactement telles qu'elles sont stockées dans la base de données, l'échappement des formules est **désactivé par défaut**. L'exporteur CSV et les exporteurs Tablib (`xlsx`, `xls` et `ods`) acceptent tous un paramètre `escape_formulas`. Lorsque vous l'activez, toute chaîne commençant par un caractère déclencheur se voit préfixer une apostrophe simple (`'`), ce qui force l'application à restituer la valeur comme du texte brut.

!!! warning "Activez l'échappement des formules pour les données saisies par les utilisateurs"
    Si un compte autre qu'administrateur peut écrire des données dans un champ exporté, définissez `escape_formulas=True`. Sans cela, des valeurs contrôlées par un attaquant peuvent exécuter des commandes système ou exfiltrer des données dès qu'une personne ouvre le fichier localement.

Pour activer l'échappement, remplacez la chaîne de format par une instance d'exporteur explicite :

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter, TablibExporter


class ProductView(ModelView):
    exporters = [
        CsvExporter(escape_formulas=True),
        TablibExporter("xlsx", escape_formulas=True),
        "json",
    ]
```

## Limites d'import

```python
from starlette_admin.importers import ImportConfig

admin = Admin(
    engine,
    title="My Admin",
    import_config=ImportConfig(
        max_upload_size=5 * 1024 * 1024,
        max_rows=50_000,
    ),
)
```

| Attribut | Valeur par défaut | Description |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | Vérifié dès l'arrivée de la requête, avant toute analyse. |
| `max_rows` | `100_000` | Nombre maximal de lignes par requête d'import. Le back-office compte la charge utile lors d'un pré-traitement et rejette un fichier trop volumineux avec une réponse HTTP 400 avant de créer le moindre enregistrement en base de données. Définissez `None` pour supprimer la limite. |

L'import refuse catégoriquement les archives ZIP, ce qui écarte le risque d'attaques par bombe ZIP sur ce endpoint. `FileField` et `ImageField` sont également exclus des imports groupés, car ils ont `exclude_from_import=True` par défaut ; les utilisateurs joignent donc les fichiers un par un via les formulaires de création ou d'édition.

## Ce que cette page ne couvre pas

Les protections intégrées traitent les risques présents dans le code du back-office. Elles ne sécurisent pas votre architecture dans son ensemble. Ces mesures opérationnelles sortent du périmètre de `starlette-admin` et demeurent de votre responsabilité :

* **Sécurité du transport :** servez le back-office en HTTPS. Les cookies CSRF et flash sont signés, mais non chiffrés ; toute personne interceptant du trafic HTTP en clair peut donc les lire.
* **Authentification et autorisation :** l'instance `Admin` est publique tant que vous n'y avez pas attaché un `AuthProvider`. Sans lui, chaque endpoint et chaque route reste ouvert. Voir [Authentication](auth.md).
* **Exposition réseau :** si le panneau d'administration n'a pas besoin d'être accessible publiquement, placez-le derrière un pare-feu, un VPN ou une liste blanche d'adresses IP.
* **Hygiène des dépendances :** surveillez les avis de sécurité et maintenez `starlette-admin`, Starlette, votre pilote ORM et le reste de vos dépendances à jour.
* **Actions post-authentification :** la protection CSRF et la validation des téléversements ne limitent pas ce qu'un utilisateur connecté peut faire. Le contrôle d'accès fin provient entièrement des vérifications de permissions que vous écrivez dans `is_accessible`, `can_create`, `can_edit` et `can_delete`. Voir [Authentication](auth.md).

Considérez cette page comme un guide de configuration du package, et non comme une checklist pour sécuriser l'ensemble de votre déploiement de production.

---

## Pour aller plus loin

* **[Export & Import](export-import.md) :** la fenêtre d'export, le cycle de vie de l'aperçu d'import et la structure de l'archive ZIP.
* **[File Storage](file-storage.md) :** modèles de configuration des backends de stockage pour `FileField` et `ImageField`.
* **[Authentication](auth.md) :** comment `secret_key` conditionne les sessions de connexion et les vérifications CSRF une fois un fournisseur d'authentification ajouté.
