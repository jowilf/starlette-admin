---
title: Actions
description: Exécutez des opérations groupées et au niveau des lignes avec des confirmations
  et des formulaires personnalisés directement depuis la page de liste.
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

# Actions

Les actions offrent un moyen direct de travailler sur vos enregistrements de base de données depuis l'interface d'administration, permettant aux utilisateurs d'exécuter des opérations telles que des suppressions massives, des mises à jour en bloc et des envois d'e-mails.

## Comprendre `ActionSelection`

`ActionSelection` est l'objet central de l'API des actions. Au lieu d'une liste brute de clés primaires, votre handler reçoit une instance de `ActionSelection`.

L'objet est résolu paresseusement (lazy) et se comporte de la même manière que l'utilisateur ait coché les lignes une par une ou utilisé « tout sélectionner parmi les résultats correspondants ». Il expose également les filtres actifs de la page de liste à votre handler.

### Référence de l'API `ActionSelection`

| Méthode ou propriété      | Description                                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| `await selection.rows()`  | Récupère les lignes ciblées. Elles sont récupérées une seule fois, puis mises en cache.         |
| `await selection.pks()`   | Récupère les clés primaires des lignes ciblées.                                                 |
| `await selection.count()` | Renvoie le nombre total de lignes ciblées par l'action.                                         |
| `selection.is_select_all` | Booléen indiquant si l'utilisateur a choisi « tout sélectionner parmi les résultats correspondants ». |
| `selection.filters`       | Le `FilterGroup` actif, identique à `ListParams.filters`.                                       |
| `selection.q`             | Le terme de recherche plein texte actif, ou `None` lorsque la recherche est inactive.           |

## Actions groupées

Par défaut, les utilisateurs modifient un objet en le sélectionnant sur la page de liste puis en l'éditant individuellement. Pour appliquer la même modification à plusieurs objets à la fois, ajoutez une **action groupée** personnalisée.

!!! note
    `starlette-admin` ajoute une action groupée `delete` par défaut.

Pour ajouter une action groupée personnalisée à votre `ModelView`, écrivez une fonction async contenant votre logique et enveloppez-la avec le décorateur `@action`.

!!! important
    Les noms des actions groupées doivent être uniques au sein d'un `ModelView`.

### Exemple d'action groupée

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

```

## Actions globales

Une action groupée standard nécessite une sélection active : le menu déroulant **Avec la sélection** n'apparaît que lorsqu'au moins une ligne est cochée. Lorsqu'une action cible l'ensemble de la collection, par exemple une synchronisation complète de la base de données, faites-en une action globale.

Définissez `allow_empty_selection=True` dans le décorateur `@action`. Les actions globales s'affichent dans un menu déroulant **Actions** toujours visible et s'exécutent sans sélection de ligne.

**Comportement du handler pour les actions globales :**

- **Sélection vide :** l'objet `selection` peut se résoudre à zéro ligne.
- **Sélections fortuites :** si l'utilisateur a des lignes cochées lorsqu'il déclenche une action globale, le handler reçoit quand même ces lignes. Ignorez explicitement `selection` lorsque votre logique cible l'ensemble de la collection.

Tous les autres paramètres (`confirmation`, `form`, `custom_response` et `is_action_allowed`) fonctionnent exactement comme pour une action groupée standard.

**Boutons dédiés dans la barre d'outils :** ajoutez `dedicated_button=True` pour afficher une action globale comme bouton autonome dans la barre d'outils plutôt que comme entrée du menu déroulant **Actions**. L'action d'exportation intégrée utilise cette option. Combiner `dedicated_button=True` avec une action réservée à la sélection provoque une erreur au démarrage.

### Exemple d'action globale

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

```

### La fonctionnalité « tout sélectionner »

Lorsqu'un utilisateur coche toutes les lignes de la page courante alors que d'autres lignes correspondent au filtre ailleurs, l'interface propose de sélectionner toutes les lignes correspondantes.

