---
title: Inline-Bearbeitung
description: Ermöglichen Sie es Benutzern, Feldwerte direkt in der Tabelle der Listenseite
  zu bearbeiten, um die Dateneingabe zu beschleunigen.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Inline-Bearbeitung

Die Inline-Bearbeitung ermöglicht es Benutzern, ein einzelnes Feld direkt auf der Listenseite zu ändern. Beim Auswählen einer Zelle öffnet sich ein kleines Popover, sodass niemand das vollständige Bearbeitungsformular öffnen muss. Verwenden Sie sie für schnelle Aktualisierungen eines einzelnen Felds: einen Titel korrigieren, einen Status umschalten oder ein Datum anpassen. Die Interaktion folgt dem bekannten [x-editable](https://vitalets.github.io/x-editable/)-Muster.

Das Feature ist opt-in und standardmäßig deaktiviert. Das Aktivieren ändert nicht die Standard-Bearbeitungsseite, die weiterhin das Haupt-Interface für komplexe Bearbeitungen mehrerer Felder bleibt.

> Ein lauffähiges Beispiel mit Inline-Bearbeitung finden Sie unter [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Grundlegende Verwendung

Deklarieren Sie die bearbeitbaren Feldnamen in der Liste `inline_editable_fields`:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Bearbeitbare Zellen zeigen dann auf der Listenseite eine gestrichelte Unterstreichung. Beim Auswählen einer Zelle öffnet sich ein Popover mit dem Standardformular-Steuerelement des Felds, vorausgefüllt mit dem aktuellen Wert.

Die Unterstreichung wird nicht über die gesamte Zelle gezeichnet. Jedes Listentemplate setzt die CSS-Klasse `inline-edit-value` auf genau das Element, das unterstrichen werden soll, und der Stil gilt nur innerhalb einer bearbeitbaren Zelle. Alle integrierten Listentemplates enthalten die Klasse bereits. Wenn Sie ein benutzerdefiniertes `list_template` schreiben und dieselbe visuelle Unterstützung wünschen, fügen Sie die Klasse selbst hinzu:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Ohne die Klasse öffnet die Zelle weiterhin das Popover, rendert aber keine Unterstreichung.

- **Speichern:** Wählen Sie den Häkchen-Button aus oder drücken Sie <kbd>Enter</kbd> in einem einzeiligen Eingabefeld. Das Admin-Panel validiert das Feld, speichert die Änderung und aktualisiert die Zeile, ohne die Seite neu zu laden.
- **Abbrechen:** Wählen Sie den <kbd>x</kbd>-Button aus oder drücken Sie <kbd>Esc</kbd>, um die Änderung zu verwerfen.

## Konfigurationsregeln

Die Anwendung validiert `inline_editable_fields` beim Start, sodass Fehlkonfigurationen schnell fehlschlagen. Ein gelisteter Name löst einen `ValueError` aus, wenn er eine dieser Bedingungen erfüllt:

- Er ist nicht in `fields` deklariert.
- Er ist das Primärschlüsselfeld.
- Er ist von der Listenseite (`exclude_from_list`) oder vom Bearbeitungsformular (`exclude_from_edit`) ausgeschlossen.
- Er ist ein Container- oder schreibgeschütztes Feld: `CollectionField`, `ListField`, `ComputedField`, `FileField` oder `ImageField`.

## Feldunterstützung

Jedes bearbeitbare Feld rendert dasselbe Formular-Widget, das es auf der Bearbeitungsseite verwendet. Die JavaScript- und CSS-Assets eines Felds, wie select2, flatpickr, JSONEditor oder TinyMCE, werden auf der Listenseite nur geladen, wenn dieses Feld inline-bearbeitbar ist. Views ohne Inline-Bearbeitung behalten ihren bisherigen leichten Seitenumfang.

| Feldtyp                                                                              | Unterstützt | Popover-Widget                      |
| ------------------------------------------------------------------------------------ | --------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Ja        | Einfaches Eingabefeld               |
| `SlugField`                                                                          | Ja        | Einfaches Eingabefeld (Quellfeld ausgeschlossen) |
| `TextAreaField`                                                                      | Ja        | Textarea                            |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Ja        | Zahlen-Eingabefeld                  |
| `BooleanField`                                                                       | Ja        | Toggle                              |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Ja        | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Ja        | select2 oder natives Select         |
| `TagsField`                                                                          | Ja        | select2-Tags                        |
| `JSONField`                                                                          | Ja        | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | Ja        | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | Ja        | select2 mit asynchroner Suche       |
| `FileField`, `ImageField`                                                            | Nein      | Keins (erfordert Bearbeitungsseite) |
| `CollectionField`, `ListField`, `ComputedField`                                      | Nein      | Keine (schreibgeschützte Container) |

---

## Berechtigungen

Die Inline-Bearbeitung verwendet das bestehende Berechtigungsmodell wieder. Das Popover erscheint, und das Admin-Panel akzeptiert den Request nur, wenn sowohl `is_accessible(request)` als auch `can_edit(request)` `True` zurückgeben. Das Überschreiben von `can_edit` sichert daher auch Inline-Bearbeitungen ab:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Also disables inline edit when False
        return "edit:post" in request.state.admin_user.roles
```

---

## Validierung

Ein Inline-Speichern validiert und schreibt nur das bearbeitete Feld.

- Die `required`-Prüfung des Felds und die `validators`-Kette laufen genau wie auf der Bearbeitungsseite.
- Andere Felder werden übersprungen. Ein Speichern von der Listenseite kann eine gleichzeitige Bearbeitung eines anderen Felds nicht überschreiben, und ungültige Daten in einem anderen Feld blockieren das Speichern nicht.

Der feldübergreifende `validate`-Hook der View läuft weiterhin, aber das `data`-Dictionary enthält nur das bearbeitete Feld. Ein Hook, der eine vollständige Formularübermittlung erwartet, löst einen `KeyError` aus, wenn er fehlende Schlüssel direkt indiziert. Prüfen Sie daher zuerst, ob ein Schlüssel vorhanden ist:

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

Schlägt die Validierung fehl, bleibt das Popover mit dem übermittelten Wert geöffnet. Die Meldung des bearbeiteten Felds wird unter dem Steuerelement gerendert, genau wie auf der Bearbeitungsseite. Eine Meldung, die einem anderen Feld zugeordnet ist, erhält das Label dieses Felds als Präfix.

Um ein Inline-Speichern innerhalb eines Hooks zu erkennen, prüfen Sie `request.state.action == RequestAction.INLINE_EDIT`. Verwenden Sie dies, um Flash-Nachrichten zu überspringen, die für vollständige Seitenrenderings gedacht sind.

!!! warning
    Eine Validierungsregel, die einem Feld zugeordnet ist, das der Benutzer nicht bearbeitet hat, läuft während eines Inline-Speicherns nicht. Hängen die Invarianten eines Felds von Werten ab, die der Benutzer auf der Listenseite weder sehen noch ändern kann, lassen Sie dieses Feld aus `inline_editable_fields` weg.

---

## Lebenszyklus-Hooks und Events

Inline-Speicherungen durchlaufen den standardmäßigen `edit()`-Pfad der View. Die Hooks `before_edit`, `after_edit` und `after_edit_committed` werden wie üblich ausgelöst, und die entsprechenden [Events](../advanced/events.md) verwenden die Standard-Kontexttypen. Die Payloads `data` und `old_data` enthalten nur das bearbeitete Feld und spiegeln somit genau wider, was das Speichern berührt hat.

Um ein Inline-Speichern innerhalb eines Event-Listeners zu unterscheiden, prüfen Sie `ctx.extra["inline"]`, das für Inline-Bearbeitungen `True` ist:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Benutzerdefinierte Felder

Benutzerdefinierte Felder unterstützen die Inline-Bearbeitung automatisch, wenn sie dem standardmäßigen `BaseField`-Contract folgen. Da `RequestAction.INLINE_EDIT` eine Formularaktion ist, gibt `action.is_form()` `True` zurück. Wenn Ihr benutzerdefiniertes Feld `action == RequestAction.EDIT` prüft, um eine Formularwert-Darstellung zu erstellen, ändern Sie dies so, dass `action.is_form()` verwendet wird, damit das Popover die richtige Darstellung erhält. Den vollständigen Field-Contract finden Sie unter [Benutzerdefinierte Felder](../advanced/custom-fields.md).
