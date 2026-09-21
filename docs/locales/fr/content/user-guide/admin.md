---
title: Configuration de l'Admin
description: Configurez votre instance starlette-admin, personnalisez le thème, le
  routage et les paramètres généraux de sécurité.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Admin

Vous transmettez chaque paramètre global de l'admin en tant qu'argument nommé à la classe `Admin` : le titre de la barre de navigation, l'emplacement de montage, la configuration CSRF et d'authentification, ainsi que le thème affiché.

## Utilisation de base

Commencez par importer la classe `Admin` depuis le paquet `contrib` correspondant à votre ORM (object-relational mapper) :

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

Voici une configuration minimale utilisant SQLAlchemy :

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` définit le texte de la barre de navigation et la balise HTML `<title>`.
* `base_url` définit le préfixe de chemin sous lequel l'admin est monté.
* `secret_key` signe les cookies CSRF et flash.
* `add_view` enregistre une vue, et `mount_to` construit les routes et le middleware de l'admin avant de les monter sur votre application.

Chaque classe `Admin` accepte toutes les options de configuration décrites ci-dessous, et certaines ajoutent des comportements spécifiques au backend :

* `contrib.sqla.Admin(session_provider, ...)` prend un `Engine`, `AsyncEngine`, `sessionmaker` ou `async_sessionmaker` comme premier argument positionnel et insère pour vous le middleware `DBSessionMiddleware`. `contrib.sqlmodel.Admin` est la même classe, réexportée. Consultez [SQLAlchemy](../integrations/sqlalchemy.md) et [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` et `contrib.tortoise.Admin` ne prennent aucun argument supplémentaire au constructeur, car Beanie, MongoEngine et Tortoise ORM gèrent leurs propres connexions en dehors de l'admin. `mongoengine.Admin` enregistre également une route de diffusion de fichiers GridFS dans `mount_to`. Consultez [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) et [Tortoise ORM](../integrations/tortoise.md).

## Référence complète

Le constructeur `Admin` accepte tous les paramètres ci-dessous comme arguments nommés.

### Identité et image de marque

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Texte de la barre de navigation et balise `<title>`. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo affiché dans la barre de navigation à la place de `title`. Passez une URL simple, ou une fonction qui la résout par requête, par exemple pour une image de marque multi-tenant. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo affiché sur la page de connexion à la place de `logo_url`. Retombe sur `logo_url` s'il n'est pas défini. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Attribut href du `<link>` du favicon. |

`logo_url`, `login_logo_url` et `favicon_url` acceptent chacun soit une chaîne de caractères, soit une fonction `(request) -> str | None`. Utilisez une fonction lorsque l'image de marque dépend de la requête, comme dans une application multi-tenant ou lorsque vous servez plusieurs noms d'hôte :

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Montage

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | Préfixe d'URL sous lequel l'admin est monté. |
| `route_name` | `str` | `"admin"` | Nom du montage Starlette. Chaque lien interne (`list`, `edit`, exports, ressources statiques) est généré en appelant `request.url_for(route_name + ":list", ...)`. |

