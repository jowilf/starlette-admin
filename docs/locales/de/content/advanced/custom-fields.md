---
title: Benutzerdefinierte Felder
description: Erfahren Sie, wie Sie in starlette-admin benutzerdefinierte Feldtypen
  erstellen, um spezielle Datentypen und benutzerdefinierte UI-Widgets zu verarbeiten.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Benutzerdefinierte Felder

Die integrierten Felder decken die meisten Spalten ab, auf die Sie treffen werden. Wenn keines davon passt, können Sie Ihr eigenes bauen, indem Sie [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField) subclassen. Ein Feld besteht aus drei Methoden, die Daten zwischen Ihrem Modell und dem Browser bewegen, plus einer Reihe von Template-Pfaden, die es rendern. Subclassen Sie `BaseField` direkt oder erweitern Sie das integrierte Feld, das Ihren Anforderungen am nächsten kommt (z. B. `StringField` oder `EnumField`), und überschreiben Sie nur die Teile, die abweichen.

## Minimales Beispiel

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

Richten Sie Ihre `Admin`-Instanz auf das Template-Verzeichnis und verwenden Sie dann das Feld in Ihrer View:

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

Da `StatusBadgeField` von `EnumField` statt von `BaseField` erbt, erbt es `choices`, die Formularvalidierung gegen diese Choices sowie das Default-Template `fields/form/enum.html` für die Create- und Edit-Formulare. Nichts davon muss geändert werden, daher überschreibt die Klasse nur die Attribute für das List- und Detail-Rendering.

