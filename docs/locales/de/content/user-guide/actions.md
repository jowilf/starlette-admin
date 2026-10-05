---
title: Aktionen
description: Führen Sie Batch- und zeilenbezogene Operationen mit eigenen Bestätigungen
  und Formularen direkt aus der Listenansicht aus.
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# Aktionen

Aktionen bieten Ihnen einen direkten Weg, mit Ihren Datenbankdatensätzen aus der Admin-Oberfläche zu arbeiten, sodass Benutzer Operationen wie Massenlöschungen, Bulk-Updates und den Versand von E-Mails ausführen können.

## `ActionSelection` verstehen

`ActionSelection` ist das zentrale Objekt der Actions-API. Statt einer rohen Liste von Primärschlüsseln erhält Ihr Handler eine `ActionSelection`-Instanz.

Das Objekt wird lazy aufgelöst und verhält sich identisch, unabhängig davon, ob der Benutzer Zeilen einzeln angehakt oder „alle passenden auswählen" verwendet hat. Es stellt Ihrem Handler außerdem die aktiven Filter der Listenseite zur Verfügung.

### `ActionSelection` API-Referenz

| Methode oder Eigenschaft  | Beschreibung                                                                    |
| ------------------------- | ------------------------------------------------------------------------------- |
| `await selection.rows()`  | Ruft die Zielzeilen ab. Wird einmal geladen und anschließend gecacht.           |
| `await selection.pks()`   | Ruft die Primärschlüssel der Zielzeilen ab.                                     |
| `await selection.count()` | Gibt die Gesamtzahl der Zeilen zurück, auf die die Aktion abzielt.              |
| `selection.is_select_all` | Ein boolescher Wert, der angibt, ob der Benutzer „alle passenden auswählen" gewählt hat. |
| `selection.filters`       | Die aktive `FilterGroup`, identisch mit `ListParams.filters`.                   |
| `selection.q`             | Der aktive Volltext-Suchbegriff oder `None`, wenn die Suche inaktiv ist.        |

## Batch-Aktionen

Standardmäßig aktualisieren Benutzer ein Objekt, indem sie es auf der Listenseite auswählen und es einzeln bearbeiten. Um dieselbe Änderung auf viele Objekte gleichzeitig anzuwenden, fügen Sie eine eigene **Batch-Aktion** hinzu.

!!! note
    `starlette-admin` fügt standardmäßig eine `delete`-Batch-Aktion hinzu.

Um eine eigene Batch-Aktion zu Ihrer `ModelView` hinzuzufügen, schreiben Sie eine asynchrone Funktion mit Ihrer Logik und umschließen Sie sie mit dem `@action`-Decorator.

!!! important
    Namen von Batch-Aktionen müssen innerhalb einer `ModelView` eindeutig sein.

### Beispiel für eine Batch-Aktion

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

## Globale Aktionen

Eine Standard-Batch-Aktion benötigt eine aktive Auswahl: Das Dropdown-Menü **With selected** erscheint nur, wenn mindestens eine Zeile angehakt ist. Wenn eine Aktion stattdessen die gesamte Sammlung betrifft – etwa eine vollständige Datenbank-Synchronisation –, machen Sie daraus eine globale Aktion.

Setzen Sie `allow_empty_selection=True` im `@action`-Decorator. Globale Aktionen werden in einem stets sichtbaren Dropdown-Menü **Actions** dargestellt und laufen ohne Zeilenauswahl.

**Verhalten des Handlers bei globalen Aktionen:**

- **Leere Auswahl:** Das `selection`-Objekt kann zu null Zeilen aufgelöst werden.
- **Zufällige Auswahlen:** Hat der Benutzer beim Auslösen einer globalen Aktion Zeilen angehakt, erhält der Handler diese Zeilen dennoch. Ignorieren Sie `selection` explizit, wenn Ihre Logik die gesamte Sammlung betrifft.

Alle übrigen Parameter (`confirmation`, `form`, `custom_response` und `is_action_allowed`) funktionieren genau wie bei einer Standard-Batch-Aktion.

**Eigene Toolbar-Schaltflächen:** Setzen Sie `dedicated_button=True`, um eine globale Aktion als eigene Toolbar-Schaltfläche statt als Eintrag im Dropdown-Menü **Actions** darzustellen. Die eingebaute Export-Aktion nutzt diese Option. Die Kombination von `dedicated_button=True` mit einer nur für Auswahlen verfügbaren Aktion führt beim Start zu einem Fehler.

### Beispiel für eine globale Aktion

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

### Die Funktion „alle passenden auswählen"

Wenn ein Benutzer alle Zeilen der aktuellen Seite anhakt und weitere Zeilen den Filter an anderer Stelle erfüllen, bietet die Oberfläche an, alle passenden Zeilen auszuwählen.

