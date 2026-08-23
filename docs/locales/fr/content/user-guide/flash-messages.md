---
title: Messages flash
description: Envoyez des alertes éphémères de succès, d'avertissement ou d'erreur
  aux utilisateurs après avoir accompli des actions dans starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

# Messages flash

Les messages flash fournissent aux utilisateurs un retour temporaire, à usage unique, après l'exécution d'une action, comme « Post créé avec succès » ou « Type de fichier invalide ». Un message survit à une seule redirection HTTP, et le panneau d'administration le supprime après son affichage.

`flash()` met en file d'attente un message sur la requête courante. Le panneau d'administration affiche le message sur la page suivante que l'utilisateur voit, puis vide la file. Ce motif provient de Flask-Admin.


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash

class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Mettre le message en file pour le prochain chargement de page
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")

```

## Catégories de messages

Chaque message flash nécessite une catégorie. La catégorie définit la couleur de la bannière dans le thème par défaut, ce qui permet aux utilisateurs d'évaluer la gravité d'un coup d'œil.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

L'argument `category` vaut par défaut `"info"`. Il doit être exactement l'une des valeurs suivantes : `success`, `info`, `warning` ou `error`. Toute autre valeur lève une `ValueError`.

## Messages CRUD intégrés

Vous n'avez pas besoin d'appeler `flash()` pour les opérations CRUD standard. Le panneau d'administration affiche automatiquement un message `success` lorsque ces actions se terminent :

| Action | Message par défaut |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "À quoi correspond `<repr>`"
    Les messages automatiques utilisent la représentation de ligne définie par `view.repr()`, et non le nom de classe du modèle. Par exemple, la création d'un post déclenche l'affichage de *« The item 'My First Post' was added successfully »* plutôt qu'un générique *« Post was added successfully »*.

## Utiliser des messages flash dans les actions personnalisées

Les gestionnaires d'actions personnalisées (`@action` et `@row_action`) retournent `None` par défaut. Pour fournir un retour à l'utilisateur, appelez `flash()` avant que le gestionnaire ne retourne.

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash

class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Informer l'utilisateur du succès de l'action personnalisée
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **Si vous omettez `flash()` :** l'action s'exécute quand même, mais l'utilisateur ne reçoit aucune confirmation visuelle après la redirection de la page.
* **Si l'action échoue :** lorsque votre action personnalisée lève `ActionFailed`, le panneau d'administration intercepte l'exception et affiche sa chaîne sous forme de bannière d'erreur. N'appelez pas `flash()` dans une branche `ActionFailed`, car la requête n'est pas redirigée.

## Afficher les messages dans vos templates personnalisés

Le template de base du panneau d'administration récupère et affiche les messages flash pour vous. Vous n'avez besoin de les récupérer vous-même que si vous construisez entièrement une [vue personnalisée](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

La lecture de la file des messages flash est **destructrice**. Le premier appel à `get_flashed_messages(request)` récupère et vide la file. Les appels suivants au cours de la même requête retournent une liste vide, `[]`.

!!! important "Gardez les messages courts"
    Les messages flash sont stockés dans un cookie signé et `httponly` nommé `admin_flash`, et non dans la session du serveur. Les navigateurs limitent la taille des cookies à environ 4 Ko ; utilisez donc les messages flash uniquement pour un retour concis. Évitez les chaînes longues et les charges utiles volumineuses. L'approche basée sur les cookies signifie également que les messages flash fonctionnent sans `SessionMiddleware`.

> Consultez [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) pour voir une application exécutable qui appelle `flash()` depuis des hooks et des actions personnalisées.

---

## Et ensuite ?

* **[Actions](actions.md)** : Déclencher une logique métier pour les actions groupées et les actions de ligne.
* **[Sécurité](security.md)** : Découvrez comment sécuriser le cookie des messages flash et les jetons CSRF.
* **[Templates avancés](../advanced/templates.md)** : Rendre des bannières de messages flash dans vos propres templates.
