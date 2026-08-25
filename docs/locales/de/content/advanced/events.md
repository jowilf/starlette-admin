---
title: Events
description: Abonnieren Sie globale Lebenszyklus-Ereignisse wie AFTER_CREATE, um Audit-Logs,
  Webhooks und asynchrone Workflows zu erstellen.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# Events

Ein Methoden-Hook wie `before_create` wird nur für die View ausgeführt, die ihn definiert. Das Event-System ermöglicht es Code außerhalb dieser View, auf das Geschehen darin zu reagieren – ein Audit-Log, ein Webhook oder eine Cache-Invalidierung kann so an einem einzigen Ort leben, statt in jede `ModelView` kopiert zu werden, die Sie schreiben.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Registrieren Sie dies einmalig neben Ihrer `admin`-Instanz, und der Create-Endpoint jeder View ruft es auf – einschließlich der Views, die Sie später hinzufügen.

## View- vs. Admin-Ebene

Jede View besitzt ein `events`-Attribut, das Sie direkt abonnieren können; dessen Gültigkeit ist auf diese einzelne View beschränkt. Die `Admin`-Instanz verfügt ebenfalls über eines, das alle bei ihr registrierten Views erreicht – oder eine Teilmenge davon, wenn Sie `keys=` übergeben.

* **`view.events.on(...)`**: Wird nur für diese View ausgelöst.
* **`admin.events.on(...)`**: Wird für jede aktuelle und zukünftige View ausgelöst, sofern Sie es nicht mit `keys=` einschränken.

Sie können sich sowohl vor als auch nach dem Aufruf von `admin.add_view(...)` bei `admin.events` registrieren. Die Reihenfolge spielt keine Rolle: Ein zuerst registrierter Handler wird dennoch an die View angehängt, sobald Sie sie hinzufügen.

## Methoden-Hooks vs. Event-Abonnements

Beide werden am selben Punkt im Request-Lifecycle ausgelöst. Sie unterscheiden sich darin, wo der Code lebt und wie viele Views er erreicht.

