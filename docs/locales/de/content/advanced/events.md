---
title: Events
description: Globale Lifecycle-Events wie AFTER_CREATE abonnieren, um Audit-Logs,
  Webhooks und asynchrone Workflows zu erstellen.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Ein Methoden-Hook wie `before_create` läuft nur für die View, die ihn definiert. Das Event-System ermöglicht es, dass Code außerhalb dieser View auf das reagiert, was in ihr passiert. Das bedeutet: Ein Audit-Log, ein Webhook oder eine Cache-Invalidierung kann an einem Ort leben, statt in jede `ModelView`, die Sie schreiben, kopiert zu werden.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Registrieren Sie dies einmal neben Ihrer `admin`-Instanz, und der Create-Endpoint jeder View ruft es auf, einschließlich der Views, die Sie später hinzufügen.

## View vs. Admin-Ebene

Jede View hat ein `events`-Attribut, das Sie direkt abonnieren können, beschränkt auf diese View allein. Die `Admin`-Instanz hat ebenfalls eines, das jede bei ihr registrierte View erreicht, oder eine Teilmenge, wenn Sie `keys=` übergeben.

* **`view.events.on(...)`**: Löst nur für diese View aus.
* **`admin.events.on(...)`**: Löst für jede aktuelle und zukünftige View aus, sofern Sie es nicht mit `keys=` einschränken.

Sie können sich vor oder nach dem Aufruf von `admin.add_view(...)` auf `admin.events` registrieren. Die Reihenfolge spielt keine Rolle: Ein Handler, der zuerst registriert wurde, verbindet sich trotzdem mit der View, sobald Sie sie hinzufügen.

## Methoden-Hooks vs. Event-Abonnements

Beide werden am selben Punkt im Request-Lifecycle ausgelöst. Sie unterscheiden sich darin, wo der Code lebt und wie viele Views er erreicht.