Der Rest dieser Seite behandelt, was Sie überschreiben müssen, wenn ein Feld mehr als einen Template-Austausch benötigt. Den vollständigen lauffähigen Code finden Sie zusammen mit einem zweiten Feld (`AvatarNameField`), das tatsächlich die Datenmethoden überschreibt, unter [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Die drei Datenmethoden

| Methode | Aufgerufen, wenn | Signatur |
| --- | --- | --- |
| `parse_form_data` | Ein Create/Edit-Formular abgesendet wird | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Ein Wert von einer Modellinstanz zur Anzeige gelesen wird | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Ein Wert für das Frontend formatiert wird (Liste, Detail, API, Export) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` überschreibt keine davon, weil `EnumField` den abgesendeten Wert bereits gegen `choices` parst und den rohen String aus `obj.status` liest. Das Badge ist nur Präsentation auf Basis dieses Strings. Überschreiben Sie diese drei Methoden, wenn der Wert selbst berechnet oder umgeformt werden muss statt nur neu gerendert.

!!! tip "Hooks oder Subclassing"
    Für eine einmalige Änderung an einem einzelnen Feld brauchen Sie selten eine Unterklasse. Übergeben Sie stattdessen die [Hooks `getter`, `formatter` und `parser`](../user-guide/fields.md#werte-berechnen-formatieren-und-parsen) als Konstruktorargumente, um das Lesen, die Anzeigeformatierung und das Parsen der Eingabe zu handhaben.
    **Wann Subclassing:** nur wenn Sie dieselbe Logik in mehr als einer View benötigen oder wenn Sie die Templates ändern müssen.

`parse_form_data` empfängt die rohe `FormData` (aus `starlette.datastructures`) vom Request und gibt die Daten zurück, die `view.create()` bzw. `view.edit()` für dieses Feld erhalten sollen. Die Default-Implementierung liest `form_data.get(self.id)` und gibt es unverändert zurück. Die meisten Felder müssen nur eine Typumwandlung hinzufügen:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` empfängt die Modellinstanz und gibt den anzuzeigenden Wert zurück. Der Default gibt `getattr(obj, self.name, None)` zurück. Überschreiben Sie ihn für Felder, die nicht auf ein einzelnes Modellattribut abgebildet werden, z. B. eines, das zwei Spalten kombiniert. `AvatarNameField` kombiniert beispielsweise einen `name`-String mit dem hochgeladenen Avatar der Zeile:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` empfängt, was `parse_obj` (oder die ORM-Schicht) erzeugt hat, und formatiert es für den aktuellen Request. Es wird separat für die Listenseite, die Detailseite, die JSON-API und Datenexporte aufgerufen. Verzweigen Sie daher auf `request.state.action`, wenn sich die Struktur je nach Kontext unterscheiden muss. `AvatarNameField` benötigt das Avatar-Bild nur auf der Listenseite und fällt überall sonst auf reinen Text zurück:

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
    Was auch immer `serialize_value` für `RequestAction.LIST` und `RequestAction.RELATION_LOOKUP` zurückgibt, geht direkt in eine JSON-Response ein, es muss also JSON-serialisierbar sein.

## Template-Pfade

Jedes Feld trägt die folgenden Template-Attribute. Jedes davon ist ein Pfad, den der Jinja2-Loader des Admins auflöst: Er prüft zuerst Ihr `templates_dir`, falls Sie eines gesetzt haben, und fällt dann auf das integrierte Verzeichnis `starlette_admin/templates/` zurück. Einzelheiten finden Sie unter [Templates](templates.md).

| Attribut | Default | Gerendert für |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Den Spaltenwert jeder Zeile auf der Listenseite |
| `detail_template` | `"fields/detail/text.html"` | Die schreibgeschützte Detailseite |
| `form_template` | `"fields/form/input.html"` | Das Create/Edit-Formularfeld |
| `null_template` | `"fields/detail/_null.html"` | Listen- und Detailseiten, wenn der Wert `None` ist |
| `empty_template` | `"fields/detail/_empty.html"` | Listen- und Detailseiten, wenn der Wert eine leere Liste oder ein leeres Tuple ist |

Alle fünf Templates erhalten die `field`-Instanz und den aktuellen `data`-Wert. Bei `list_template` und `detail_template` ist `data` niemals `None` oder leer, da diese Fälle zu `null_template` bzw. `empty_template` weitergeleitet werden, bevor das typspezifische Template eingebunden wird. Das `form_template` erhält außerdem `error` (die Nachricht einer `FormValidationError`, falls eine aufgetreten ist) und `action` (`RequestAction.CREATE`, `RequestAction.EDIT` oder `RequestAction.INLINE_EDIT`, wenn es innerhalb des [Inline-Edit](../user-guide/inline-edit.md)-Popovers der Listenseite gerendert wird). Alle drei sind Formularaktionen, daher gibt `action.is_form()` `True` zurück. Feldcode, der die Darstellung des Formularwerts benötigt, sollte darauf verzweigen und nicht auf `action == RequestAction.EDIT`.

Überschreiben Sie `null_template` und `empty_template`, wenn ein fehlender Wert anders aussehen soll als die Default-Labels `-null-` und `-empty-`, z. B. als Icon für einen leeren Zustand oder als Badge „Nicht angegeben", das zum eigenen Styling des Feldes passt:

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

Da `null_template` und `empty_template` einfache Feldattribute wie `list_template` sind, werden sie über Liste, Detail und jede andere View geteilt, die dieses Feld rendert, etwa die Inline-Tabelle einer verwandten View.

`StatusBadgeField` weist sowohl `list_template` als auch `detail_template` dasselbe Template zu, weil dasselbe Badge in beiden Kontexten funktioniert:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` überschreibt nur `list_template`. Die Variable `data` in diesem Template ist das Dictionary, das `parse_obj` gebaut und `serialize_value` umgeformt hat, und kein einfacher String:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

Die Klasse `inline-edit-value` ist das Opt-in-Marker für die Unterstreichung des [Inline-Edits](../user-guide/inline-edit.md). Sie ist wirkungslos, solange das Feld nicht inline editierbar ist. Daher kostet es hier nichts, sie auf dem Namen statt auf dem Avatar zu setzen, während der Hinweis korrekt eingegrenzt bleibt, falls das Feld jemals editierbar wird.

Das Überschreiben von `list_template` und `detail_template` bei Beibehaltung des Default-`form_template` ist genau das, was `StatusBadgeField` tut, indem es `EnumField` erweitert. Das Default-Template `fields/form/enum.html` rendert ein `<select>`-Dropdown-Menü, das aus `field.choices` befüllt wird, sodass das Bearbeiten eines Status ohne weitere Änderungen funktioniert.

## Registrierung im Converter-Registry

Die Liste `fields = [...]` einer View akzeptiert einfache Attributnamen ebenso wie Feldobjekte. Jedes Element, das noch kein `BaseField` ist, durchläuft ein **Converter-Registry**, das den Spaltentyp auf eine Feldklasse abbildet. Jedes ORM-Backend bringt sein eigenes Registry mit (`starlette_admin.contrib.sqla.converters.ModelConverter` und die Äquivalente für `beanie`, `mongoengine` und `tortoise`), alle basieren auf derselben Basisklasse:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

Der Dekorator `@converts(*types)` markiert eine Methode als Converter für einen oder mehrere Typschlüssel. `BaseModelConverter.__init__` scannt die Instanz nach diesen dekorierten Methoden und baut daraus sein `converters`-Dictionary. Beim SQLAlchemy-Backend sind die Typschlüssel die **Namen** der Spaltentypen (`"String"`, `"Integer"`, `"Enum"` usw.), weil SQLAlchemy keine gemeinsame gemeinsame Basisklasse über Dialekte hinweg hat.

Subclassen Sie den Converter des Backends, um eigene Mappings hinzuzufügen. Dieses Beispiel leitet jede `Enum`-Spalte an `StatusBadgeField` statt an das Default-`EnumField` weiter:

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

Übergeben Sie die Unterklasse an `ModelView(converter=...)`, damit die String-Feldnamen in `fields = [...]` über Ihren Converter statt über den Default aufgelöst werden:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Wenn Sie Felder immer explizit konstruieren, wie im minimalen Beispiel oben, können Sie das Converter-Registry umgehen. Sie benötigen es nur, wenn ein Eintrag wie `fields = ["status"]` aus dem zugrunde liegenden Spaltentyp ein `StatusBadgeField` erzeugen soll.

---

## Wie es weitergeht

* **[Felder](../user-guide/fields.md):** Die vollständige Referenz der integrierten Felder und die Tabelle der `BaseField`-Attribute.
* **[Templates](templates.md):** Wie der Template-Loader `list_template`, `detail_template`, `form_template`, `null_template` und `empty_template` auflöst.
* **[Erweiterungspunkte](extension-points.md):** Alle weiteren austauschbaren Oberflächen in `starlette-admin`.
