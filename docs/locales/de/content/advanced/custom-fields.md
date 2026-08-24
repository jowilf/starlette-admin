---
title: Benutzerdefinierte Felder
description: Erfahren Sie, wie Sie in starlette-admin eigene Feldtypen erstellen,
  um spezielle Datentypen und benutzerdefinierte UI-Widgets zu verarbeiten.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Benutzerdefinierte Felder

Die integrierten Felder decken die meisten Spalten ab, auf die Sie stoßen werden. Wenn jedoch keines davon passt, können Sie ein eigenes erstellen, indem Sie [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField) ableiten. Ein Feld besteht aus drei Methoden, die Daten zwischen Ihrem Modell und dem Browser bewegen, sowie einer Reihe von Template-Pfaden, die es rendern. Leiten Sie direkt von `BaseField` ab oder erweitern Sie das integrierte Feld, das Ihren Anforderungen am nächsten kommt (z. B. `StringField` oder `EnumField`), und überschreiben Sie nur die Teile, die sich unterscheiden.

## Minimalbeispiel

```python
from dataclasses import dataclass
from dataclasses import field as dc_field

from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

Richten Sie Ihre `Admin`-Instanz auf das Templates-Verzeichnis und verwenden Sie dann das Feld in Ihrer View:

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

Da `StatusBadgeField` von `EnumField` statt von `BaseField` abstammt, erbt es `choices`, die Formularvalidierung gegen diese Auswahl sowie die Standard-Template `fields/form/enum.html` für die Erstell- und Bearbeitungsformulare. Nichts davon muss geändert werden, daher überschreibt die Klasse nur die Attribute für die Listen- und Detaildarstellung.

Der Rest dieser Seite behandelt, was Sie überschreiben müssen, wenn ein Feld mehr als einen Template-Austausch erfordert. Den vollständigen, lauffähigen Code – zusammen mit einem zweiten Feld (`AvatarNameField`), das tatsächlich die Datenmethoden überschreibt – finden Sie unter [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Die drei Datenmethoden

| Methode | Aufgerufen, wenn | Signatur |
| --- | --- | --- |
| `parse_form_data` | Ein Erstell-/Bearbeitungsformular abgesendet wird | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Ein Wert von einer Modellinstanz zur Anzeige gelesen wird | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Ein Wert für das Frontend formatiert wird (Liste, Detail, API, Export) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` überschreibt keine dieser Methoden, da `EnumField` den abgesendeten Wert bereits gegen `choices` validiert und den rohen String aus `obj.status` liest. Das Badge ist lediglich die Präsentation dieses Strings. Überschreiben Sie diese drei Methoden, wenn der Wert selbst berechnet oder umgeformt werden muss, statt nur neu gerendert zu werden.

