---
title: Événements
description: Abonnez-vous aux événements globaux du cycle de vie tels que AFTER_CREATE
  pour construire des journaux d'audit, des webhooks et des workflows asynchrones.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

# Événements

Un hook de méthode comme `before_create` ne s'exécute que pour la vue qui le définit. Le système d'événements permet à du code extérieur à cette vue de réagir à ce qui s'y passe : un journal d'audit, un webhook ou une invalidation de cache peuvent ainsi être définis à un seul endroit au lieu d'être copiés-collés dans chaque `ModelView` que vous écrivez.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Enregistrez ce gestionnaire une seule fois à côté de votre instance `admin` et l'endpoint de création de chaque vue l'appellera, y compris celles que vous ajouterez plus tard.

## Vue vs. niveau admin

Chaque vue possède un attribut `events` auquel vous pouvez vous abonner directement, limité à cette seule vue. L'instance `Admin` en possède également un, qui couvre toutes les vues qui lui sont enregistrées, ou un sous-ensemble si vous passez `keys=`.

* **`view.events.on(...)`** : se déclenche uniquement pour cette vue.
* **`admin.events.on(...)`** : se déclenche pour toutes les vues actuelles et futures, sauf restriction via `keys=`.

Vous pouvez vous inscrire sur `admin.events` avant ou après avoir appelé `admin.add_view(...)`. L'ordre n'a pas d'importance : un gestionnaire enregistré en premier reste attaché à la vue dès que vous l'ajoutez.

## Hooks de méthode vs. abonnements aux événements

Les deux se déclenchent au même moment du cycle de vie de la requête. Ils diffèrent par l'emplacement du code et le nombre de vues touchées.

