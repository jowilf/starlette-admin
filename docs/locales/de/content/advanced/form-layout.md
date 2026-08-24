---
title: Formularlayouts
description: Entwerfen Sie komplexe, responsive Formularlayouts mit TabsWidget, FieldsetWidget
  und Grid-Spalten in starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Formularlayouts

Standardmäßig rendern die Create- und Edit-Formulare alles in `fields` als eine flache Liste. Das Attribut `form_layout` ermöglicht es Ihnen, diese Eingabefelder mit denselben komponierbaren Widgets anzuordnen, die Sie auch für [Dashboards](../user-guide/custom-views.md) verwenden: nebeneinanderliegende Zeilen, betitelte oder einklappbare Panels, Tabs, statische Inhalte und Ihre eigenen benutzerdefinierten Widgets.

## Grundlegende Verwendung

Das einfachste Layout benötigt überhaupt keine Widgets. Referenzieren Sie ein Feld über seinen String-Namen, um es in einer eigenen Zeile zu behalten, und gruppieren Sie Namen in einem Tuple, um sie nebeneinander in einer Zeile darzustellen.

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

Sie können beliebig viele Felder in einer Zeile platzieren und ein- und mehrspaltige Zeilen frei mischen.

Container-Widgets erweitern diese Kurzschreibweise selbst: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` und `Col` wandeln bei ihrer Konstruktion Tuples in Zeilen und Listen in gestapelte Spalten um. Die Kurzschreibweise funktioniert daher auch innerhalb verschachtelter `children`-Attribute sowie innerhalb eines [`CustomView.widget`](../user-guide/custom-views.md)-Dashboards.

## Felder gruppieren

### Betitelte Panels

Um einer Gruppe von Feldern einen Titel zu geben oder sie einklappbar zu machen, wrappen Sie sie in ein `PanelWidget`. Das Widget akzeptiert dieselbe String- und Tuple-Kurzschreibweise wie die oberste Ebene.

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

`PanelWidget` nimmt folgende Attribute:

| Attribut | Beschreibung |
| --- | --- |
| `title` | Die Überschrift, die im Card-Header des Panels angezeigt wird. |
| `children` | Die Widgets, die innerhalb des Panels der Reihe nach gerendert werden. Akzeptiert die oben genannte Kurzschreibweise oder verschachtelte Widgets. Fügen Sie ein Kind `TextWidget(card=False)` hinzu, um erklärenden Text unterhalb des Titels darzustellen. |
| `collapsible` | Ermöglicht es, das Panel auf- und zuzuklappen. |
| `collapsed` | Startet das Panel eingeklappt. Gilt nur, wenn `collapsible=True`. |

Für eine Gruppe ohne Titel verwenden Sie stattdessen `ColumnWidget`. Es stapelt seine Kinder vertikal, ohne sie in eine gestylte Card zu wrappen.

### Fieldsets

`FieldsetWidget` gruppiert Felder ähnlich wie `PanelWidget`, rendert aber ein natives HTML-`<fieldset>` und `<legend>` statt einer gestylten Card. Verwenden Sie es, wenn Sie eine einfachere, mit Rahmen versehene Gruppierung wünschen.

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

Das Attribut `legend` legt die Beschriftung im `<legend>`-Element fest. `disabled=True` setzt das HTML-Attribut `disabled` auf dem Container, wodurch alle verschachtelten Formularelemente deaktiviert werden. `FieldsetWidget` unterstützt dieselbe `children`-Kurzschreibweise wie `PanelWidget`, jedoch keine panelspezifischen Optionen wie `collapsible` und `icon`.

## Explizite Spaltenbreiten

Die Tuple-Kurzschreibweise teilt eine Zeile immer gleichmäßig auf. Für feinere Kontrolle über die Spaltenbreiten bauen Sie die Zeile explizit mit `RowWidget`, `Col` und `FieldRef`:

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

## Feldlabels ausblenden

Wenn Sie ein `FieldRef` explizit konstruieren, erhalten Sie den Parameter `show_label`, der das `<label>`-Element weglässt, wenn das umgebende Layout den Zweck des Feldes bereits offensichtlich macht.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` hat als Defaultwert `True`. Die String- und Tuple-Kurzschreibweisen rendern immer Labels, da sie keine Keyword-Argumente akzeptieren.