Diese Option sendet `all=1` an die Action-API statt einer Liste von Primärschlüsseln. Verwenden Sie `selection.is_select_all`, um Ihre Logik zu verzweigen, oder lassen Sie `selection.rows()` die Daten in beiden Fällen auflösen:

```python
@action(name="archive", text="Archive")
async def archive_action(self, request: Request, selection: ActionSelection) -> None:
    if selection.is_select_all:
        await self.bulk_archive_where(request, selection.filters, selection.q)
    else:
        await self.bulk_archive_pks(request, await selection.pks())
```

!!! important "Materialisierungsgrenzen"
    Im Select-all-Modus sind `selection.rows()`, `pks()` und `count()` durch `action_select_all_limit` begrenzt, das standardmäßig auf 1000 gesetzt ist. Eine Überschreitung des Limits löst eine `ActionFailed`-Exception aus. Ein Handler, der ausschließlich `selection.filters` und `selection.q` liest, materialisiert nichts, sodass das Limit nicht greift.

## Zeilenaktionen {#row-actions}

Zeilenaktionen ermöglichen es Benutzern, direkt aus der Listenansicht auf ein einzelnes Element zu operieren. `starlette-admin` enthält standardmäßig drei Zeilenaktionen: `view`, `edit` und `delete`.

Um eine eigene Zeilenaktion hinzuzufügen, schreiben Sie Ihre Logik und wenden den `@row_action`-Decorator an. Wenn die Aktion den Benutzer lediglich zu einer anderen URL weiterleitet, verwenden Sie stattdessen den `@link_row_action`-Decorator. Er bettet den Link in das HTML-Attribut `href` ein und umgeht die Action-API.

!!! important
    Namen von Zeilenaktionen müssen innerhalb einer `ModelView` eindeutig sein.

### Beispiel für eine Zeilenaktion

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

### Zeilenaktionen einschränken

Zwei Hooks steuern, ob eine Zeilenaktion verfügbar ist. Beide erlauben die Aktion standardmäßig.

1. **`is_row_action_allowed(request, name)`**: Wird einmal pro Aktionsname ausgeführt. Verwenden Sie ihn für Einschränkungen, die nicht von der Zeile abhängen, etwa rollenbasierte Zugriffskontrolle.
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: Wird einmal pro Zeile für die Aktionen ausgeführt, die die erste Prüfung bestanden haben. Verwenden Sie ihn für datenabhängige Einschränkungen, etwa das Ausblenden einer Schaltfläche **Publish** bei einem bereits veröffentlichten Artikel.

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
    Rufen Sie `super()` immer für Aktionsnamen auf, die Ihre Überschreibung nicht behandelt. Andernfalls deaktivieren Sie stillschweigend die Berechtigungsprüfungen der eingebauten Aktionen.

## UI-Konfiguration für Zeilenaktionen

### Anzeigetypen

Der Parameter `row_actions_display_type` legt fest, wie Aktionen auf der Listenseite erscheinen. Aktionen auf Detailseiten werden immer als vollständige Schaltflächen dargestellt.

| Anzeigetyp     | Beschreibung                                                                       |
| -------------- | ---------------------------------------------------------------------------------- |
| `ICON_LIST`    | Rendert eine horizontale Liste von Schaltflächen, die nur aus Icons bestehen.      |
| `DROPDOWN`     | Gruppiert Aktionen in einem beschrifteten Dropdown-Menü.                           |
| `KEBAB`        | Gruppiert Aktionen in einem Dropdown-Menü, das über ein `⋮`-Icon geöffnet wird.    |
| `INLINE_LINKS` | Rendert das Aktionslabel unterhalb des Icons, getrennt durch einen Mittelpunkt.    |

### Spaltenpositionierung

Standardmäßig wird die Aktionsspalte vor Ihren Datenspalten gerendert. Um sie an die rechte Seite der Tabelle zu verschieben, verwenden Sie `RowActionsPosition`:

```python
from starlette_admin.types import RowActionsPosition


class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS
```

## Dynamische Aktionsformulare

Der Parameter `form` akzeptiert sowohl beim `@action`- als auch beim `@row_action`-Decorator ein Callable, sodass Sie das HTML zur Laufzeit des Requests generieren können.

Das Callable kann synchron oder asynchron sein und muss einen String zurückgeben.

- **Signatur von `@action`**: `(request) -> str`
- **Signatur von `@row_action`**: `(request, obj) -> str`

Verwenden Sie ein Callable, wenn Sie Formularfelder mit den aktuellen Werten einer Zeile vorbelegen möchten.

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
    Ein Callable für ein Zeilenaktionsformular wird einmal pro Zeile auf der Listenseite ausgeführt. Halten Sie es schnell und vermeiden Sie Datenbankabfragen darin. Die benötigten Zeilendaten stehen Ihnen bereits über den Parameter `obj` zur Verfügung.
