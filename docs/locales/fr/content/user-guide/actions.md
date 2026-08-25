---
title: Actions
description: Exécutez des opérations par lots et au niveau des lignes avec des confirmations
  et des formulaires personnalisés directement depuis la vue en liste.
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# Actions

Les actions vous offrent un moyen direct de manipuler vos enregistrements de base de données depuis l'interface d'administration, permettant aux utilisateurs d'exécuter des opérations comme des suppressions massives, des mises à jour groupées et des envois d'e-mails.

## Comprendre `ActionSelection`

`ActionSelection` est l'objet central de l'API des actions. Au lieu d'une simple liste de clés primaires, votre handler reçoit une instance de `ActionSelection`.

Cet objet se résout paresseusement et se comporte de la même manière que l'utilisateur ait coché les lignes une par une ou utilisé « tout sélectionner parmi les correspondances ». Il expose également à votre handler les filtres actifs de la page en liste.

### Référence de l'API `ActionSelection`

| Méthode ou propriété      | Description                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `await selection.rows()`  | Récupère les lignes cibles. Chargées une seule fois, puis mises en cache.          |
| `await selection.pks()`   | Récupère les clés primaires des lignes cibles.                                     |
| `await selection.count()` | Retourne le nombre total de lignes ciblées par l'action.                           |
| `selection.is_select_all` | Un booléen indiquant si l'utilisateur a choisi « tout sélectionner parmi les correspondances ». |
| `selection.filters`       | Le `FilterGroup` actif, identique à `ListParams.filters`.                          |
| `selection.q`             | Le terme de recherche plein texte actif, ou `None` lorsque la recherche est inactive. |

## Actions par lot

Par défaut, les utilisateurs modifient un objet en le sélectionnant sur la page en liste et en l'éditant individuellement. Pour appliquer la même modification à plusieurs objets à la fois, ajoutez une **action par lot** personnalisée.

!!! note
    `starlette-admin` ajoute une action par lot `delete` par défaut.

Pour ajouter une action par lot personnalisée à votre `ModelView`, écrivez une fonction asynchrone contenant votre logique et enveloppez-la avec le décorateur `@action`.

!!! important
    Les noms des actions par lot doivent être uniques au sein d'un même `ModelView`.

### Exemple d'action par lot

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

Une action par lot standard nécessite une sélection active : le menu déroulant **With selected** n'apparaît que lorsqu'au moins une ligne est cochée. Lorsqu'une action cible l'ensemble de la collection, comme une synchronisation complète de la base de données, faites-en une action globale.

Définissez `allow_empty_selection=True` dans le décorateur `@action`. Les actions globales s'affichent dans un menu déroulant **Actions** toujours visible et s'exécutent sans sélection de ligne.

**Comportement du handler pour les actions globales :**

- **Sélection vide :** L'objet `selection` peut se résoudre à zéro ligne.
- **Sélections incidentes :** Si l'utilisateur a coché des lignes au moment de déclencher une action globale, le handler reçoit quand même ces lignes. Ignorez explicitement `selection` lorsque votre logique cible l'intégralité de la collection.

Tous les autres paramètres (`confirmation`, `form`, `custom_response` et `is_action_allowed`) fonctionnent exactement comme pour une action par lot standard.

**Boutons dédiés dans la barre d'outils :** Ajoutez `dedicated_button=True` pour afficher une action globale sous forme de bouton dédié dans la barre d'outils plutôt que comme une entrée du menu déroulant **Actions**. L'action d'export intégrée utilise cette option. Combiner `dedicated_button=True` avec une action nécessitant une sélection déclenche une erreur au démarrage.

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

### La fonctionnalité « tout sélectionner parmi les correspondances »

Lorsqu'un utilisateur coche toutes les lignes de la page courante et que d'autres lignes correspondent au filtre ailleurs, l'interface propose de sélectionner toutes les lignes correspondantes.

Cette option envoie `all=1` à l'API des actions au lieu d'une liste de clés primaires. Utilisez `selection.is_select_all` pour adapter votre logique, ou laissez `selection.rows()` résoudre les données dans les deux cas :

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
    En mode select-all, `selection.rows()`, `pks()` et `count()` sont plafonnés par `action_select_all_limit`, dont la valeur par défaut est 1000. Dépasser cette limite lève une exception `ActionFailed`. Un handler qui ne lit que `selection.filters` et `selection.q` ne matérialise rien, le plafond ne s'applique donc pas.

## Actions de ligne {#row-actions}

Les actions de ligne permettent aux utilisateurs d'intervenir sur un élément unique directement depuis la vue en liste. `starlette-admin` inclut trois actions de ligne par défaut : `view`, `edit` et `delete`.

Pour ajouter une action de ligne personnalisée, écrivez votre logique et appliquez le décorateur `@row_action`. Lorsque l'action redirige simplement l'utilisateur vers une autre URL, utilisez plutôt le décorateur `@link_row_action`. Ce dernier intègre le lien dans l'attribut HTML `href` et ne fait pas appel à l'API des actions.

!!! important
    Les noms des actions de ligne doivent être uniques au sein d'un même `ModelView`.

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

Deux hooks déterminent si une action de ligne est disponible. Par défaut, ils autorisent tous deux l'action.

1. **`is_row_action_allowed(request, name)`** : exécuté une fois par nom d'action. Utilisez-le pour des restrictions qui ne dépendent pas de la ligne, telles que le contrôle d'accès basé sur les rôles.
2. **`is_row_action_allowed_for_obj(request, name, obj)`** : exécuté une fois par ligne, pour les actions ayant passé la première vérification. Utilisez-le pour des restrictions dépendant des données, comme masquer un bouton **Publish** sur un article déjà publié.

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
    Appelez toujours `super()` pour les noms d'action que votre surcharge ne traite pas. Sinon, vous désactivez silencieusement les vérifications de permissions des actions intégrées.

## Configuration de l'interface pour les actions de ligne

### Types d'affichage

Le paramètre `row_actions_display_type` définit la manière dont les actions apparaissent sur la page en liste. Sur la page de détail, les actions sont toujours affichées sous forme de boutons complets.

| Type d'affichage | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `ICON_LIST`      | Affiche une liste horizontale de boutons contenant uniquement des icônes. |
| `DROPDOWN`       | Regroupe les actions dans un menu déroulant avec étiquette.             |
| `KEBAB`          | Regroupe les actions dans un menu déroulant ouvert via une icône `⋮`.   |
| `INLINE_LINKS`   | Affiche l'étiquette de l'action sous l'icône, séparées par un point médian. |

### Positionnement de la colonne

Par défaut, la colonne des actions s'affiche avant vos colonnes de données. Pour la placer à droite du tableau, utilisez `RowActionsPosition` :

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## Formulaires d'action dynamiques

Le paramètre `form` des décorateurs `@action` et `@row_action` accepte un callable, ce qui vous permet de générer le HTML au moment de la requête.

Le callable peut être synchrone ou asynchrone, et il doit retourner une chaîne de caractères.

- **Signature de `@action`** : `(request) -> str`
- **Signature de `@row_action`** : `(request, obj) -> str`

Utilisez un callable lorsque vous souhaitez préremplir les champs du formulaire avec les valeurs actuelles d'une ligne.

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
    Un callable de formulaire d'action de ligne est exécuté une fois par ligne sur la page en liste. Veillez à ce qu'il soit rapide et évitez d'y effectuer des requêtes en base de données. Les données de ligne dont vous avez besoin sont déjà disponibles via le paramètre `obj`.
