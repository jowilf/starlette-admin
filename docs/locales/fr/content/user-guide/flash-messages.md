---
title: Messages flash
description: Envoyer des alertes éphémères de succès, d'avertissement ou d'erreur
  aux utilisateurs après la réalisation d'actions dans starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Messages flash

Les messages flash fournissent aux utilisateurs un retour temporaire, à usage unique, après qu'ils ont effectué une action, par exemple « Article créé avec succès » ou « Type de fichier invalide ». Un message survit à une seule redirection HTTP, et l'interface d'administration le supprime une fois affiché.

`flash()` place un message en file d'attente sur la requête courante. L'administration affiche le message sur la page suivante que l'utilisateur consulte, puis vide la file. Ce modèle provient de Flask-Admin.


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash


class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Queue the message for the next page load
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")
```

## Catégories de messages

Chaque message flash nécessite une catégorie. La catégorie détermine la couleur du bandeau dans le thème par défaut, ce qui permet aux utilisateurs d'évaluer la gravité d'un coup d'œil.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")
```

L'argument `category` vaut `"info"` par défaut. Il doit correspondre exactement à l'une des valeurs suivantes : `success`, `info`, `warning` ou `error`. Toute autre valeur lève une `ValueError`.

## Messages CRUD intégrés

Vous n'avez pas besoin d'appeler `flash()` pour les opérations CRUD standard. L'administration émet automatiquement un message `success` lorsque ces actions se terminent :

| Action | Message par défaut |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "À quoi correspond `<repr>`"
    Les messages automatiques utilisent la représentation de ligne définie par `view.repr()`, et non le nom de classe du modèle. Par exemple, la création d'un article émet *« The item 'My First Post' was added successfully »* plutôt qu'un générique *« Post was added successfully »*.

## Utiliser les messages flash dans des actions personnalisées

Les gestionnaires d'actions personnalisées (`@action` et `@row_action`) renvoient `None` par défaut. Pour fournir un retour à l'utilisateur, appelez `flash()` avant que le gestionnaire ne retourne.

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

        # Notify the user that the custom action succeeded
        flash(request, f"{len(pks)} post(s) published.", category="success")
```

* **Si vous omettez `flash()` :** l'action s'exécute toujours, mais l'utilisateur ne reçoit aucune confirmation visuelle après la redirection de la page.
* **Si l'action échoue :** lorsque votre action personnalisée lève `ActionFailed`, l'administration intercepte l'exception et affiche sa chaîne sous forme de bandeau d'erreur. N'appelez pas `flash()` dans une branche `ActionFailed`, car la requête n'est pas redirigée.

## Afficher les messages dans des templates personnalisés

Le template de base de l'administration extrait et affiche les messages flash pour vous. Vous n'avez besoin de les récupérer vous-même que si vous construisez entièrement une [vue personnalisée](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]
```

La lecture de la file des messages flash est **destructive**. Le premier appel à `get_flashed_messages(request)` extrait et vide la file. Les appels suivants durant la même requête renvoient une liste vide, `[]`.

!!! important "Gardez des messages courts"
    Les messages flash sont stockés dans un cookie signé et `httponly` nommé `admin_flash`, et non dans la session côté serveur. Les navigateurs limitent la taille d'un cookie à environ 4 Ko ; réservez donc les messages flash aux retours brefs. Évitez les longues chaînes et les charges de données volumineuses. Cette approche basée sur les cookies signifie également que les messages flash fonctionnent sans `SessionMiddleware`.

> Consultez [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) pour une application exécutable qui appelle `flash()` depuis des hooks et des actions personnalisées.

---

## Pour aller plus loin

* **[Actions](actions.md)** : Déclencher une logique métier via des actions groupées ou sur des lignes.
* **[Sécurité](security.md)** : Découvrez comment `secret_key` sécurise à la fois le cookie des messages flash et les jetons CSRF.
* **[Templates](../advanced/templates.md)** : Afficher les bandeaux de messages flash dans vos propres mises en page.
