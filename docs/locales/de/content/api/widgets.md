---
title: Widgets-API-Referenz
description: Vollständige API-Referenz für Dashboard- und Formularlayout-Widgets in
  starlette-admin.
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# Widgets

Vollständige Referenz der Attribute und Methoden des Widget-Systems, generiert aus Docstrings. Eine aufgabenorientierte Einführung finden Sie unter [Benutzerdefinierte Views & Widgets](../user-guide/custom-views.md) und [Formularlayouts](../advanced/form-layout.md).

Widgets sind kombinierbare, renderbare Bausteine, mit denen sich UI-Elemente dynamisch erstellen lassen. Jede unten aufgeführte Widget-Klasse kann direkt aus `starlette_admin` importiert werden.

Das Widget-System erfüllt je nach Kontext zwei Hauptaufgaben:

* **Dashboards & benutzerdefinierte Seiten:** Wird als `widget`-Attribut von [`CustomView`](views.md#starlette_admin.views.CustomView) verwendet, um eigenständige Interfaces und Metrik-Boards zu erstellen.
* **Formularlayouts:** Wird als `form_layout`-Attribut von [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) verwendet, um Eingaben auf Erstellungs-/Bearbeitungsformularen anzuordnen und zu gruppieren.

---

## Basisklasse

Alle Widgets erben von einer gemeinsamen Basisklasse, die das Standard-Interface für Rendering und Asset-Sammlung definiert.

::: starlette_admin.widgets.BaseWidget

---

## Content-Widgets

Content-Widgets fungieren als Blattknoten Ihres UI-Baums. Statt andere Widgets zu enthalten, zeigen sie Live-Daten an. Jedes Content-Widget akzeptiert einen asynchronen Callback, der einmal pro Request aufgerufen wird, sodass die gerenderten Werte immer aktuell sind.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Layout-Widgets

Layout-Widgets sind Container, die dazu dienen, ihre `children` (also Content-Widgets, Formularfelder oder andere Layout-Widgets) anzuordnen.

**Automatisches Asset-Management:** Layout-Widgets durchlaufen ihren Baum rekursiv, um `additional_css_links` und `additional_js_links` ihrer Kinder zu sammeln. So laden tief verschachtelte Komponenten automatisch die benötigten CSS/JS-Assets, ganz ohne manuelle Verdrahtung.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Responsives Sizing

Hilfsklassen zur Steuerung responsiven Grid-Verhaltens, von Spaltenbreiten und Breakpoints über verschiedene Bildschirmgrößen hinweg.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Formularlayout-Referenzen

Spezialisierte Widgets, die ausschließlich im Kontext von Modellformularen verwendet werden, um auf bestimmte Datenbankfelder zu verweisen.

::: starlette_admin.widgets.FieldRef

---

## Shorthand & Normalisierung

Damit Ihr Layout-Code sauber und gut lesbar bleibt, akzeptieren Container-Widgets einfache Python-Typen anstelle expliziter Widget-Klasseninstanziierungen. Während der Initialisierung (`__post_init__`) lösen Container diese Shorthand-Werte automatisch in ihre entsprechenden Widget-Pendants auf.

**Unterstützte Shorthands:**

* `str`: Wird zu einer Feldreferenz (`FieldRef`) aufgelöst.
* `tuple`: Wird zu einer nebeneinander angeordneten Zeile (`RowWidget`) aufgelöst.
* `list`: Wird zu einem vertikalen Stapel (`ColumnWidget`) aufgelöst.

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Hilfsfunktionen

Utility-Funktionen zum Rendern von Widgets innerhalb von Jinja2-Templates oder benutzerdefinierten Kontexten.

::: starlette_admin.widgets.render_widget
