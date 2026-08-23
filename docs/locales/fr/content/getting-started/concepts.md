---
title: Concepts fondamentaux
description: Comprenez les principes de conception architecturale de starlette-admin,
  notamment les vues déclaratives, l'état basé sur l'URL et les modèles indépendants
  du backend.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

# Concepts fondamentaux

Après avoir terminé le guide de démarrage rapide en écrivant une classe `PostView` et en montant une instance d'administration, découvrez les principes de conception architecturale du framework. Ces concepts fondamentaux constituent la base du reste de la documentation.

## Une classe par ressource

Chaque ressource gérée par le panneau d'administration est exposée au moyen d'une seule classe dédiée. Lorsque vous créez une sous-classe de `ModelView` et que vous la pointez vers un modèle de base de données, vous générez automatiquement des vues paginables, triables et filtrables pour toutes les opérations CRUD standard (liste, détail, création, modification et suppression).

Cela vous évite d'avoir à écrire des routes personnalisées ou des templates HTML. Tout ce qui régit l'apparence, la validation et le comportement d'une ressource réside dans cette unique classe de vue.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## La même vue, quel que soit le backend

Les vues communiquent avec vos données via une couche backend adaptable. Que votre application utilise SQLAlchemy, SQLModel, Beanie, MongoEngine ou Tortoise ORM, l'API de configuration reste exactement la même.

Les champs, les filtres, les permissions et les hooks de cycle de vie fonctionnent de manière cohérente, quel que soit l'emplacement de vos données. Les connaissances acquises sur un backend se transfèrent directement aux autres. Le remplacement de votre source de données sous-jacente ne nécessite qu'une mise à jour de vos instructions d'importation.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## État de la page de liste basé sur l'URL

Le tri, le filtrage, la pagination et les critères de recherche sont synchronisés directement avec la chaîne de requête de l'URL. Comme le serveur génère les états de liste entièrement à partir de ces paramètres d'URL, chaque état de vue est naturellement ajoutable aux favoris et partageable.

Si vous envoyez un lien d'administration précis à un collègue, celui-ci voit exactement les mêmes lignes filtrées et la même configuration de tri que vous.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Des champs qui savent s'afficher eux-mêmes

Les champs sont des composants auto-rendus. Chaque type de champ gère sa propre logique d'affichage dans trois contextes distincts : une cellule dans un tableau de liste, une ligne dans une vue de détail et un élément de saisie dans un formulaire.

Lorsque vous construisez une vue, vous déclarez des instances de champ ou passez des noms d'attributs que le backend associe automatiquement à des champs. Choisissez le type correspondant à votre modèle de données ; le framework se charge du rendu :

* `StringField` pour les chaînes de texte
* `IntegerField` pour les données numériques
* `ImageField` pour le téléversement de fichiers

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Dispositions de formulaire déclaratives

Par défaut, l'attribut `fields` affiche vos formulaires de création et de modification sous forme de liste verticale simple. Pour réorganiser l'interface utilisateur sans modifier vos définitions de données sous-jacentes, utilisez l'attribut `form_layout`.

### La notation abrégée en tuple

Pour les dispositions en grille simples, regroupez les noms de champs dans un tuple afin de les afficher côte à côte sur une même ligne. Cela évite d'avoir à importer des classes de widget complexes.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Widgets de disposition avancés

À mesure que vos formulaires gagnent en complexité, vous pouvez les structurer à l'aide de widgets de disposition. La notation abrégée en tuple fonctionne nativement dans ces composants :

* **`PanelWidget` ou `FieldsetWidget` :** utilisez ces composants pour regrouper des champs liés sous un titre clair ou pour rendre des sections repliables.
* **`TabsWidget` :** utilisez ce composant lorsqu'une ressource comporte des catégories de données distinctes (comme les informations d'expédition par rapport aux métadonnées SEO) qui n'ont pas besoin d'être visibles simultanément.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

## Des filtres attachés aux types de champ

Les capacités de filtrage correspondent directement aux types de données, ce qui garantit que les utilisateurs ne voient que les options de requête pertinentes. Un `StringField` propose des options textuelles contextuelles comme *contient*, *commence par*, *est égal à* et *est nul*. Un champ entier fournit des contraintes numériques comme *supérieur à* ou *entre*.

Vous pouvez restreindre ou remplacer ces valeurs par défaut sur un champ individuel à l'aide du paramètre `filters`, ou enregistrer des filtres personnalisés pour des types de données spécifiques.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Apportez votre propre authentification

