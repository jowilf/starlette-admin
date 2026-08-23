---
title: Sécurité
description: Découvrez les fonctionnalités de sécurité intégrées de starlette-admin,
  notamment la protection CSRF, la sécurité des téléversements de fichiers et le contrôle
  d'accès.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Sécurité

`starlette-admin` inclut des protections contre les risques liés à l'exécution d'un panneau d'administration. La protection contre la falsification de requête intersite (CSRF) et les limites sur la taille des charges utiles d'exportation et d'importation sont actives dès que vous instanciez la classe `Admin`.

Ces valeurs par défaut renforcent l'interface contre les attaques courantes, mais elles ne remplacent pas une sécurité de déploiement standard. Vous restez responsable de la sécurité de la couche transport (HTTPS/TLS), du contrôle d'accès réseau, de l'authentification des utilisateurs (voir [Authentification](auth.md)), des mises à jour des dépendances et des revues de sécurité. Cette page présente les protections automatiques, celles que vous configurez, ainsi que le paramètre `secret_key` dont vous avez besoin en production.

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

* **Protection CSRF :** active sur chaque formulaire et chaque appel AJAX jQuery, y compris les actions de ligne et les boîtes de dialogue de confirmation.
* **Messages flash :** transportés dans un cookie signé, vous n'avez donc pas besoin de `SessionMiddleware`.
* **Assainissement des noms de fichiers :** appliqué à chaque téléversement de fichier qui passe par un backend de stockage.
* **Vérification du contenu des images :** valide les téléversements `ImageField` au niveau des octets avec Pillow, lorsqu'il est installé.
* **Limites d'exportation :** plafonnées à 100 000 lignes par requête, pour prévenir l'épuisement des ressources et le déni de service.
* **Limites d'importation :** plafonnées à 10 Mo par requête, pour limiter l'épuisement de la mémoire.