Cette option envoie `all=1` à l'API des actions au lieu d'une liste de clés primaires. Utilisez `selection.is_select_all` pour orienter votre logique, ou laissez `selection.rows()` résoudre les données dans tous les cas :

```python
    @action(name="archive", text="Archive")
    async def archive_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        if selection.is_select_all:
            await self.bulk_archive_where(request, selection.filters, selection.q)
        else:
            await self.bulk_archive_pks(request, await selection.pks())

```

!!! important "Limites de matérialisation"
    En mode « tout sélectionner », `selection.rows()`, `pks()` et `count()` sont limités par `action_select_all_limit`, dont la valeur par défaut est 1000. Dépasser cette limite lève une exception `ActionFailed`. Un handler qui lit uniquement `selection.filters` et `selection.q` ne matérialise rien ; la limite ne s'applique donc pas.

## Actions de ligne

Les actions de ligne permettent aux utilisateurs d'opérer sur un seul élément directement depuis la page de liste. `starlette-admin` inclut trois actions de ligne par défaut : `view`, `edit` et `delete`.

Pour ajouter une action de ligne personnalisée, écrivez votre logique et appliquez le décorateur `@row_action`. Lorsque l'action redirige simplement l'utilisateur vers une autre URL, utilisez plutôt le décorateur `@link_row_action`. Il intègre le lien dans l'attribut HTML `href` et contourne l'API des actions.

!!! important
    Les noms des actions de ligne doivent être uniques au sein d'un `ModelView`.

### Exemple d'action de ligne

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### Restreindre les actions de ligne

Deux hooks déterminent si une action de ligne est disponible. Tous deux autorisent l'action par défaut.

1. **`is_row_action_allowed(request, name)`** : exécuté une fois par nom d'action. Utilisez-le pour les restrictions qui ne dépendent pas de la ligne, comme le contrôle d'accès basé sur les rôles.
2. **`is_row_action_allowed_for_obj(request, name, obj)`** : exécuté une fois par ligne, pour les actions ayant passé la première vérification. Utilisez-le pour les restrictions dépendant des données, comme masquer un bouton **Publier** sur un article déjà publié.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView

class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)

```

!!! warning
    Appelez toujours `super()` pour les noms d'actions non gérés par votre override. Sinon, vous désactivez silencieusement les vérifications de permissions des actions intégrées.

## Configuration de l'interface pour les actions de ligne

### Types d'affichage

Le paramètre `row_actions_display_type` définit la façon dont les actions apparaissent sur la page de liste. Sur la page de détail, les actions sont toujours affichées comme des boutons complets.

| Type d'affichage | Description                                                                       |
| ---------------- | ---------------------------------------------------------------------------------- |
| `ICON_LIST`      | Affiche une liste horizontale de boutons réduits à leur icône.                     |
| `DROPDOWN`       | Regroupe les actions dans un menu déroulant libellé.                               |
| `KEBAB`          | Regroupe les actions dans un menu déroulant ouvert via une icône `⋮`.              |
| `INLINE_LINKS`   | Affiche le libellé de l'action sous l'icône, séparé par un point médian.           |

### Positionnement de la colonne

Par défaut, la colonne des actions est affichée avant vos colonnes de données. Pour la placer à droite du tableau, utilisez `RowActionsPosition` :

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## Formulaires d'action dynamiques

Le paramètre `form` des décorateurs `@action` et `@row_action` accepte un callable, ce qui vous permet de générer le HTML au moment de la requête.

Le callable peut être synchrone ou asynchrone, et il doit renvoyer une chaîne de caractères.

- **Signature de `@action`** : `(request) -> str`
- **Signature de `@row_action`** : `(request, obj) -> str`

Utilisez un callable lorsque vous souhaitez préremplir les champs d'un formulaire avec les valeurs actuelles d'une ligne.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]

```

!!! important
    Un callable de formulaire d'action de ligne est exécuté une fois par ligne sur la page de liste. Veillez à ce qu'il soit rapide et évitez d'y effectuer des requêtes en base de données. Les données de ligne dont vous avez besoin sont déjà disponibles via le paramètre `obj`.