| Fonctionnalité | Hook de méthode (`before_create`, ...) | Abonnement aux événements (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Emplacement du code** | Dans la classe de la vue | N'importe où, par exemple une fonction au niveau du module ou une classe d'abonné |
| **Portée** | Cette vue spécifique | Une vue (`view.events`) ou toutes les vues (`admin.events`) |
| **Adapté à** | Logique propre à cette ressource (slugifier un titre, horodater) | Préoccupations transversales (journaux d'audit, notifications, plug-ins) |
| **Multiples autorisés ?** | Non, une méthode par vue | Oui, autant de gestionnaires que souhaité par événement, ordonnés par priorité |

Utilisez un hook de méthode lorsque la logique est intrinsèque au modèle. Utilisez un abonnement aux événements lorsqu'elle n'appartient à aucune vue en particulier, ou lorsque vous la livrez comme un composant réutilisable dans plusieurs panneaux d'administration.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## Valeurs d'`AdminEvent`

`AdminEvent` est une énumération de chaînes. Voici les membres activement émis par le cycle de vie des vues :

| Événement | Déclenché lorsque | Classe de contexte |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Enregistrement créé | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Transaction de création validée | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Enregistrement mis à jour | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Transaction de modification validée | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Enregistrement supprimé | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Transaction de suppression validée | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Action groupée ou action de ligne exécutée | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Exportation déclenchée | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Importation déclenchée | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Connexion réussie | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` et `AFTER_DELETE_COMMITTED` ne se déclenchent que pour les backends qui diffèrent la validation à la fin de la requête, ce qui désigne aujourd'hui le backend SQLAlchemy. Consultez [Vues](../user-guide/views.md#lifecycle-hooks) pour connaître les méthodes de hook `after_create_committed`, `after_edit_committed` et `after_delete_committed` qui les émettent.

Pour `AFTER_DELETE_COMMITTED`, `ctx.obj` est une instance détachée : ses attributs déjà chargés restent lisibles, mais la lecture d'un attribut non chargé avant la suppression lève une exception, car la ligne correspondante a disparu.

Chaque contexte est une dataclass qui hérite d'`EventContext`, laquelle porte des champs communs à tous les événements :

| Attribut | Type | Description |
| --- | --- | --- |
| `event` | `AdminEvent` ou `str` | L'événement déclenché |
| `request` | `Request` | La requête en cours |
| `view_key` | `str` | La clé (`key`) de la vue |
| `extra` | `dict` | Vide par défaut, librement utilisable pour stocker des données dans une chaîne de gestionnaires personnalisés |

Chaque sous-classe ajoute les champs propres à son événement.

Les événements de modification déclenchés par une [modification en ligne](../user-guide/inline-edit.md) depuis la page de liste portent `extra["inline"] = True`, et leurs charges utiles `data` / `old_data` ne contiennent que le champ modifié. Tout le reste est identique à une modification classique, si bien que les gestionnaires existants ne nécessitent aucun changement.

## S'abonner avec un décorateur

`view.events.on()` fonctionne aussi bien comme décorateur que comme appel direct de fonction :

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

Enregistré ainsi, `log_deletion` se déclenche uniquement pour `order_view`, pas pour les autres vues du panneau d'administration. La méthode `on()` accepte aussi le gestionnaire directement, sans passer par le décorateur :

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## `AdminEventSubscriber` : regrouper les gestionnaires

Lorsqu'une même préoccupation réagit à plusieurs événements, `AdminEventSubscriber` permet de les rassembler dans une seule classe au lieu de disperser des fonctions au niveau du module. Décorez les méthodes avec `@on(AdminEvent.X)`, où le `on` au niveau du module issu de `starlette_admin.events`, et non la méthode du bus, puis appelez `subscribe()` une fois :

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` est disponible sur `view.events` comme sur `admin.events`. Appelez-le sur `view.events` pour limiter l'abonné à une seule vue.

Une méthode peut gérer plusieurs événements : `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` enregistre la même méthode pour les deux.

## `admin.events` : déléguer aux vues

`admin.events.on()` accepte les mêmes arguments que `view.events.on()`, plus `keys=`, une liste de clés de vues à laquelle restreindre l'abonnement. Laissez-la non définie (`None`, valeur par défaut) et chaque vue de modèle actuelle et future reçoit le gestionnaire :

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Seule la vue enregistrée avec `key="order"`, ou dont la clé par défaut correspond à `"order"`, appelle ce gestionnaire. Un `AFTER_CREATE` sur toute autre vue ne le déclenchera pas.

`admin.events.subscribe()` accepte également `keys=`, ce qui vous permet de limiter un `AdminEventSubscriber` à un sous-ensemble de vues de la même façon :

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` n'affecte que les événements du cycle de vie des vues du tableau ci-dessus : création, modification, suppression, action, exportation et importation. C'est ainsi que `admin.events` détermine les vues auxquelles un gestionnaire s'applique. `AFTER_LOGIN` est un événement de niveau admin et n'est lié à aucune vue ; `keys=` n'a donc aucun effet pour lui.

## Priorité

`on()` accepte un mot-clé `priority`, un entier valant `0` par défaut. Les gestionnaires d'un même événement s'exécutent par ordre de priorité décroissante : un nombre plus élevé se déclenche en premier :

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

Les gestionnaires de priorité identique s'exécutent dans l'ordre d'enregistrement. Les méthodes d'un `AdminEventSubscriber` acceptent une priorité via `@on(AdminEvent.X, priority=10)`, transmise de la même façon.

!!! warning
    Un gestionnaire `BEFORE_DELETE`, ou tout gestionnaire `BEFORE_*`, qui lève une exception interrompt l'opération, et les gestionnaires suivants de cet événement ne s'exécutent pas. Un gestionnaire `AFTER_*` qui lève une exception transforme une modification déjà validée en requête échouée. Si un échec ne doit pas apparaître comme une erreur du panneau d'administration, encapsulez la logique risquée, telle que les appels réseau ou les API tierces, dans son propre bloc `try`/`except` à l'intérieur du gestionnaire.

## Exemple étendu

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) réunit tous les schémas de cette page : surcharges de hooks sur `PostView`, un `AuditSubscriber` enregistré sur `admin.events` pour toutes les vues, un enregistrement direct de gestionnaires pour les avertissements de suppression, d'exportation et d'importation, un gestionnaire limité à `post_view.events` et un `CommentModerationSubscriber` limité à `comment_view.events`. Exécutez-le pour observer l'interaction entre priorité et portée dans une même application.

---

## Pour aller plus loin

* **[Vues](../user-guide/views.md)** : les hooks de méthode `before_*` et `after_*` sur lesquels cette page s'appuie.
* **[Actions](../user-guide/actions.md)** : actions groupées et actions de ligne, qui émettent `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Formulaires en ligne](../user-guide/inline-forms.md)** : enregistrements imbriqués créés en même temps qu'un parent.