Une protection supplémentaire est disponible, mais désactivée par défaut : l'échappement qui prévient l'injection de formules dans les exports CSV et tableur (XLSX, XLS, ODS). Voir [Injection de formules](#injection-de-formules).

Les sections ci-dessous expliquent ces protections et comment ajuster les seuils que vous contrôlez.

## La clé secrète

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

La clé `secret_key` est la racine cryptographique pour signer deux cookies : le jeton CSRF et le cookie des messages flash. Les deux utilisent [itsdangerous](https://itsdangerous.palletsprojects.com/), si bien que les clients peuvent lire les cookies mais ne peuvent ni falsifier ni altérer la charge utile sans la clé.

!!! warning "Définissez toujours une clé secrète explicite en production"
    Si vous omettez `secret_key`, l'instance `Admin` génère une clé aléatoire au démarrage et émet un `UserWarning`. C'est acceptable pour une démonstration locale, mais cela casse dans les déploiements multi-workers. Lorsque vous exécutez plusieurs workers, tels que `uvicorn --workers 4`, Gunicorn ou plusieurs conteneurs, chaque processus génère sa propre clé. Un jeton CSRF signé par le worker ayant servi le formulaire échoue alors à la validation quand un autre worker traite la soumission, ce qui produit des erreurs de jeton CSRF invalide sur une fraction apparemment aléatoire des requêtes. Définissez `secret_key` explicitement avant de passer à l'échelle au-delà d'un seul processus.

## Protection CSRF

`CSRFMiddleware` utilise un motif de double soumission par cookie signé pour prévenir la falsification de requête intersite. Il émet un cookie `starlette_admin_csrftoken` sur les méthodes HTTP sûres (`GET`, `HEAD`, `OPTIONS` et `TRACE`). Pour les requêtes mutatrices, il valide ce cookie contre un en-tête `X-CSRFToken` ou un champ de formulaire masqué `csrftoken`.

Chaque template intégré du panneau d'administration (`create`, `edit` et `login`) affiche le champ masqué pour vous :

```jinja
{{ csrf_input(request) }}

```

Le JavaScript fourni attache également l'en-tête à chaque appel AJAX jQuery, si bien que les actions de ligne et les autres interactions asynchrones sont protégées sans code supplémentaire. Appelez vous-même `csrf_input(request)` uniquement lorsque vous créez des formulaires personnalisés en dehors des templates par défaut. Voir [Vues personnalisées](custom-views.md).

## Téléversement de fichiers

Chaque téléversement qui passe par un [backend de stockage](file-storage.md) est assaini avec `secure_filename`. Les composants de traversée de répertoires sont retirés, et les caractères en dehors de `[A-Za-z0-9_.-]` deviennent des traits de soulignement (`_`). Vous ne pouvez pas désactiver ce comportement.

Définissez des restrictions de type de contenu et de taille par champ avec `accept` et `max_size` :

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Sans elles, un `FileField` accepte n'importe quel type et taille de fichier. `ImageField` fait exception : il utilise par défaut `accept="image/*"`, et lorsque Pillow est installé, il ajoute un validateur qui ouvre le téléversement avec `PIL.Image` pour confirmer que les octets décodent bien comme une image, plutôt que de se fier aux métadonnées fournies par le navigateur.

!!! important "Appliquez des limites de taille de requête au niveau du serveur web"
    Ne comptez pas uniquement sur `max_size`. Cette vérification au niveau de l'application ne s'exécute qu'une fois que le serveur a reçu l'intégralité de la charge utile de la requête. Pour prévenir les attaques par déni de service (DoS), plafonnez la taille du corps de requête dans la configuration de votre serveur web, comme `client_max_body_size` dans NGINX ou le paramètre équivalent sur votre répartiteur de charge.

!!! warning "Les extensions de fichiers et les en-têtes Content-Type peuvent être falsifiés"
    L'attribut `accept` repose sur l'extension du nom de fichier et sur l'en-tête `Content-Type` fourni par le navigateur, et un attaquant peut falsifier les deux. Un fichier qui ressemble à `invoice.pdf` peut contenir une charge utile exécutable.

    Pour les fichiers autres que les images, associez `accept` à un validateur personnalisé qui inspecte les octets magiques du fichier. Des bibliothèques telles que [`filetype`](https://github.com/h2non/filetype.py) et [`python-magic`](https://github.com/ahupp/python-magic) vérifient le véritable format du fichier :

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

## Limites d'exportation

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribut | Valeur par défaut | Description |
| --- | --- | --- |
| `max_rows` | `100_000` | Nombre maximal de lignes par requête d'exportation. Au-delà de la limite, un message flash d'erreur s'affiche et l'utilisateur est ramené à la page de liste. Définissez `None` pour supprimer la limite. |
| `restrict_url_download` | `True` | S'applique aux références de fichiers par URL uniquement. Restreint l'archive ZIP d'exportation aux fichiers dont l'origine correspond au `base_url` du panneau d'administration. |
| `max_download_size` | `20 MB` | Taille maximale pour un téléchargement par URL uniquement empaqueté dans une archive ZIP d'exportation. Les fichiers plus volumineux sont ignorés et consignés avec un avertissement. |
| `safe_download_url` | `None` | Une fonction de rappel personnalisée avec la signature `(url, request) -> str`. |

Pour savoir comment l'archive ZIP est construite, voir [Exportation & Importation](export-import.md).

### Injection de formules

Les logiciels tableur traitent une valeur de cellule qui commence par `=`, `+`, `-` ou `@` comme une formule. Si un utilisateur non fiable enregistre une charge utile telle que `=HYPERLINK(...)` dans un champ exporté, l'application tableur l'exécute lorsqu'un administrateur ouvre le fichier. C'est ce qu'on appelle l'injection CSV, ou injection de formules.

Comme les valeurs exportées sont écrites exactement telles qu'elles sont stockées dans la base de données, l'échappement des formules est **désactivé par défaut**. L'exportateur CSV et les exportateurs Tablib (`xlsx`, `xls` et `ods`) acceptent tous un paramètre `escape_formulas`. Lorsque vous l'activez, toute chaîne commençant par un caractère déclencheur reçoit une apostrophe simple en tête (`'`), ce qui force l'application à afficher la valeur comme du texte brut.

!!! warning "Activez l'échappement des formules pour les données fournies par les utilisateurs"
    Si un compte autre qu'administrateur peut écrire des données dans un champ exporté, définissez `escape_formulas=True`. Sans cela, des valeurs contrôlées par un attaquant peuvent exécuter des commandes système ou exfiltrer des données lorsque quelqu'un ouvre le fichier localement.

Pour activer l'échappement, remplacez la chaîne de format par une instance d'exportateur explicite :

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

## Limites d'importation

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
| `max_upload_size` | `10 MB` | Vérifiée dès l'arrivée de la requête, avant toute analyse. |
| `max_rows` | `100_000` | Nombre maximal de lignes par requête d'importation. Le panneau d'administration compte la charge utile lors d'un pré-passe et rejette un fichier plus volumineux avec une réponse HTTP 400 avant de créer un quelconque enregistrement en base de données. Définissez `None` pour supprimer la limite. |

L'importation rejette systématiquement les archives ZIP, ce qui supprime le risque d'attaques par bombe ZIP sur cet endpoint. `FileField` et `ImageField` sont également exclus des importations groupées, car `exclude_from_import=True` par défaut ; les utilisateurs joignent donc les fichiers un par un via les formulaires de création ou de modification.

## Ce que cette page ne couvre pas

Les protections intégrées couvrent les risques présents dans la base de code du panneau d'administration. Elles ne sécurisent pas votre architecture dans son ensemble. Ces mesures opérationnelles sortent du périmètre de `starlette-admin` et restent à votre charge :

* **Sécurité du transport :** servez le panneau d'administration en HTTPS. Les cookies CSRF et messages flash sont signés, mais non chiffrés ; toute personne interceptant du trafic HTTP en clair peut donc les lire.
* **Authentification et autorisation :** l'instance `Admin` est publique tant que vous n'y attachez pas un `AuthProvider`. Sans cela, chaque endpoint et chaque route reste ouvert. Voir [Authentification](auth.md).
* **Exposition réseau :** si le panneau d'administration n'a pas besoin d'être accessible publiquement, placez-le derrière un pare-feu, un VPN ou une liste blanche d'adresses IP.
* **Hygiène des dépendances :** surveillez les avis de sécurité et maintenez `starlette-admin`, Starlette, votre pilote ORM et le reste de vos dépendances à jour.
* **Actions post-authentification :** la protection CSRF et la validation des téléversements ne limitent pas ce qu'un utilisateur connecté peut faire. Le contrôle d'accès granulaire provient entièrement des vérifications de permissions que vous écrivez dans `is_accessible`, `can_create`, `can_edit` et `can_delete`. Voir [Authentification](auth.md).

Considérez cette page comme un guide de configuration du paquet admin, et non comme une liste de contrôle pour sécuriser l'ensemble de votre déploiement de production.

---

## Et ensuite

* **[Exportation & Importation](export-import.md) :** la boîte de dialogue d'exportation, le cycle de vie de l'aperçu d'importation et la structure de l'archive ZIP.
* **[Stockage de fichiers](file-storage.md) :** modèles de configuration des backends de stockage pour `FileField` et `ImageField`.
* **[Authentification](auth.md) :** comment `secret_key` conditionne les sessions de connexion et les vérifications CSRF une fois que vous avez ajouté un fournisseur d'authentification.