!!! tip "Hooks oder Subclassing"
    Für eine einmalige Änderung an einem einzelnen Feld benötigen Sie selten eine eigene Klasse. Übergeben Sie stattdessen die [Hooks `getter`, `formatter` und `parser`](../user-guide/fields.md#computing-formatting-and-parsing-values) als Konstruktorargumente, um das Lesen, die Anzeigeformatierung und das Parsen der Eingabe zu handhaben.
    **Wann Subclassing:** Nur wenn Sie dieselbe Logik in mehr als einer View benötigen oder wenn Sie die Templates ändern möchten.

`parse_form_data` erhält die rohen `FormData` (aus `starlette.datastructures`) der Anfrage und gibt die Daten zurück, die `view.create()` bzw. `view.edit()` für dieses Feld erhalten sollen. Die Standardimplementierung liest `form_data.get(self.id)` und gibt ihn unverändert zurück. Die meisten Felder müssen lediglich eine Typkonvertierung ergänzen:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` erhält die Modellinstanz und gibt den anzuzeigenden Wert zurück. Die Standardimplementierung gibt `getattr(obj, self.name, None)` zurück. Überschreiben Sie sie für Felder, die nicht auf ein einzelnes Modellattribut abgebildet sind, etwa eines, das zwei Spalten kombiniert. `AvatarNameField` kombiniert beispielsweise einen `name`-String mit dem hochgeladenen Avatar der Zeile:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` erhält das Ergebnis von `parse_obj` (oder der ORM-Schicht) und formatiert es für die aktuelle Anfrage. Es wird separat für die Listenseite, die Detailseite, die JSON-API und Datenexporte aufgerufen. Verzweigen Sie daher über `request.state.action`, wenn sich die Struktur je nach Kontext unterscheiden muss. `AvatarNameField` benötigt das Avatar-Bild nur auf der Listenseite und fällt überall sonst auf reinen Text zurück:

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    Was auch immer `serialize_value` für `RequestAction.LIST` und `RequestAction.RELATION_LOOKUP` zurückgibt, geht direkt in eine JSON-Antwort ein und muss daher JSON-serialisierbar sein.

## Template-Pfade

Jedes Feld trägt die folgenden Template-Attribute. Jedes davon ist ein Pfad, den der Jinja2-Loader des Admins auflöst: Er prüft zunächst Ihr `templates_dir`, sofern gesetzt, und fällt anschließend auf das integrierte Verzeichnis `starlette_admin/templates/` zurück. Details finden Sie unter [Templates](templates.md).

| Attribut | Standardwert | Gerendert für |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Den Spaltenwert jeder Zeile auf der Listenseite |
| `detail_template` | `"fields/detail/text.html"` | Die schreibgeschützte Detailseite |
| `form_template` | `"fields/form/input.html"` | Das Eingabefeld im Erstell-/Bearbeitungsformular |
| `null_template` | `"fields/detail/_null.html"` | Listen- und Detailseiten, wenn der Wert `None` ist |
| `empty_template` | `"fields/detail/_empty.html"` | Listen- und Detailseiten, wenn der Wert eine leere Liste oder ein leeres Tupel ist |

Alle fünf Templates erhalten die `field`-Instanz und den aktuellen `data`-Wert. Bei `list_template` und `detail_template` ist `data` niemals `None` oder leer, da diese Fälle vor dem Einbinden des typspezifischen Templates an `null_template` bzw. `empty_template` weitergeleitet werden. Das `form_template` erhält außerdem `error` (die Meldung einer `FormValidationError`, falls eine aufgetreten ist) sowie `action` (`RequestAction.CREATE`, `RequestAction.EDIT` oder `RequestAction.INLINE_EDIT`, wenn es innerhalb des Popovers für [Inline-Bearbeitung](../user-guide/inline-edit.md) der Listenseite gerendert wird). Alle drei sind Formular-Aktionen, sodass `action.is_form()` `True` zurückgibt. Feldcode, der die Formulardarstellung des Werts benötigt, sollte auf dieser Grundlage verzweigen und nicht auf `action == RequestAction.EDIT`.

Überschreiben Sie `null_template` und `empty_template`, wenn ein fehlender Wert anders aussehen soll als die standardmäßigen gedämpften Beschriftungen `-null-` und `-empty-` – beispielsweise ein Icon für den leeren Zustand oder ein Badge „Nicht angegeben“, das zum Stil des Feldes passt:

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

Da `null_template` und `empty_template` einfache Feldattribute wie `list_template` sind, gelten sie übergreifend für Liste, Detail und jede andere View, die dieses Feld rendert – etwa die Inline-Tabelle einer verwandten View.

`StatusBadgeField` weist sowohl `list_template` als auch `detail_template` dasselbe Template zu, weil dasselbe Badge in beiden Kontexten funktioniert:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` überschreibt nur `list_template`. Die Variable `data` in diesem Template ist das Dictionary, das `parse_obj` erstellt und `serialize_value` umgeformt hat – kein simpler String:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

Die Klasse `inline-edit-value` ist das Opt-in-Merkmal für die Unterstreichung der [Inline-Bearbeitung](../user-guide/inline-edit.md). Sie bleibt wirkungslos, solange das Feld nicht inline-editierbar ist. Sie hier auf den Namen und nicht auf den Avatar zu setzen, kostet also nichts und hält die Funktion korrekt eingegrenzt, falls das Feld später editierbar wird.

Das Überschreiben von `list_template` und `detail_template` bei Beibehaltung des Standard-`form_template` ist genau das, was `StatusBadgeField` durch die Erweiterung von `EnumField` erreicht. Das Standard-Template `fields/form/enum.html` rendert ein `<select>`-Dropdown, das aus `field.choices` befüllt wird, sodass sich ein Status ohne weitere Änderung bearbeiten lässt.

## Registrierung in der Converter-Registry

Die Liste `fields = [...]` einer View akzeptiert neben Feldobjekten auch einfache Attributnamen. Jeder Eintrag, der nicht bereits ein `BaseField` ist, durchläuft eine **Converter-Registry**, die den Spaltentyp einer Feldklasse zuordnet. Jedes ORM-Backend bringt seine eigene Registry mit (`starlette_admin.contrib.sqla.converters.ModelConverter` und die Entsprechungen für `beanie`, `mongoengine` und `tortoise`); alle bauen auf derselben Basis auf:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

Der Decorator `@converts(*types)` markiert eine Methode als Converter für einen oder mehrere Typschlüssel. `BaseModelConverter.__init__` durchsucht die Instanz nach diesen dekorierten Methoden und baut daraus sein `converters`-Dictionary auf. Beim SQLAlchemy-Backend sind die Typschlüssel die **Namen** der Spaltentypen (`"String"`, `"Integer"`, `"Enum"` usw.), da SQLAlchemy keine gemeinsame Basisklasse über alle Dialekte hinweg besitzt.

Leiten Sie vom Converter des Backends ab, um eigene Zuordnungen hinzuzufügen. Dieses Beispiel leitet jede `Enum`-Spalte an `StatusBadgeField` statt an das Standard-`EnumField` weiter:

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

Übergeben Sie die Unterklasse an `ModelView(converter=...)`, damit die String-Feldnamen in `fields = [...]` über Ihren Converter statt über den Standard-Converter aufgelöst werden:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Wenn Sie Felder stets explizit konstruieren – wie im Minimalbeispiel oben –, können Sie die Converter-Registry umgehen. Sie benötigen sie nur, wenn ein Eintrag wie `fields = ["status"]` anhand des zugrunde liegenden Spaltentyps ein `StatusBadgeField` erzeugen soll.

---

## Wie es weitergeht

* **[Felder](../user-guide/fields.md):** Die vollständige Referenz der integrierten Felder samt Attributtabelle von `BaseField`.
* **[Templates](templates.md):** Wie der Template-Loader `list_template`, `detail_template`, `form_template`, `null_template` und `empty_template` auflöst.
* **[Erweiterungspunkte](extension-points.md):** Alle weiteren pluggable Oberflächen in `starlette-admin`.