Pour exécuter plusieurs instances `Admin` dans la même application, donnez à chaque instance un `base_url` et un `route_name` distincts. Sinon, les liens générés par un admin peuvent pointer vers un autre. Consultez [Instances multiples de l'Admin](../advanced/multiple-admin.md).


### Templates, fichiers statiques et thème

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Répertoire examiné pour les surcharges de templates avant de retomber sur les templates intégrés. |
| `static_dir` | `str | None` | `None` | Répertoire des fichiers statiques supplémentaires servis aux côtés du CSS et du JS intégrés. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Une sous-classe de thème qui définit les templates de mise en page, le jeu d'icônes et les ressources statiques. |

[Thèmes personnalisés](../advanced/custom-themes.md) et [Templates](../advanced/templates.md) couvrent ces options en détail.

### La page d'accueil

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (une `DefaultIndexView` construite à partir de vos vues enregistrées) | La page rendue à l'adresse `base_url`. |

La page d'accueil par défaut est une bannière de bienvenue accompagnée d'un panneau par vue de modèle enregistrée, chacun affichant son nombre d'enregistrements. Pour la remplacer, passez votre propre `CustomView`, généralement une sous-classe de `DefaultIndexView` ou tout `CustomView` avec un `widget`. Consultez [Vues & widgets personnalisés](custom-views.md).

### Authentification, sécurité et intégrité des données

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (l'admin est accessible publiquement) | Protège toutes les routes. Consultez [Authentification](auth.md). |
| `secret_key` | `str | None` | `None` (une clé aléatoire est générée au démarrage, avec un `UserWarning`) | Signe les cookies CSRF et flash. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Middleware Starlette supplémentaires, exécutés en plus des middleware CSRF, flash et auth que l'admin ajoute lui-même. |
| `import_config` | `ImportConfig | None` | `None` (valeurs par défaut de `ImportConfig()`) | Limites de taille de téléversement et de protection contre les ZIP bombs pour l'endpoint d'import. |
| `export_config` | `ExportConfig | None` | `None` (valeurs par défaut de `ExportConfig()`) | Limite du nombre de lignes et limites de téléchargement depuis fichier URL pour l'endpoint d'export. |

Le guide [Sécurité](security.md) traite ces cinq paramètres en profondeur.

### Locale et fuseau horaire

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (anglais uniquement, pas de `LocaleMiddleware`) | Active les chaînes d'interface traduites. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (activé) | Convertit les dates-heures affichées vers le fuseau horaire du visiteur. |

Pour une présentation complète, consultez [Internationalisation & fuseaux horaires](i18n.md).

### Débogage {#debugging}

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Lorsque la valeur est `True`, appelle `starlette_admin.logging.configure_logging()` avant le démarrage, ce qui active la journalisation console colorée au niveau DEBUG pour le paquet `starlette_admin`. |

```python
admin = Admin(
    session_provider=engine,
    title="My Admin",
    secret_key="a-long-random-string",
    debug=True,
)
```

La journalisation de débogage est utile pendant le développement. Chaque requête journalise le middleware exécuté, la vue qui a résolu l'URL, ainsi que la raison pour laquelle un contrôle d'autorisation a réussi ou échoué.

!!! warning
    Conservez `debug=False` en production. La journalisation au niveau DEBUG est prolixe et ajoute une surcharge significative à chaque requête.

Pour une approche plus légère, appelez vous-même `starlette_admin.logging.configure_logging(level=logging.INFO)` au lieu de passer `debug=True`. Vous bénéficiez du gestionnaire sans toute la verbosité DEBUG.

## Enregistrement des vues et montage

Après avoir créé l'instance `Admin`, enregistrez vos vues et montez l'admin sur votre application.

```python
admin.add_view(ModelView(Post))  # Enregistre une vue (BaseModelView, CustomView, etc.)
admin.mount_to(app)  # Monte l'admin sur votre application Starlette ou FastAPI
```

### Enregistrement des vues

Utilisez `add_view` pour ajouter des composants à votre tableau de bord admin. Cette méthode accepte aussi bien une instance de vue qu'une classe de vue, et vous pouvez enregistrer des vues de modèle, des pages personnalisées, des menus déroulants et des liens externes.

### Montage de l'application

Une fois toutes vos vues enregistrées, appelez `mount_to(app)` exactement une fois pour rattacher l'admin à votre application Starlette ou FastAPI. Cette étape finalise la configuration du routage et de la sécurité.

!!! important "L'ordre des opérations compte"
    Le montage verrouille la configuration de l'admin afin que chaque vue soit routée correctement.

    * Accéder à `admin.app` avant le montage déclenche une `RuntimeError`.
    * Enregistrer une autre vue ou appeler `mount_to` une seconde fois après le premier montage déclenche également une `RuntimeError`.

```python
admin.app  # Déclenche RuntimeError: pas encore monté

admin.mount_to(app)
admin.app  # Renvoie la sous-application montée

admin.add_view(ModelView(Comment))  # Déclenche RuntimeError: déjà monté
```

---

**Et ensuite ?**

* **[Sécurité](security.md) :** la `secret_key`, le CSRF, ainsi que les limites d'export et d'import.
* **[Authentification](auth.md) :** câblage de l'`auth_provider`.
* **[Instances multiples de l'Admin](../advanced/multiple-admin.md) :** exécution de plusieurs instances `Admin` dans la même application.