## Input Groups

Die Parameter `prepend` und `append` fügen ein [Input-Group](https://docs.tabler.io/ui/forms/form-elements#input-group)-Addon an einer Seite eines Eingabefelds an. Jeder davon akzeptiert reinen Text oder rohes HTML, etwa ein Font-Awesome-Icon.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Addons funktionieren bei Feldern, deren Formulartemplate ein natives `<input>`-Element rendert: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, die numerischen Felder (`IntegerField`, `DecimalField`, `FloatField`) sowie die Datums- und Zeitfelder. Andere Typen, wie `EnumField`, `TextAreaField` und `BooleanField`, ignorieren sie stillschweigend.

!!! warning
    Addon-Werte werden unescaped gerendert, damit HTML wie Icon-Markup funktioniert. Übergeben Sie nur vertrauenswürdige Inhalte, die Sie selbst geschrieben haben, niemals Nutzereingaben.

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

Verwenden Sie `HtmlWidget` und `TextWidget`, um beliebige Inhalte an beliebiger Stelle im Layout zu rendern: Anleitungen, Warnungen oder Trennlinien.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Benutzerdefinierte Widgets

Da sich `form_layout` die `BaseWidget`-Hierarchie mit Dashboards teilt, können Sie `BaseWidget` subclassen, um eigene Elemente zu erstellen. Das ist die Hintertür für alles, was die integrierten Widgets nicht abdecken, etwa schreibgeschützte Vorschauen, eingebettete Diagramme oder benutzerdefinierte Macros.

Sehen Sie sich [Custom Views & Widgets](../user-guide/custom-views.md) für das allgemeine Muster an sowie die [Widgets-API-Referenz](../api/widgets.md) für die Methoden, die ein Subclass überschreiben kann. Benutzerdefinierte Widgets in `form_layout` werden immer gerendert, ganz gleich, was die Sichtbarkeitsregeln für Felder besagen.

## Zugriffskontrolle und Sichtbarkeit

`form_layout` respektiert Ihre Zugriffsregeln auf Feldebene. Jedes `FieldRef` durchläuft die übliche Prüfung `can_access_field`, und `exclude_from_create`, `exclude_from_edit` sowie rollenbasierte Berechtigungen bleiben weiterhin in Kraft.

* **Zeilenerweiterung:** Wenn ein Feld in einer mehrspaltigen Zeile für einen Request ausgeblendet ist, erweitern sich die übrigen sichtbaren Felder, um den Platz auszufüllen.
* **Leere Container:** Wenn jedes Feld in einem Container (Zeile, Panel, Fieldset, Spalte, Grid oder Tab) ausgeblendet ist, wird der Container weggelassen, sodass Sie nie eine leere Hülle erhalten.
* **Statisches Rendering:** Statische Komponenten wie `HtmlWidget`, `TextWidget` und benutzerdefinierte `BaseWidget`-Subclasses werden immer gerendert, da sie nicht von Formularfeldern abhängen.

## Umgang mit ausgelassenen Feldern

Ein Feld, das in `fields` deklariert, aber nicht in `form_layout` berücksichtigt wurde, wird am Ende des Formulars in Deklarationsreihenfolge angehängt, sodass kein Feld jemals stillschweigend verloren geht.

Wird dasselbe Feld zweimal referenziert oder wird ein Name referenziert, der nicht in `fields` enthalten ist, wird beim Konstruieren der View ein `ValueError` ausgelöst.

---

## Was kommt als Nächstes

* **[Custom Views & Widgets](../user-guide/custom-views.md):** Die Widget-Hierarchie, auf der `form_layout` aufbaut, und wie Sie Ihr eigenes Widget schreiben.
* **[Templates](templates.md):** Überschreiben Sie `_form_group.html`, um das Markup zu ändern, das eine Layoutgruppe rendert.
* **[Fields](../user-guide/fields.md):** Die Feldtypen und Sichtbarkeitsregeln, die ein Layout anordnet.
