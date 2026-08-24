---
title: Flash-Nachrichten
description: Senden Sie flüchtige Erfolgs-, Warn- oder Fehlermeldungen an Benutzer,
  nachdem Aktionen in starlette-admin abgeschlossen wurden.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Flash-Nachrichten

Flash-Nachrichten geben Benutzern temporäres, einmaliges Feedback, nachdem sie eine Aktion ausgeführt haben, etwa „Post erfolgreich erstellt“ oder „Ungültiger Dateityp“. Eine Nachricht überlebt einen einzelnen HTTP-Redirect, und das Admin-Panel verwirft sie nach der Anzeige.

`flash()` stellt eine Nachricht in die Warteschlange des aktuellen Requests. Das Admin-Panel rendert die Nachricht auf der nächsten Seite, die der Benutzer sieht, und leert dann die Warteschlange. Dieses Muster stammt von Flask-Admin.


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

## Nachrichten-Kategorien

Jede Flash-Nachricht benötigt eine Kategorie. Die Kategorie legt die Farbe des Banners im Standard-Theme fest, sodass Benutzer den Schweregrad auf einen Blick erkennen können.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

Das Argument `category` hat als Defaultwert `"info"`. Es muss genau einer der Werte `success`, `info`, `warning` oder `error` sein. Jeder andere Wert löst einen `ValueError` aus.

## Integrierte CRUD-Nachrichten

Sie müssen `flash()` für Standard-CRUD-Operationen nicht aufrufen. Das Admin-Panel zeigt automatisch eine `success`-Nachricht an, wenn diese Aktionen abgeschlossen sind:

| Aktion | Standardnachricht |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "Worauf `<repr>` aufgelöst wird"
    Die automatischen Nachrichten verwenden die Zeilendarstellung, die `view.repr()` definiert, nicht den Klassennamen des Modells. Beim Erstellen eines Posts erscheint beispielsweise die Flash-Nachricht *„The item 'My First Post' was added successfully“* statt einer generischen *„Post was added successfully“*.

## Flash-Nachrichten in benutzerdefinierten Aktionen verwenden

Handler für benutzerdefinierte Aktionen (`@action` und `@row_action`) geben standardmäßig `None` zurück. Um dem Benutzer Feedback zu geben, rufen Sie `flash()` auf, bevor der Handler zurückkehrt.

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

* **Wenn Sie `flash()` weglassen:** Die Aktion wird trotzdem ausgeführt, aber der Benutzer erhält nach dem Redirect der Seite keine visuelle Bestätigung.
* **Wenn die Aktion fehlschlägt:** Wenn Ihre benutzerdefinierte Aktion ein `ActionFailed` auslöst, fängt das Admin-Panel die Exception ab und zeigt den Exception-String als Fehlerbanner an. Rufen Sie `flash()` nicht in einem `ActionFailed`-Zweig auf, da der Request keinen Redirect durchführt.

## Nachrichten in benutzerdefinierten Templates rendern

Das Basis-Template des Admin-Panels holt die Flash-Nachrichten für Sie ab und rendert sie. Sie müssen sie nur selbst abrufen, wenn Sie eine vollständig [benutzerdefinierte View](custom-views.md) erstellen.

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

Das Lesen der Flash-Warteschlange ist **destruktiv**. Der erste Aufruf von `get_flashed_messages(request)` holt die Nachrichten ab und leert die Warteschlange. Spätere Aufrufe innerhalb desselben Requests geben eine leere Liste zurück, `[]`.

!!! important "Halten Sie Nachrichten kurz"
    Flash-Nachrichten werden in einem signierten, `httponly`-Cookie namens `admin_flash` gespeichert, nicht in der Server-Session. Browser begrenzen die Cookie-Größe auf etwa 4 KB, verwenden Sie Flash-Nachrichten daher nur für kurzes Feedback. Vermeiden Sie lange Strings und große Daten-Payloads. Der Cookie-basierte Ansatz bedeutet auch, dass Flash-Nachrichten ohne `SessionMiddleware` funktionieren.

> Sehen Sie sich [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) für eine lauffähige App an, die `flash()` aus Hooks und benutzerdefinierten Aktionen aufruft.

---

## Was kommt als Nächstes

* **[Actions](actions.md)**: Geschäftslogik über Massen- oder Zeilenaktionen auslösen.
* **[Security](security.md)**: Erfahren Sie, wie `secret_key` sowohl das Flash-Cookie als auch CSRF-Tokens absichert.
* **[Templates](../advanced/templates.md)**: Flash-Banner in Ihren eigenen Layouts rendern.
