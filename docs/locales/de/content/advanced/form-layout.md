---
title: Formular-Layouts
description: Gestalten Sie komplexe, responsive Formular-Layouts mit TabsWidget, FieldsetWidget
  und Grid-Spalten in starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Formular-Layouts

Standardmäßig rendert das Create- und Edit-Formular alles in `fields` als eine flache Liste. Mit dem Attribut `form_layout` können Sie diese Eingabefelder mit denselben komponierbaren Widgets anordnen, die Sie auch für [Dashboards](../user-guide/custom-views.md) verwenden: nebeneinanderliegende Zeilen, betitelte oder einklappbare Panels, Tabs, statische Inhalte und Ihre eigenen benutzerdefinierten Widgets.

## Grundlegende Verwendung

Das einfachste Layout benötigt überhaupt keine Widgets. Referenzieren Sie ein Feld über seinen String-Namen, um es in einer eigenen Zeile zu platzieren, und gruppieren Sie Namen in einem Tuple, um sie nebeneinander in einer Zeile anzuordnen.

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

Im obigen Layout:

* `("first_name", "last_name")` erzeugt eine Zeile, die gleichmäßig zwischen den beiden Eingabefeldern aufgeteilt ist.
* `"email"` wird direkt darunter in einer eigenen Zeile gerendert.
* `("salary", "notes")` erzeugt eine zweite mehrspaltige Zeile.

Sie können beliebig viele Felder in eine Zeile aufnehmen und einspaltige sowie mehrspaltige Zeilen frei kombinieren.

Container-Widgets erweitern diese Kurzschreibweise selbst: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` und `Col` wandeln bei der Konstruktion Tuples in Zeilen und Listen in gestapelte Spalten um. Die Kurzschreibweise funktioniert daher auch innerhalb verschachtelter `children`-Attribute sowie innerhalb eines [`CustomView.widget`](../user-guide/custom-views.md)-Dashboards.

## Gruppierung von Feldern

### Betitelte Panels

Um einer Gruppe von Feldern einen Titel zu geben oder sie einklappbar zu machen, umschließen Sie sie mit einem `PanelWidget`. Das Widget akzeptiert dieselbe String- und Tuple-Kurzschreibweise wie die oberste Ebene.

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` akzeptiert folgende Attribute:

| Attribut | Beschreibung |
| --- | --- |
| `title` | Die Überschrift, die im Karten-Kopf des Panels angezeigt wird. |
| `children` | Die Widgets, die in dieser Reihenfolge im Panel gerendert werden. Akzeptiert die oben genannte Kurzschreibweise oder verschachtelte Widgets. Fügen Sie ein Kind-Element `TextWidget(card=False)` hinzu, um erklärenden Text unterhalb des Titels anzuzeigen. |
| `collapsible` | Ermöglicht es Benutzern, das Panel auszuklappen und einzuklappen. |
| `collapsed` | Startet das Panel eingeklappt. Gilt nur, wenn `collapsible=True`. |

Für eine Gruppe ohne Titel verwenden Sie stattdessen `ColumnWidget`. Es stapelt seine Kinder vertikal, ohne sie in eine gestylte Karte einzubetten.

### Fieldsets

`FieldsetWidget` gruppiert Felder ähnlich wie `PanelWidget`, rendert jedoch ein natives HTML-`<fieldset>` mit `<legend>` statt einer gestylten Karte. Verwenden Sie es, wenn Sie eine einfachere, umrandete Gruppierung wünschen.

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

Das Attribut `legend` legt die Beschriftung im `<legend>`-Element fest. `disabled=True` setzt das HTML-Attribut `disabled` auf dem Container, wodurch jedes verschachtelte Formularelement deaktiviert wird. `FieldsetWidget` unterstützt dieselbe `children`-Kurzschreibweise wie `PanelWidget`, jedoch keine panelspezifischen Optionen wie `collapsible` und `icon`.

## Explizite Spaltenbreiten

Die Tuple-Kurzschreibweise teilt eine Zeile immer gleichmäßig auf. Für eine feinere Kontrolle über die Spaltenbreiten bauen Sie die Zeile explizit mit `RowWidget`, `Col` und `FieldRef` auf:

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Ausblenden von Feldbeschriftungen

