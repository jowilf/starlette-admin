---
title: Widgets-API-Referenz
description: Vollständige API-Referenz für Dashboard- und Formular-Layout-Widgets
  in starlette-admin.
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# Widgets

Vollständige Referenz aller Attribute und Methoden des Widget-Systems, generiert aus den Docstrings. Eine aufgabenorientierte Einführung finden Sie unter [Custom Views & Widgets](../user-guide/custom-views.md) und [Form Layouts](../advanced/form-layout.md).

Widgets sind zusammensetzbare, renderbare Bausteine, mit denen sich UI-Elemente dynamisch konstruieren lassen. Jede unten aufgeführte Widget-Klasse kann direkt aus `starlette_admin` importiert werden.

Das Widget-System erfüllt je nach Kontext zwei Hauptfunktionen:

* **Dashboards & Custom Pages:** Wird als `widget`-Attribut von [`CustomView`](views.md#starlette_admin.views.CustomView) verwendet, um eigenständige Oberflächen und Metrik-Übersichten zu erstellen.
* **Form Layouts:** Wird als `form_layout`-Attribut von [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) verwendet, um Eingabefelder auf Create-/Edit-Formularen anzuordnen und zu gruppieren.

---

## Basisklasse

Alle Widgets erben von einer gemeinsamen Basisklasse, die die standardmäßige Rendering-Schnittstelle und das Asset-Erfassungsinterface definiert.

::: starlette_admin.widgets.BaseWidget

---

## Content Widgets

Content Widgets bilden die Blattknoten Ihres UI-Baums. Statt andere Widgets zu enthalten, zeigen sie Live-Daten an. Jedes Content Widget akzeptiert eine asynchrone Callback-Funktion, die einmal pro Request aufgerufen wird – so sind die gerenderten Werte stets aktuell.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Layout Widgets

Layout Widgets sind Container, mit denen sich ihre `children` anordnen lassen (dies können Content Widgets, Formularfelder oder weitere Layout Widgets sein).

**Automatisches Asset-Management:** Layout Widgets durchlaufen ihren Baum rekursiv und sammeln `additional_css_links` und `additional_js_links` ihrer Kinder ein. Dadurch laden auch tief verschachtelte Komponenten ihre benötigten CSS/JS-Assets automatisch, ohne dass eine manuelle Verdrahtung erforderlich ist.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Responsive Größenanpassung

Utility-Klassen zur Steuerung responsiver Grid-Verhalten, Spaltenbreiten und Breakpoints über verschiedene Bildschirmgrößen hinweg.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Formular-Layout-Referenzen

Spezialisierte Widgets, die ausschließlich im Kontext von Modellformularen verwendet werden, um auf bestimmte Datenbankfelder zu verweisen.

::: starlette_admin.widgets.FieldRef

---

## Kurzschreibweise & Normalisierung

Damit Ihr Layout-Code übersichtlich und gut lesbar bleibt, akzeptieren Container-Widgets einfache Python-Typen anstelle expliziter Widget-Instanziierungen. Während der Initialisierung (`__post_init__`) lösen Container diese Kurzschreibweisen automatisch in die entsprechenden Widget-Klassen auf.

**Unterstützte Kurzschreibweisen:**

* `str`: Wird zu einer Feldreferenz (`FieldRef`) aufgelöst.
* `tuple`: Wird zu einer nebeneinander angeordneten Zeile (`RowWidget`) aufgelöst.
* `list`: Wird zu einem vertikalen Stapel (`ColumnWidget`) aufgelöst.

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Hilfsfunktionen

Utility-Funktionen zum Rendern von Widgets innerhalb von Jinja2-Templates oder benutzerdefinierten Kontexten.

::: starlette_admin.widgets.render_widget