| Merkmal | Methoden-Hook (`before_create`, ...) | Event-Abonnement (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Wo der Code lebt** | Innerhalb der View-Klasse | Beliebig, zum Beispiel eine Funktion auf Modulebene oder eine Subscriber-Klasse |
| **Gültigkeitsbereich** | Diese spezifische View | Eine View (`view.events`) oder jede View (`admin.events`) |
| **Geeignet für** | Logik, die spezifisch für diese Ressource ist (einen Titel slugifizieren, einen Zeitstempel setzen) | Querschnittsanliegen (Audit-Logs, Benachrichtigungen, Plugins) |
| **Mehrfach erlaubt?** | Nein, eine Methode pro View | Ja, beliebig viele Handler pro Event, sortiert nach Priorität |

Verwenden Sie einen Methoden-Hook, wenn die Logik dem Modell inhärent ist. Verwenden Sie ein Event-Abonnement, wenn sie zu keiner einzelnen View gehört oder wenn Sie sie als wiederverwendbares Bauteil über mehrere Admins hinweg ausliefern.

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

## AdminEvent-Werte

`AdminEvent` ist ein String-Enum. Dies sind die Member, die vom View-Lifecycle aktiv ausgelöst werden:

| Event | Ausgelöst, wenn | Context-Klasse |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Datensatz erstellt | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Create-Transaktion committet | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Datensatz aktualisiert | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Edit-Transaktion committet | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Datensatz gelöscht | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Delete-Transaktion committet | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Batch- oder Row-Action ausgeführt | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Export ausgelöst | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Import ausgelöst | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Login erfolgreich | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` und `AFTER_DELETE_COMMITTED` werden nur von Backends ausgelöst, die den Commit bis zum Ende des Requests zurückstellen – heute bedeutet das das SQLAlchemy-Backend. Siehe [Views](../user-guide/views.md#lifecycle-hooks) für die Hook-Methoden `after_create_committed`, `after_edit_committed` und `after_delete_committed`, die diese Events auslösen.

Bei `AFTER_DELETE_COMMITTED` ist `ctx.obj` eine detached Instanz: Ihre bereits geladenen Attribute bleiben lesbar, aber der Lesezugriff auf ein Attribut, das vor dem Löschen nicht geladen wurde, löst einen Fehler aus, da die zugrunde liegende Zeile nicht mehr existiert.

Jeder Context ist eine Dataclass, die von `EventContext` erbt und Felder enthält, die allen Events gemeinsam sind:

| Attribut | Typ | Beschreibung |
| --- | --- | --- |
| `event` | `AdminEvent` oder `str` | Das ausgelöste Event |
| `request` | `Request` | Der Request in Bearbeitung |
| `view_key` | `str` | Der `key` der View |
| `extra` | `dict` | Standardmäßig leer; frei verfügbar, um Daten in einer eigenen Handler-Kette abzulegen |

Jede Subklasse ergänzt die für das jeweilige Event relevanten Felder.

Edit-Events, die durch eine [Inline-Bearbeitung](../user-guide/inline-edit.md) von der Listenseite ausgelöst werden, enthalten `extra["inline"] = True`, und ihre `data`-/`old_data`-Payloads umfassen nur das bearbeitete Feld. Alles andere ist identisch mit einer regulären Bearbeitung, sodass bestehende Handler keine Änderungen benötigen.

## Abonnieren mit einem Decorator

`view.events.on()` funktioniert sowohl als Decorator als auch als direkter Funktionsaufruf:

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

Auf diese Weise registriert, wird `log_deletion` nur für `order_view` ausgelöst, nicht für andere Views des Admins. Die Methode `on()` akzeptiert den Handler auch direkt, ohne die Decorator-Form:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: Handler gruppieren

Wenn ein Anliegen auf mehrere Events reagiert, hält `AdminEventSubscriber` diese in einer einzigen Klasse zusammen, statt Funktionen auf Modulebene zu verstreuen. Dekorieren Sie die Methoden mit `@on(AdminEvent.X)` – dem modulweiten `on` aus `starlette_admin.events`, nicht der Bus-Methode – und rufen Sie anschließend einmal `subscribe()` auf:

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

`subscribe()` ist sowohl auf `view.events` als auch auf `admin.events` verfügbar. Rufen Sie es auf `view.events` auf, um den Subscriber stattdessen auf eine einzelne View zu beschränken.

Eine Methode kann mehrere Events behandeln: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` registriert dieselbe Methode für beide.

## admin.events: Delegation an Views

`admin.events.on()` akzeptiert dieselben Argumente wie `view.events.on()`, zusätzlich jedoch `keys=` – eine Liste von View-Keys, auf die das Abonnement beschränkt wird. Lassen Sie es ungesetzt (`None`, der Standardwert), erhält jede aktuelle und zukünftige Model-View den Handler:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Nur die View, die mit `key="order"` registriert ist – oder deren Standard-Key zu `"order"` aufgelöst wird –, ruft diesen Handler auf. Ein `AFTER_CREATE` auf einer anderen View löst ihn nicht aus.

Auch `admin.events.subscribe()` akzeptiert `keys=`, sodass Sie einen `AdminEventSubscriber` auf dieselbe Weise auf eine Teilmenge von Views beschränken können:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` wirkt sich nur auf die View-Lifecycle-Events in der obigen Tabelle aus: create, edit, delete, action, export und import. Daran entscheidet `admin.events`, für welche Views ein Handler gilt. `AFTER_LOGIN` liegt auf Admin-Ebene und ist an keine View gebunden, daher hat `keys=` darauf keine Wirkung.

## Priorität

`on()` nimmt ein `priority`-Keyword entgegen, einen Integer mit dem Standardwert `0`. Handler für dasselbe Event werden in absteigender Prioritätsreihenfolge ausgeführt, sodass eine höhere Zahl zuerst ausgelöst wird:

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

Handler mit derselben Priorität werden in Registrierungsreihenfolge ausgeführt. Methoden eines `AdminEventSubscriber` erhalten eine Priorität über `@on(AdminEvent.X, priority=10)`, die auf dieselbe Weise weitergereicht wird.

!!! warning
    Ein `BEFORE_DELETE`-Handler – oder jeder andere `BEFORE_*`-Handler –, der eine Exception auslöst, stoppt die Operation, und nachfolgende Handler für dieses Event werden nicht mehr ausgeführt. Ein `AFTER_*`-Handler, der eine Exception auslöst, verwandelt eine bereits committete Änderung in einen fehlgeschlagenen Request. Sollte ein Fehler nicht als Admin-Fehler sichtbar werden, umschließen Sie riskante Logik wie Netzwerkaufrufe oder Third-Party-APIs innerhalb des Handlers mit einem eigenen `try`/`except`-Block.

## Erweitertes Beispiel

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) führt alle Muster dieser Seite gemeinsam aus: Hook-Overrides auf `PostView`, einen auf `admin.events` für alle Views registrierten `AuditSubscriber`, die direkte Handler-Registrierung für Delete-, Export- und Import-Warnungen, einen auf `post_view.events` beschränkten Handler sowie einen auf `comment_view.events` beschränkten `CommentModerationSubscriber`. Führen Sie es aus, um zu beobachten, wie Priorität und Gültigkeitsbereich in einer App zusammenwirken.

---

## Was kommt als Nächstes?

* **[Views](../user-guide/views.md)**: Die `before_*`- und `after_*`-Methoden-Hooks, auf denen diese Seite aufbaut.
* **[Actions](../user-guide/actions.md)**: Batch- und Row-Actions, die `BEFORE_ACTION` / `AFTER_ACTION` auslösen.
* **[Inline Forms](../user-guide/inline-forms.md)**: Verschachtelte Datensätze, die zusammen mit einem übergeordneten Datensatz erstellt werden.
