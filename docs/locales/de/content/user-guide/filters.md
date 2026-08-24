---
title: Filter
description: Fügen Sie Ihren Admin-Views komplexe verschachtelte AND/OR-Filterfunktionen
  mit typbewussten Query-Buildern hinzu.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# Filter

Jedes Feld auf einer Listenseite kann über einen eigenen Satz von Filteroperatoren verfügen, z. B. `contains`, `between` und `is null`. Ihre Benutzer kombinieren diese Operatoren zu einem verschachtelten `AND`/`OR`-Baum, und Sie müssen nie eine komplexe Datenbankquery schreiben.

Das Admin-Panel leitet die verfügbaren Filter aus dem zugrunde liegenden Typ des Felds ab. Sie können diesen Satz für jedes Feld einschränken, erweitern oder vollständig ersetzen.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

Unter [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) finden Sie eine lauffähige App, die Standardfilter, Overrides pro Feld und eine benutzerdefinierte `BaseFilter`-Subklasse abdeckt.

Jedes Feld, das Sie in `searchable_fields` auflisten, erhält ein **Filter**-Dropdown-Menü in der Listen-Toolbar. Von dort aus kombinieren die Benutzer beliebig viele Filter, um die benötigten Zeilen zu finden.

## So funktioniert der Filter-Builder

Durch Auswählen der Schaltfläche **Filter** öffnet sich ein Dropdown-Formular, in dem die Benutzer ihre Queries erstellen:

