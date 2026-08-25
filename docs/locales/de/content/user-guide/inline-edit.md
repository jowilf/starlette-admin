---
title: Inline-Bearbeitung
description: Ermöglichen Sie Benutzern, Feldwerte direkt in der Listentabelle zu bearbeiten,
  um die Dateneingabe zu beschleunigen.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Inline-Bearbeitung

Mit der Inline-Bearbeitung können Benutzer ein einzelnes Feld direkt auf der Listenseite ändern. Durch das Auswählen einer Zelle öffnet sich ein kleines Popover, sodass niemand das vollständige Bearbeitungsformular öffnen muss. Verwenden Sie sie für schnelle Aktualisierungen einzelner Felder: etwa um einen Titel zu korrigieren, einen Status umzuschalten oder ein Datum anzupassen. Die Interaktion folgt dem bekannten [x-editable](https://vitalets.github.io/x-editable/)-Muster.

Die Funktion ist optional und standardmäßig deaktiviert. Ihre Aktivierung ändert nichts an der üblichen Bearbeitungsseite, die weiterhin die Hauptoberfläche für komplexe Bearbeitungen mehrerer Felder bleibt.

> Ein ausführbares Beispiel mit Inline-Bearbeitung finden Sie unter [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Grundlegende Verwendung

Deklarieren Sie die bearbeitbaren Feldnamen in der Liste `inline_editable_fields`:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Bearbeitbare Zellen zeigen daraufhin auf der Listenseite eine gestrichelte Unterstreichung an. Das Auswählen einer Zelle öffnet ein Popover mit dem Standard-Formularelement des Felds, vorausgefüllt mit dem aktuellen Wert.

Die Unterstreichung wird nicht über die gesamte Zelle gezeichnet. Jede Listen-Template legt die CSS-Klasse `inline-edit-value` auf genau das Element, das unterstrichen werden soll, und der Stil greift nur innerhalb einer bearbeitbaren Zelle. Alle integrierten Listen-Templates enthalten die Klasse bereits. Wenn Sie ein eigenes `list_template` schreiben und denselben Hinweis wünschen, fügen Sie die Klasse selbst hinzu:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Ohne die Klasse öffnet die Zelle weiterhin das Popover, rendert jedoch keine Unterstreichung.

- **Speichern:** Wählen Sie die Schaltfläche mit dem Häkchen oder drücken Sie <kbd>Enter</kbd> in einem einzeiligen Eingabefeld. Der Admin validiert das Feld, speichert die Änderung und aktualisiert die Zeile, ohne die Seite neu zu laden.
- **Abbrechen:** Wählen Sie die Schaltfläche <kbd>x</kbd> oder drücken Sie <kbd>Esc</kbd>, um die Änderung zu verwerfen.

## Konfigurationsregeln

Die Anwendung validiert `inline_editable_fields` beim Start, sodass Fehlkonfigurationen schnell auffallen. Ein aufgeführter Name löst einen `ValueError` aus, wenn eine dieser Bedingungen zutrifft:

- Er ist nicht in `fields` deklariert.
- Es ist das Primärschlüsselfeld.
- Es ist von der Listenseite (`exclude_from_list`) oder vom Bearbeitungsformular (`exclude_from_edit`) ausgeschlossen.
- Es ist ein Container- oder schreibgeschütztes Feld: `CollectionField`, `ListField`, `ComputedField`, `FileField` oder `ImageField`.

## Feldunterstützung

Jedes bearbeitbare Feld rendert dasselbe Formular-Widget, das es auch auf der Bearbeitungsseite verwendet. Die JavaScript- und CSS-Assets eines Felds, wie select2, flatpickr, JSONEditor oder TinyMCE, werden nur dann auf der Listenseite geladen, wenn dieses Feld inline-bearbeitbar ist. Views ohne Inline-Bearbeitung behalten ihren bisher geringen Seitenumfang.

| Feldtyp                                                                              | Unterstützt | Popover-Widget                      |
| ------------------------------------------------------------------------------------ | --------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Ja        | Einfaches Eingabefeld               |
| `SlugField`                                                                          | Ja        | Einfaches Eingabefeld (Quellfeld ausgeschlossen) |
| `TextAreaField`                                                                      | Ja        | Textarea                            |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Ja        | Zahlenfeld                          |
| `BooleanField`                                                                       | Ja        | Toggle                              |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Ja        | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Ja        | select2 oder natives Select         |
| `TagsField`                                                                          | Ja        | select2 tags                        |
| `JSONField`                                                                          | Ja        | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | Ja        | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | Ja        | select2 mit asynchroner Suche       |
| `FileField`, `ImageField`                                                            | Nein      | Keine (erfordert Bearbeitungsseite) |
| `CollectionField`, `ListField`, `ComputedField`                                      | Nein      | Keine (schreibgeschützte Container) |

---

## Berechtigungen

Die Inline-Bearbeitung nutzt das vorhandene Berechtigungsmodell. Das Popover erscheint und der Admin akzeptiert die Anfrage nur, wenn sowohl `is_accessible(request)` als auch `can_edit(request)` den Wert `True` zurückgeben. Eine Überschreibung von `can_edit` sichert daher auch Inline-Bearbeitungen ab:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Deaktiviert auch die Inline-Bearbeitung bei False
        return "edit:post" in request.state.admin_user.roles
```

---

## Validierung

Ein inline durchgeführtes Speichern validiert und schreibt ausschließlich das bearbeitete Feld.

- Die `required`-Prüfung des Felds und die Kette seiner `validators` laufen genau so wie auf der Bearbeitungsseite.
- Andere Felder werden übersprungen. Ein Speichern auf der Listenseite kann eine gleichzeitige Bearbeitung eines anderen Felds nicht überschreiben, und ungültige Daten in einem anderen Feld blockieren das Speichern nicht.

Der view-übergreifende `validate`-Hook läuft weiterhin, enthält aber im `data`-Wörterbuch nur das bearbeitete Feld. Ein Hook, der eine vollständige Formularübermittlung erwartet, löst einen `KeyError` aus, wenn er fehlende Schlüssel direkt indiziert – prüfen Sie daher zunächst, ob ein Schlüssel vorhanden ist:

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

Bei einer fehlgeschlagenen Validierung bleibt das Popover mit dem übermittelten Wert unverändert offen. Die Meldung des bearbeiteten Felds wird unterhalb des Elements gerendert – genau wie auf der Bearbeitungsseite. Eine Meldung, die sich auf ein anderes Feld bezieht, erhält das Label dieses Felds als Präfix.

Um ein Inline-Speichern innerhalb eines Hooks zu erkennen, prüfen Sie `request.state.action == RequestAction.INLINE_EDIT`. Nutzen Sie dies, um Flash-Meldungen zu überspringen, die für vollständige Seitenrenderings bestimmt sind.

!!! warning
    Eine Validierungsregel, die sich auf ein Feld bezieht, das der Benutzer nicht bearbeitet hat, läuft während eines Inline-Speicherns nicht. Hängen die Invarianten eines Felds von Werten ab, die der Benutzer auf der Listenseite weder sehen noch ändern kann, lassen Sie dieses Feld aus `inline_editable_fields` weg.

---

## Lifecycle-Hooks und Ereignisse

Inline-Speicherungen durchlaufen den üblichen `edit()`-Pfad des Views. Die Hooks `before_edit`, `after_edit` und `after_edit_committed` werden wie gewohnt ausgelöst, und die entsprechenden [Ereignisse](../advanced/events.md) verwenden die Standard-Kontexttypen. Die Nutzdaten `data` und `old_data` enthalten nur das bearbeitete Feld und spiegeln somit exakt wider, was das Speichern betroffen hat.

Um ein Inline-Speichern innerhalb eines Event-Listeners zu unterscheiden, prüfen Sie `ctx.extra["inline"]`, das bei Inline-Bearbeitungen `True` ist:

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

Benutzerdefinierte Felder unterstützen die Inline-Bearbeitung automatisch, wenn sie dem Standard-Vertrag von `BaseField` folgen. Da `RequestAction.INLINE_EDIT` eine Formularaktion ist, gibt `action.is_form()` den Wert `True` zurück. Wenn Ihr benutzerdefiniertes Feld `action == RequestAction.EDIT` prüft, um eine Formularwert-Darstellung zu erzeugen, ändern Sie dies auf `action.is_form()`, damit das Popover die richtige Darstellung erhält. Den vollständigen Feldvertrag finden Sie unter [Custom Fields](../advanced/custom-fields.md).