Bei der expliziten Konstruktion eines `FieldRef` steht Ihnen der Parameter `show_label` zur Verfügung, der das `<label>`-Element weglässt, wenn das umgebende Layout den Zweck des Feldes bereits offensichtlich macht.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` ist standardmäßig auf `True` gesetzt. Die String- und Tuple-Kurzschreibweisen rendern immer Beschriftungen, da sie keine Schlüsselwortargumente entgegennehmen.

## Input Groups

Die Parameter `prepend` und `append` fügen ein [Input Group](https://docs.tabler.io/ui/forms/form-elements#input-group)-Addon an einer der beiden Seiten eines Eingabefelds an. Jeder davon akzeptiert reinen Text oder rohes HTML, beispielsweise ein Font-Awesome-Icon.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Addons funktionieren bei Feldern, deren Formular-Template ein natives `<input>`-Element rendert: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, die numerischen Felder (`IntegerField`, `DecimalField`, `FloatField`) sowie die Datums- und Zeitfelder. Andere Typen wie `EnumField`, `TextAreaField` und `BooleanField` ignorieren sie stillschweigend.

!!! warning
    Addon-Werte werden unescaped gerendert, damit HTML wie Icon-Markup funktioniert. Übergeben Sie ausschließlich vertrauenswürdige Inhalte, die Sie selbst verfasst haben, niemals Benutzereingaben.

## Tabs

Um Abschnitte in eine Tab-Oberfläche aufzuteilen, verwenden Sie `TabsWidget`. Es nimmt eine Liste von `(label, widgets)`-Paaren entgegen.

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Statische Inhalte

Verwenden Sie `HtmlWidget` und `TextWidget`, um beliebige Inhalte an jeder Stelle des Layouts zu rendern: Anleitungen, Warnhinweise oder Trennlinien.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Benutzerdefinierte Widgets

Da sich `form_layout` die `BaseWidget`-Hierarchie mit Dashboards teilt, können Sie `BaseWidget` ableiten, um eigene Elemente zu erstellen. Das ist der Ausweg für alles, was die integrierten Widgets nicht abdecken, etwa schreibgeschützte Vorschauen, eingebettete Diagramme oder eigene Makros.

Sehen Sie sich [Custom Views & Widgets](../user-guide/custom-views.md) für das allgemeine Muster an sowie die [Widgets-API-Referenz](../api/widgets.md) für die Methoden, die eine Unterklasse überschreiben kann. Benutzerdefinierte Widgets in `form_layout` werden immer gerendert, unabhängig davon, was die Regeln zur Feldsichtbarkeit vorgeben.

## Zugriffskontrolle und Sichtbarkeit

`form_layout` respektiert Ihre Regeln für den Zugriff auf Feldebene. Jeder `FieldRef` durchläuft die übliche Prüfung `can_access_field`, und `exclude_from_create`, `exclude_from_edit` sowie rollenbasierte Berechtigungen bleiben weiterhin wirksam.

* **Zeilenerweiterung:** Wenn ein Feld in einer mehrspaltigen Zeile für eine Anfrage ausgeblendet ist, erweitern sich die verbleibenden sichtbaren Felder, um den Platz auszufüllen.
* **Leere Container:** Wenn jedes Feld in einem Container (Zeile, Panel, Fieldset, Spalte, Grid oder Tab) ausgeblendet ist, wird der Container weggelassen, sodass nie eine leere Hülle entsteht.
* **Statisches Rendering:** Statische Komponenten wie `HtmlWidget`, `TextWidget` und benutzerdefinierte `BaseWidget`-Unterklassen werden immer gerendert, da sie nicht von Formularfeldern abhängen.

## Umgang mit ausgelassenen Feldern

Ein Feld, das in `fields` deklariert, aber in `form_layout` nicht berücksichtigt wurde, wird am Ende des Formulars in Deklarationsreihenfolge angehängt, sodass kein Feld jemals unbemerkt verloren geht.

Wird dasselbe Feld zweimal referenziert oder ein Name referenziert, der nicht in `fields` enthalten ist, wird beim Konstruieren der View ein `ValueError` ausgelöst.

---

## Was kommt als Nächstes?

* **[Custom Views & Widgets](../user-guide/custom-views.md):** Die Widget-Hierarchie, auf der `form_layout` aufbaut, und wie Sie Ihr eigenes Widget schreiben.
* **[Templates](templates.md):** Überschreiben Sie `_form_group.html`, um das Markup zu ändern, das eine Layout-Gruppe rendert.
* **[Fields](../user-guide/fields.md):** Die Feldtypen und Sichtbarkeitsregeln, die ein Layout anordnet.
