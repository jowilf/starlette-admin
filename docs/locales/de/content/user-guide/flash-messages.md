---
title: Flash-Meldungen
description: Senden Sie flüchtige Erfolgs-, Warn- oder Fehlermeldungen an Benutzer,
  nachdem Aktionen in starlette-admin abgeschlossen wurden.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Flash-Meldungen

Flash-Meldungen geben Benutzern temporäres, einmaliges Feedback, nachdem sie eine Aktion ausgeführt haben, etwa „Beitrag erfolgreich erstellt“ oder „Ungültiger Dateityp“. Eine Meldung übersteht genau eine HTTP-Weiterleitung und wird vom Admin nach der Anzeige verworfen.

`flash()` stellt eine Meldung in die Warteschlange des aktuellen Requests. Der Admin rendert die Meldung auf der nächsten Seite, die der Benutzer sieht, und leert anschließend die Warteschlange. Dieses Muster stammt von Flask-Admin.


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

## Meldungskategorien

Jede Flash-Meldung benötigt eine Kategorie. Die Kategorie legt die Farbe des Banners im Standard-Theme fest, sodass Benutzer den Schweregrad auf einen Blick erkennen können.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")
```

Das Argument `category` ist standardmäßig `"info"`. Es muss exakt einer der Werte `success`, `info`, `warning` oder `error` sein. Jeder andere Wert löst einen `ValueError` aus.

## Eingebaute CRUD-Meldungen

Für Standard-CRUD-Operationen müssen Sie `flash()` nicht selbst aufrufen. Der Admin zeigt automatisch eine `success`-Meldung an, sobald diese Aktionen abgeschlossen sind:

| Aktion | Standardmeldung |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "Worauf sich `<repr>` bezieht"
    Die automatischen Meldungen verwenden die Zeilendarstellung, die `view.repr()` definiert, nicht den Klassennamen des Modells. Beim Anlegen eines Beitrags erscheint beispielsweise *„The item 'My First Post' was added successfully"* statt eines generischen *„Post was added successfully"*.

## Verwendung von Flash-Meldungen in eigenen Aktionen

Handler für eigene Aktionen (`@action` und `@row_action`) geben standardmäßig `None` zurück. Um dem Benutzer Feedback zu geben, rufen Sie `flash()` auf, bevor der Handler zurückkehrt.

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

* **Wenn Sie `flash()` weglassen:** Die Aktion läuft weiterhin durch, aber der Benutzer erhält nach der Weiterleitung keine visuelle Bestätigung.
* **Wenn die Aktion fehlschlägt:** Wenn Ihre eigene Aktion `ActionFailed` auslöst, fängt der Admin die Exception ab und zeigt deren Text als Fehlerbanner an. Rufen Sie in einem `ActionFailed`-Zweig kein `flash()` auf, da der Request nicht weitergeleitet wird.

## Rendern von Meldungen in eigenen Templates

Das Basis-Template des Admins holt die Flash-Meldungen ab und rendert sie für Sie. Sie müssen sie nur dann selbst abrufen, wenn Sie eine vollständig [eigene View](custom-views.md) erstellen.

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]
```

Der Lesezugriff auf die Flash-Warteschlange ist **destruktiv**. Der erste Aufruf von `get_flashed_messages(request)` holt die Meldungen ab und leert die Warteschlange. Weitere Aufrufe innerhalb desselben Requests geben eine leere Liste zurück, `[]`.

!!! important "Halten Sie Meldungen kurz"
    Flash-Meldungen werden in einem signierten, `httponly`-Cookie namens `admin_flash` gespeichert, nicht in der Server-Session. Browser begrenzen die Cookie-Größe auf etwa 4 KB, verwenden Sie Flash-Meldungen daher ausschließlich für kurzes Feedback. Vermeiden Sie lange Zeichenketten und große Daten-Payloads. Der Cookie-basierte Ansatz bedeutet außerdem, dass Flash-Meldungen auch ohne `SessionMiddleware` funktionieren.

> Sehen Sie sich [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) für eine lauffähige App an, die `flash()` aus Hooks und eigenen Aktionen aufruft.

---

## Was kommt als Nächstes

* **[Aktionen](actions.md)**: Lösen Sie Geschäftslogik über Bulk- oder Zeilenaktionen aus.
* **[Sicherheit](security.md)**: Erfahren Sie, wie `secret_key` sowohl das Flash-Cookie als auch CSRF-Tokens absichert.
* **[Templates](../advanced/templates.md)**: Rendern Sie Flash-Banner in Ihren eigenen Layouts.
