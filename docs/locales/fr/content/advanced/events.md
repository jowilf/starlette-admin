---
title: Événements
description: Abonnez-vous aux événements globaux du cycle de vie comme AFTER_CREATE
  pour construire des journaux d'audit, des webhooks et des workflows asynchrones.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# Événements

Un hook de méthode comme `before_create` ne s'exécute que pour la vue qui le définit. Le système d'événements permet à du code situé en dehors de cette vue de réagir à ce qui s'y passe : un journal d'audit, un webhook ou une invalidation de cache peut ainsi vivre à un seul endroit au lieu d'être copié-collé dans chaque `ModelView` que vous écrivez.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Enregistrez ceci une seule fois à côté de votre instance `admin` et le endpoint de création de chaque vue l'appellera, y compris les vues que vous ajouterez plus tard.

## Niveau vue ou niveau admin

Chaque vue possède un attribut `events` auquel vous pouvez vous abonner directement, avec une portée limitée à cette seule vue. L'instance `Admin` en possède également un, qui touche toutes les vues qui lui sont enregistrées, ou un sous-ensemble si vous passez `keys=`.

* **`view.events.on(...)`** : Se déclenche uniquement pour cette vue.
* **`admin.events.on(...)`** : Se déclenche pour toutes les vues actuelles et futures, sauf si vous le restreignez avec `keys=`.

Vous pouvez vous enregistrer sur `admin.events` avant ou après avoir appelé `admin.add_view(...)`. L'ordre n'a pas d'importance : un handler enregistré en premier s'attachera quand même à la vue dès que vous l'ajouterez.

## Hooks de méthode et abonnements aux événements

Les deux se déclenchent au même moment du cycle de vie de la requête. Ils diffèrent par l'endroit où réside le code et par le nombre de vues qu'ils atteignent.