Le framework reste totalement agnostique quant à votre schéma d'utilisateurs en omettant tout modèle d'utilisateur intégré. L'authentification nécessite l'implémentation d'une seule méthode : `authenticate(request)`.

Connectez cette méthode à votre infrastructure d'authentification existante, comme une table de base de données locale, un fournisseur OAuth ou un en-tête de proxy SSO (authentification unique) en amont. Renvoyer un objet `AdminUser` accorde l'accès à l'interface. Renvoyer `None` refuse l'accès.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Des actions exécutées sur les lignes sélectionnées

Les actions groupées opèrent sur plusieurs lignes sélectionnées depuis la barre d'outils supérieure, tandis que les actions de ligne s'exécutent directement sur des enregistrements individuels. Décorer une méthode de vue avec `@action` ou `@row_action` expose automatiquement cette méthode dans l'interface utilisateur, sans enregistrement manuel de route.

Plutôt que de renvoyer une chaîne de message depuis la méthode d'action, déclenchez directement les notifications utilisateur à l'aide de l'utilitaire intégré `flash()`.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Exportation et importation natives des données

Chaque page de liste comporte une boîte de dialogue d'exportation permettant aux utilisateurs de sélectionner la portée (lignes sélectionnées ou page actuelle), les champs, le format et le nom de fichier. Les filtres actifs et les termes de recherche sont conservés, ce qui signifie que le fichier exporté correspond exactement à ce qui apparaît à l'écran.

Le framework prend en charge nativement les formats CSV, JSON et PDF. Pour des formats supplémentaires comme Excel (`xlsx`), le framework s'intègre avec `tablib` pour prendre en charge tout type de fichier compatible. Les formats sont déclarés comme de simples chaînes d'extension. Le contrôle d'accès est géré de manière fine à l'aide du hook `can_export`.

L'assistant d'importation ingère en toute sécurité des données volumineuses dans ces mêmes formats. L'assistant valide d'abord le fichier téléversé lors d'une étape d'aperçu, en mettant en évidence les erreurs ligne par ligne avant toute écriture en base de données, et prend en charge les upserts facultatifs de clé primaire. Vous pouvez restreindre l'accès à cette fonctionnalité à l'aide du hook `can_import`.

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Stockage de fichiers flexible

La gestion des médias via `FileField` et `ImageField` repose sur une couche d'abstraction `Storage` sous-jacente. Utilisez `LocalStorage` pour les écritures sur disque local, ou installez l'intégration S3 facultative en exécutant `pip install starlette-admin[s3]`.

Le champ coordonne automatiquement le téléversement des fichiers, la validation côté backend et le rendu côté frontend une fois que vous l'avez pointé vers la configuration de stockage choisie.

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Vues personnalisées et widgets de tableau de bord

Les pages qui ne sont pas explicitement liées à un modèle de base de données, comme les tableaux de bord de métriques ou les rapports personnalisés, se construisent à l'aide de `CustomView`. Le contenu est renseigné à l'aide d'un paramètre `widget`. Ce paramètre accepte soit une instance statique de `BaseWidget`, soit un appel dynamique exécuté lorsque le contenu dépend de la requête entrante.

Vous pouvez composer des interfaces utilisateur complexes en organisant des primitives de disposition et des widgets de visualisation de données selon une hiérarchie claire.

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## Événements et hooks de méthode

Le framework fournit deux points d'extension distincts pour exécuter du code durant les cycles de création, de mise à jour et de suppression :

1. **Méthodes de cycle de vie :** pour une logique isolée à une entité spécifique, redéfinissez des méthodes locales comme `before_create` directement sur votre classe de vue.
2. **Écouteurs d'événements :** pour des préoccupations globales comme les journaux d'audit, l'invalidation du cache ou les webhooks, abonnez-vous au système `admin.events`.

Ces deux schémas se déclenchent aux mêmes points d'exécution, ce qui vous permet de choisir l'approche la mieux adaptée à l'architecture de votre application.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**Et ensuite**

* **[Vues](../user-guide/views.md) :** toutes les options de configuration de `ModelView`.
* **[Champs](../user-guide/fields.md) :** le catalogue complet des types de champ.
* **[Dispositions de formulaire](../advanced/form-layout.md) :** organisez les formulaires de création et de modification avec des lignes, des panneaux et des onglets.
* **[Actions](../user-guide/actions.md) :** les actions groupées et les actions de ligne en profondeur.
