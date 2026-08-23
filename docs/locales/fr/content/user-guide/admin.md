---
title: Configuration de l'admin
description: Configurez votre instance starlette-admin, personnalisez le thème, le
  routage et les paramètres de sécurité généraux.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

# Admin

Vous transmettez tous les paramètres globaux de l'admin en tant qu'arguments nommés à la classe `Admin` : le titre de la barre de navigation, l'emplacement de montage, la configuration CSRF et d'authentification, ainsi que le thème appliqué.

## Utilisation de base

Commencez par importer la classe `Admin` depuis le package `contrib` correspondant à votre ORM (object-relational mapper) :

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

Voici une configuration minimale qui utilise SQLAlchemy :

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
* `add_view` enregistre une vue, et `mount_to` construit les routes et les middleware de l'admin avant de les monter sur votre application.

Chaque classe `Admin` accepte toutes les options de configuration décrites ci-dessous, et certaines ajoutent un comportement propre à leur backend :

* `contrib.sqla.Admin(session_provider, ...)` prend un `Engine`, un `AsyncEngine`, un `sessionmaker` ou un `async_sessionmaker` comme premier argument positionnel et insère `DBSessionMiddleware` pour vous. `contrib.sqlmodel.Admin` est la même classe, réexportée. Voir [SQLAlchemy](../integrations/sqlalchemy.md) et [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` et `contrib.tortoise.Admin` ne prennent aucun argument de constructeur supplémentaire, car Beanie, MongoEngine et Tortoise ORM gèrent leurs propres connexions en dehors de l'admin. `mongoengine.Admin` enregistre également une route de service de fichiers GridFS dans `mount_to`. Voir [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) et [Tortoise ORM](../integrations/tortoise.md).

## Référence complète

Le constructeur `Admin` accepte tous les paramètres ci-dessous en tant qu'arguments nommés.

### Identité et image de marque

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Texte de la barre de navigation et balise `<title>`. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo affiché dans la barre de navigation à la place de `title`. Passez une URL simple, ou une fonction callable qui la résout par requête, par exemple pour une marque par tenant. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo affiché sur la page de connexion à la place de `logo_url`. Retombe sur `logo_url` lorsqu'il n'est pas défini. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Attribut href du `<link>` du favicon. |

`logo_url`, `login_logo_url` et `favicon_url` acceptent chacun soit une chaîne de caractères, soit une fonction `(request) -> str | None`. Utilisez une fonction lorsque l'image de marque dépend de la requête, par exemple dans une application multi-tenant ou lorsque vous servez plusieurs noms d'hôtes :

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Montage

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | Préfixe URL sous lequel l'admin est monté. |
| `route_name` | `str` | `"admin"` | Nom du montage Starlette. Tous les liens internes (`list`, `edit`, exportations, assets statiques) sont générés en appelant `request.url_for(route_name + ":list", ...)`. |

Pour exécuter plusieurs `Admin` dans la même application, attribuez à chaque instance un `base_url` et un `route_name` distincts. Sinon, les liens générés par un admin peuvent pointer vers un autre. Voir [Instances multiples de l'admin](../advanced/multiple-admin.md).


### Templates, fichiers statiques et thème

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Répertoire consulté pour les templates de remplacement avant de retomber sur les templates intégrés. |
| `static_dir` | `str | None` | `None` | Répertoire des fichiers statiques supplémentaires servis aux côtés des CSS et JS intégrés. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Une sous-classe de thème qui définit les templates de mise en page, le jeu d'icônes et les assets statiques. |

[Thèmes personnalisés](../advanced/custom-themes.md) et [Templates](../advanced/templates.md) couvrent ces options en détail.

### La page d'accueil

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (une `DefaultIndexView` construite à partir de vos vues enregistrées) | La page affichée à `base_url`. |

La page d'accueil par défaut est une bannière de bienvenue accompagnée d'un panneau par vue de modèle enregistrée, chacun affichant son nombre d'enregistrements. Pour la remplacer, passez votre propre `CustomView`, généralement une sous-classe de `DefaultIndexView` ou toute `CustomView` avec un widget. Voir [Vues personnalisées & widgets](custom-views.md).

### Authentification, sécurité et intégrité des données

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (l'admin est accessible publiquement) | Protège chaque route. Voir [Authentification](auth.md). |
| `secret_key` | `str | None` | `None` (une clé aléatoire est générée au démarrage, avec un `UserWarning`) | Signe les cookies CSRF et flash. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Middleware Starlette supplémentaires, exécutés en complément des middleware CSRF, flash et auth que l'admin ajoute lui-même. |
| `import_config` | `ImportConfig | None` | `None` (valeurs par défaut de `ImportConfig()`) | Limites de taille de téléversement et de protection contre les ZIP bombs pour l'endpoint d'importation. |
| `export_config` | `ExportConfig | None` | `None` (valeurs par défaut de `ExportConfig()`) | Plafond de nombre de lignes et limites de téléchargement depuis URL pour l'endpoint d'exportation. |

Le guide [Sécurité](security.md) traite ces cinq paramètres en profondeur.

### Locale et fuseau horaire

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (anglais uniquement, sans `LocaleMiddleware`) | Active les chaînes d'interface traduites. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (activé) | Convertit les dates et heures affichées dans le fuseau horaire du visiteur. |

Pour une présentation complète, voir [Internationalisation & fuseaux horaires](i18n.md).

### Débogage

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Lorsqu'il vaut `True`, appelle `starlette_admin.logging.configure_logging()` avant le démarrage, ce qui active la journalisation console colorée au niveau DEBUG pour le package `starlette_admin`. |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

La journalisation de débogage est utile pendant le développement. Chaque requête journalise le middleware exécuté, la vue qui a résolu l'URL, et la raison pour laquelle une vérification de permission a réussi ou échoué.

!!! warning
    Conservez `debug=False` en production. La journalisation au niveau DEBUG est verbeuse et ajoute une surcharge importante à chaque requête.

Pour une approche plus légère, appelez vous-même `starlette_admin.logging.configure_logging(level=logging.INFO)` au lieu de passer `debug=True`. Vous obtenez le handler sans la verbosité complète du niveau DEBUG.

## Enregistrer les vues et monter l'admin

Après avoir créé l'instance `Admin`, enregistrez vos vues et montez l'admin sur votre application.

```python
admin.add_view(ModelView(Post))  # Enregistre une vue (BaseModelView, CustomView, etc.)
admin.mount_to(app)  # Monte l'admin sur votre application Starlette ou FastAPI
```

### Enregistrer les vues

Utilisez `add_view` pour ajouter des composants à votre tableau de bord d'administration. Cette méthode accepte aussi bien une instance de vue qu'une classe de vue, et vous pouvez enregistrer des vues de modèle, des pages personnalisées, des menus déroulants et des liens externes.

### Monter l'application

Après avoir enregistré toutes vos vues, appelez `mount_to(app)` exactement une fois pour attacher l'admin à votre application Starlette ou FastAPI. Cette étape finalise la configuration du routage et de la sécurité.

!!! important "L'ordre des opérations compte"
    Le montage verrouille la configuration de l'admin afin que chaque vue soit routée correctement.

    * Accéder à `admin.app` avant le montage lève une `RuntimeError`.
    * Enregistrer une autre vue ou rappeler `mount_to` après le premier montage lève également une `RuntimeError`.

```python
admin.app  # Lève RuntimeError : pas encore monté

admin.mount_to(app)
admin.app  # Renvoie la sous-application montée

admin.add_view(ModelView(Comment))  # Lève RuntimeError : déjà monté
```

---

**Et ensuite ?**

* **[Sécurité](security.md) :** la `secret_key`, le CSRF, ainsi que les limites d'exportation et d'importation.
* **[Authentification](auth.md) :** câbler le `auth_provider`.
* **[Instances multiples de l'admin](../advanced/multiple-admin.md) :** exécuter plusieurs `Admin` dans la même application.