* **Filter hinzufügen**: Fügt eine Bedingungszeile hinzu. Der Benutzer wählt ein Feld aus, wählt einen Operator aus den verfügbaren Filtern dieses Felds und gibt einen Wert an. Die Eingabe passt sich dem Operator an: ein einfaches Textfeld für `contains`, zwei Felder für `between` und gar keine Eingabe für `is null`.
* **Gruppe hinzufügen**: Verschachtelt ein Unterformular mit eigenem `AND`/`OR`-Selektor. Damit lassen sich Bedingungen wie `A AND (B OR C)` erstellen.
* **Alle/eines der folgenden übereinstimmen**: Legt fest, ob die aktuelle Ebene `AND`- oder `OR`-Logik verwendet.
* **Filter anwenden**: Sendet das Formular als `GET`-Request. Das Admin-Panel serialisiert den gesamten Filterbaum in einen einzigen `filter`-Queryparameter, der unter [Das URL-Format des Filters](#das-url-format-des-filters) beschrieben wird.
* **Aktive Filter**: Jeder aktive Filter erscheint als entfernbare Pill über der Tabelle. Durch Auswählen von `×` wird die Liste ohne diese Regel neu geladen. Eine verschachtelte Gruppe wird zu einer einzigen Pill zusammengefasst, die Benutzer als Ganzes entfernen.

!!! tip
    Da sich der gesamte Filterzustand in der URL befindet, lässt sich eine gefilterte Liste teilen. Ihre Benutzer können die Seite als Lesezeichen speichern und den Link an Kollegen senden.

## Filter für ein bestimmtes Feld überschreiben

Wenn die Standardfilter zu breit gefasst sind oder Sie etwas Spezifischeres benötigen, übergeben Sie das Argument `filters=` an ein Feld, um dessen Standardsatz zu ersetzen.

Sie können die Liste auf die Operatoren einschränken, die wichtig sind, sie mit einem benutzerdefinierten Filter erweitern oder einem Feld Operatoren hinzufügen, das standardmäßig nur einfache Null-Prüfungen bietet, z. B. `TagsField`:

```python
from enum import Enum

from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import ModelView

# Import the concrete filter implementations for your specific backend
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    NumericEqualFilter,
)


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductView(ModelView):
    fields = [
        "id",
        StringField("name"),  # Uses the default filter set, no override needed
        EnumField("status", enum=ProductStatus),  # Uses the default filter set
        DecimalField(
            "price",
            # Narrowed down to just 3 of the 9 default numeric filters
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Importieren Sie Filter aus Ihrem Backend"
    Die Filterklassen, die Sie an `filters=` übergeben, müssen die konkreten Implementierungen für Ihr Datenbank-Backend sein: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters` oder `.tortoise.filters`. Importieren Sie aus dem `filters`-Modul Ihres Backends, nicht aus `starlette_admin.filters`.

## Das URL-Format des Filters

Der Filter-Builder serialisiert seinen Zustand in den `filter`-Queryparameter als kompakte Zeichenfolge.

Das Format ist `field__operator` für einen Filter ohne Werte, `field__operator=value` für einen einzelnen Wert und `field__operator=value..value2` für einen Filter mit zwei Werten, z. B. `between`. Regeln werden mit `AND` oder `OR` verbunden, und Klammern verschachteln eine Gruppe:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Setzen Sie einen Wert in Anführungszeichen, wenn er ein Leerzeichen oder eine Klammer enthält: `name__eq="quoted value"`. Ein Listenwert für einen Mehrfachauswahl-Filter wie `is one of` ist durch Kommas getrennt und benötigt keine Anführungszeichen: `status__in=ACTIVE,OUT_OF_STOCK`.

Wenn die URL eine ungültige `filter`-Zeichenfolge enthält, etwa ein unbekanntes Feld, einen nicht verfügbaren Operator oder einen nicht analysierbaren Wert, gibt die Anwendung einen `HTTP 400`-Fehler zurück, statt stillschweigend einen Teil der Bedingung zu verwerfen.

!!! important
    Nur die Felder, die Sie in `searchable_fields` auflisten, erhalten Filter. Wenn Sie `searchable_fields` nicht setzen, erhält jedes Feld Filter.


## Referenz integrierter Filter

Die folgende Tabelle listet jeden Filter auf, der ab Werk verfügbar ist, den URL-Slug, den Sie in einem gespeicherten Link sehen, und die Art von Wert, die jeder erwartet. Filter, die mit „zwei Werte“ markiert sind, benötigen sowohl einen `value` als auch einen `value2` in der URL, z. B. `between=2026-01-01..2026-01-31`.

| Filter | Slug | Werttyp | Zwei Werte? |
| --- | --- | --- | --- |
| Enthält | `contains` | Text |  |
| Enthält nicht | `not_contains` | Text |  |
| Beginnt mit | `startswith` | Text |  |
| Endet mit | `endswith` | Text |  |
| Gleich | `eq` | Text, Zahl, Datum, Datetime oder Zeit |  |
| Ungleich | `neq` | Text oder Zahl |  |
| Ist null | `is_null` | *(keiner)* |  |
| Ist nicht null | `is_not_null` | *(keiner)* |  |
| Größer als | `gt` | Zahl |  |
| Kleiner als | `lt` | Zahl |  |
| Größer als oder gleich | `gte` | Zahl |  |
| Kleiner als oder gleich | `lte` | Zahl |  |
| Zwischen | `between` | Zahl, Datum, Datetime oder Zeit | ✓ |
| Liegt in der Vergangenheit | `in_past` | *(keiner)* |  |
| Liegt in der Zukunft | `in_future` | *(keiner)* |  |
| Ist wahr | `is_true` | *(keiner)* |  |
| Ist falsch | `is_false` | *(keiner)* |  |
| Ist eines von | `in` | Kommagetrennte Liste |  |
| Ist keines von | `not_in` | Kommagetrennte Liste |  |

Wenn Sie einen Filter für einen Datentyp benötigen, den die integrierten Filter nicht abdecken, etwa ein JSON-Feld oder einen Geo-Punkt, lesen Sie [Benutzerdefinierte Filter](https://jowilf.github.io/starlette-admin/advanced/custom-filters/), um eine `BaseFilter`-Subklasse zu schreiben und sie global oder pro Feldinstanz zu registrieren.

---

**Wie es weitergeht**

* **[Benutzerdefinierte Filter](https://jowilf.github.io/starlette-admin/advanced/custom-filters/):** Schreiben und registrieren Sie eine `BaseFilter`-Subklasse.
* **[Aktionen](actions.md):** Fügen Sie Ihren Listenseiten Massen- und Zeilenaktionen hinzu.
* **[Views](views.md):** Erfahren Sie mehr über `searchable_fields` und die restliche Konfiguration der Listenseite.