| Merkmal | Methoden-Hook (`before_create`, ...) | Event-Abonnement (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Wo der Code lebt** | Innerhalb der View-Klasse | Beliebig, zum Beispiel eine Funktion auf Modulebene oder eine Subscriber-Klasse |
| **Geltungsbereich** | Diese spezifische View | Eine View (`view.events`) oder jede View (`admin.events`) |
| **Geeignet für** | Logik, die spezifisch für diese Ressource ist (einen Titel slugifizieren, einen Zeitstempel setzen) | Querschnittsthemen (Audit-Logs, Benachrichtigungen, Plugins) |
| **Mehrere erlaubt?** | Nein, eine Methode pro View | Ja, beliebig viele Handler pro Event, sortiert nach Priorität |

Verwenden Sie einen Methoden-Hook, wenn die Logik dem Modell inhärent ist. Verwenden Sie ein Event-Abonnement, wenn sie nicht zu einer einzelnen View gehört, oder wenn Sie sie als wiederverwendbares Bauteil über mehrere Admins hinweg ausliefern.

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

`AdminEvent` ist ein String-Enum. Dies sind die Member, die aktiv vom View-Lifecycle emittiert werden:

| Event | Ausgelöst, wenn | Context-Klasse |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Datensatz erstellt | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Create-Transaktion committed | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Datensatz aktualisiert | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Edit-Transaktion committed | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Datensatz gelöscht | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Delete-Transaktion committed | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Massenaktion oder Zeilenaktion ausgeführt | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Export ausgelöst | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Import ausgelöst | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Login erfolgreich | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` und `AFTER_DELETE_COMMITTED` werden nur von Backends ausgelöst, die den Commit bis zum Ende des Requests aufschieben, was heute das SQLAlchemy-Backend bedeutet. Siehe [Views](../user-guide/views.md#lifecycle-hooks) für die Hook-Methoden `after_create_committed`, `after_edit_committed` und `after_delete_committed`, die diese emittieren.

Bei `AFTER_DELETE_COMMITTED` ist `ctx.obj` eine detached Instanz: Ihre bereits geladenen Attribute bleiben lesbar, aber das Lesen eines Attributs, das vor dem Delete nicht geladen wurde, löst einen Fehler aus, weil die Zeile dahinter verschwunden ist.

Jeder Context ist eine Dataclass, die von `EventContext` erbt und Felder enthält, die allen Events gemeinsam sind:

| Attribut | Typ | Beschreibung |
| --- | --- | --- |
| `event` | `AdminEvent` oder `str` | Das Event, das ausgelöst wurde |
| `request` | `Request` | Der Request in Bearbeitung |
| `view_key` | `str` | Der `key` der View |
| `extra` | `dict` | Standardmäßig leer, frei für Sie, um Daten in einer benutzerdefinierten Handler-Kette abzulegen |

Jede Subklasse ergänzt die Felder, die für dieses Event relevant sind.

Edit-Events, die durch eine [Inline-Bearbeitung](../user-guide/inline-edit.md) von der Listenseite ausgelöst werden, enthalten `extra["inline"] = True`, und ihre `data`- bzw. `old_data`-Payloads enthalten nur das bearbeitete Feld. Alles andere ist identisch mit einem regulären Edit, sodass bestehende Handler keine Änderungen benötigen.

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

Wenn ein Anliegen auf mehrere Events reagiert, hält `AdminEventSubscriber` diese in einer einzigen Klasse zusammen, statt Funktionen auf Modulebene zu verstreuen. Dekorieren Sie die Methoden mit `@on(AdminEvent.X)`, wobei dies das Modul-Level-`on` aus `starlette_admin.events` ist und nicht die Bus-Methode, und rufen Sie dann einmal `subscribe()` auf:

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

`subscribe()` ist sowohl auf `view.events` als auch auf `admin.events` verfügbar. Rufen Sie es auf `view.events` auf, um den Subscriber auf eine einzelne View zu beschränken.

Eine Methode kann mehrere Events behandeln: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` registriert dieselbe Methode für beide.

## admin.events: Delegation an Views

`admin.events.on()` nimmt dieselben Argumente wie `view.events.on()`, plus `keys=`, eine Liste von View-Keys, auf die das Abonnement eingeschränkt wird. Lassen Sie es ungesetzt (`None`, der Defaultwert), dann erhält jede aktuelle und zukünftige Modell-View den Handler:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Nur die View, die mit `key="order"` registriert ist, oder deren Default-Key zu `"order"` aufgelöst wird, ruft diesen Handler auf. Ein `AFTER_CREATE` auf einer anderen View löst ihn nicht aus.

`admin.events.subscribe()` akzeptiert ebenfalls `keys=`, sodass Sie einen `AdminEventSubscriber` auf dieselbe Weise auf eine Teilmenge von Views beschränken können:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` wirkt sich nur auf die View-Lifecycle-Events in der Tabelle oben aus: Create, Edit, Delete, Action, Export und Import. So entscheidet `admin.events`, auf welche Views ein Handler angewendet wird. `AFTER_LOGIN` liegt auf Admin-Ebene und ist an keine View gebunden, daher hat `keys=` darauf keine Auswirkung.

## Priorität

`on()` nimmt ein `priority`-Keyword entgegen, ein Integer, der standardmäßig `0` beträgt. Handler für dasselbe Event laufen in absteigender Prioritätsreihenfolge, sodass eine höhere Zahl zuerst auslöst:

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

Handler mit derselben Priorität laufen in Registrierungsreihenfolge. Methoden von `AdminEventSubscriber` nehmen eine Priorität über `@on(AdminEvent.X, priority=10)` entgegen, die auf dieselbe Weise weitergeleitet wird.

!!! warning
    Ein `BEFORE_DELETE`-Handler, oder jeder andere `BEFORE_*`-Handler, der eine Exception auslöst, stoppt die Operation, und spätere Handler für dieses Event laufen nicht. Ein `AFTER_*`-Handler, der eine Exception auslöst, verwandelt eine bereits committete Änderung in einen fehlgeschlagenen Request. Wenn ein Fehler nicht als Admin-Fehler auftauchen soll, wrappen Sie riskante Logik wie Netzwerkaufrufe oder Third-Party-APIs in einen eigenen `try`/`except`-Block innerhalb des Handlers.

## Erweitertes Beispiel

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) führt alle Muster dieser Seite gemeinsam aus: Hook-Überschreibungen auf `PostView`, einen auf `admin.events` für jede View registrierten `AuditSubscriber`, direkte Handler-Registrierungen für Delete-, Export- und Import-Warnungen, einen auf `post_view.events` beschränkten Handler sowie einen auf `comment_view.events` beschränkten `CommentModerationSubscriber`. Führen Sie es aus, um zu sehen, wie Priorität und Geltungsbereich in einer App interagieren.

---

## Was kommt als Nächstes

* **[Views](../user-guide/views.md)**: Die `before_*`- und `after_*`-Methoden-Hooks, auf denen diese Seite aufbaut.
* **[Actions](../user-guide/actions.md)**: Massenaktionen und Zeilenaktionen, die `BEFORE_ACTION` / `AFTER_ACTION` emittieren.
* **[Inline Forms](../user-guide/inline-forms.md)**: Verschachtelte Datensätze, die zusammen mit einem Parent erstellt werden.