| Caractéristique | Hook de méthode (`before_create`, ...) | Abonnement aux événements (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Emplacement du code** | Dans la classe de la vue | N'importe où, par exemple une fonction au niveau module ou une classe subscriber |
| **Portée** | Cette vue spécifique | Une vue (`view.events`) ou toutes les vues (`admin.events`) |
| **Adapté à** | Logique propre à cette ressource (slugifier un titre, horodater) | Préoccupations transversales (journaux d'audit, notifications, plugins) |
| **Multiples autorisés ?** | Non, une méthode par vue | Oui, autant de handlers que souhaité par événement, ordonnés par priorité |

Utilisez un hook de méthode lorsque la logique est intrinsèque au modèle. Utilisez un abonnement aux événements lorsqu'elle n'appartient à aucune vue en particulier, ou lorsque vous la livrez comme un composant réutilisable sur plusieurs admins.

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

## Valeurs de AdminEvent

`AdminEvent` est une énumération de chaînes. Voici les membres activement émis par le cycle de vie des vues :

| Événement | Déclenché quand | Classe de contexte |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Enregistrement créé | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Transaction de création validée (commit) | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Enregistrement mis à jour | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Transaction de modification validée (commit) | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Enregistrement supprimé | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Transaction de suppression validée (commit) | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Action de lot ou de ligne exécutée | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Export déclenché | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Import déclenché | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Connexion réussie | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` et `AFTER_DELETE_COMMITTED` ne se déclenchent que pour les backends qui repoussent le commit à la fin de la requête, ce qui désigne aujourd'hui le backend SQLAlchemy. Consultez [Views](../user-guide/views.md#lifecycle-hooks) pour connaître les méthodes de hook `after_create_committed`, `after_edit_committed` et `after_delete_committed` qui les émettent.

Pour `AFTER_DELETE_COMMITTED`, `ctx.obj` est une instance détachée : ses attributs déjà chargés restent lisibles, mais la lecture d'un attribut qui n'était pas chargé avant la suppression lève une exception, car la ligne sous-jacente a disparu.

Chaque contexte est une dataclass qui hérite de `EventContext`, laquelle porte des champs communs à tous les événements :

| Attribut | Type | Description |
| --- | --- | --- |
| `event` | `AdminEvent` ou `str` | L'événement qui s'est déclenché |
| `request` | `Request` | La requête en cours |
| `view_key` | `str` | Le `key` de la vue |
| `extra` | `dict` | Vide par défaut, à votre libre disposition pour stocker des données dans une chaîne de handlers personnalisée |

Chaque sous-classe ajoute les champs propres à son événement.

Les événements de modification déclenchés par une [modification inline](../user-guide/inline-edit.md) depuis la page de liste portent `extra["inline"] = True`, et leurs payloads `data` / `old_data` ne contiennent que le champ modifié. Tout le reste est identique à une modification classique ; les handlers existants ne nécessitent donc aucun changement.

## Abonnement via un décorateur

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

Enregistré ainsi, `log_deletion` ne se déclenche que pour `order_view`, pas pour les autres vues de l'admin. La méthode `on()` accepte également le handler directement, sans passer par la forme décorateur :

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber : regrouper les handlers

Lorsqu'une même préoccupation réagit à plusieurs événements, `AdminEventSubscriber` permet de les rassembler dans une seule classe au lieu de disperser des fonctions au niveau module. Décorez les méthodes avec `@on(AdminEvent.X)`, le `on` au niveau module issu de `starlette_admin.events` plutôt que la méthode du bus, puis appelez `subscribe()` une seule fois :

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

`subscribe()` est disponible aussi bien sur `view.events` que sur `admin.events`. Appelez-le sur `view.events` pour limiter le subscriber à une seule vue.

Une même méthode peut gérer plusieurs événements : `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` enregistre la même méthode pour les deux.

## admin.events : délégation aux vues

`admin.events.on()` accepte les mêmes arguments que `view.events.on()`, plus `keys=`, une liste de clés de vues à laquelle restreindre l'abonnement. Laissez-la non renseignée (`None`, la valeur par défaut) et chaque vue de modèle, actuelle comme future, reçoit le handler :

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Seule la vue enregistrée avec `key="order"`, ou dont la clé par défaut correspond à `"order"`, appelle ce handler. Un `AFTER_CREATE` sur toute autre vue ne le déclenchera pas.

`admin.events.subscribe()` accepte également `keys=`, ce qui vous permet de limiter un `AdminEventSubscriber` à un sous-ensemble de vues de la même manière :

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` n'affecte que les événements de cycle de vie des vues du tableau ci-dessus : create, edit, delete, action, export et import. C'est ainsi que `admin.events` détermine à quelles vues un handler s'applique. `AFTER_LOGIN` est de niveau admin et n'est lié à aucune vue ; `keys=` n'a donc aucun effet pour cet événement.

## Priorité

`on()` accepte un mot-clé `priority`, un entier valant `0` par défaut. Les handlers d'un même événement s'exécutent par ordre de priorité décroissante : un nombre plus élevé se déclenche en premier :

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

Les handlers de même priorité s'exécutent dans leur ordre d'enregistrement. Les méthodes de `AdminEventSubscriber` acceptent une priorité via `@on(AdminEvent.X, priority=10)`, qui est transmise de la même façon.

!!! warning
    Un handler `BEFORE_DELETE`, ou tout handler `BEFORE_*`, qui lève une exception interrompt l'opération, et les handlers suivants de cet événement ne s'exécutent pas. Un handler `AFTER_*` qui lève une exception transforme une modification déjà validée (committed) en requête échouée. Si un échec ne doit pas apparaître comme une erreur admin, encapsulez la logique à risque, telle que des appels réseau ou des API tierces, dans son propre bloc `try`/`except` au sein du handler.

## Exemple complet

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) met en œuvre ensemble tous les schémas de cette page : des surcharges de hooks sur `PostView`, un `AuditSubscriber` enregistré sur `admin.events` pour toutes les vues, un enregistrement direct de handlers pour les avertissements de suppression, d'export et d'import, un handler limité à `post_view.events`, et un `CommentModerationSubscriber` limité à `comment_view.events`. Exécutez-le pour observer l'interaction entre priorité et portée au sein d'une même application.

---

## Et ensuite ?

* **[Views](../user-guide/views.md)** : Les hooks de méthode `before_*` et `after_*` sur lesquels cette page s'appuie.
* **[Actions](../user-guide/actions.md)** : Les actions de lot et de ligne, qui émettent `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Inline Forms](../user-guide/inline-forms.md)** : Les enregistrements imbriqués créés en même temps qu'un parent.
