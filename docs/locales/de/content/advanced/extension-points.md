---
title: Extension Points
description: Eine Übersicht über alle anpassbaren Hook-Methoden, Basisklassen und
  Konfigurationspunkte in starlette-admin.
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/extension-points/)
<!-- translation-notice:end -->

# Extension Points

Diese Seite listet alle austauschbaren Schnittstellen in `starlette-admin` an einem Ort auf. Finden Sie die Klasse, den Hook oder den Decorator, der zu dem passt, was Sie ändern möchten, und folgen Sie dann dem Link zur vollständigen Anleitung.

| Extension Point | API-Interface oder Hook | Dokumentation |
| --- | --- | --- |
| **Benutzerdefinierter Filter** | Unterklasse von `BaseFilter` bilden und `get_filter_registry()` in einer `ModelView` überschreiben. | [Custom Filters](https://jowilf.github.io/starlette-admin/advanced/custom-filters/) |
| **Benutzerdefinierter Exporter** | Unterklasse von `BaseExporter` bilden. | [Export and Import](../user-guide/export-import.md) |
| **Benutzerdefinierter Importer** | Unterklasse von `BaseImporter` bilden. | [Export and Import](../user-guide/export-import.md) |
| **Benutzerdefiniertes Theme** | Unterklasse von `BaseTheme` bilden. | [Custom Themes](https://jowilf.github.io/starlette-admin/advanced/custom-themes/) |
| **Benutzerdefiniertes Authentifizierungs-Backend** | Unterklasse von `BaseAuthProvider` bilden. | [Authentication](../user-guide/auth.md) |
| **Benutzerdefinierter Dateispeicher** | Unterklasse von `BaseStorage` bilden, das sich über sein `name`-Attribut selbst registriert. | [File Storage](../user-guide/file-storage.md) |
| **Benutzerdefiniertes Widget** | Unterklasse von `BaseWidget` bilden. | [Custom Views](../user-guide/custom-views.md) |
| **Zusätzliche Routen in einer benutzerdefinierten View** | Den Decorator `@route("/path", methods=["GET"])` auf eine Methode eines `CustomView` anwenden. | [Custom Views](../user-guide/custom-views.md) |
| **Plugin** | Unterklasse von `BasePlugin` bilden, um Felder, Views, Assets und mehr zu bündeln. | [Plugins](plugins.md) |

!!! tip
    Um die Standardfarben des Tabler-Themes zu ändern, benötigen Sie kein benutzerdefiniertes Theme. Übergeben Sie stattdessen ein `TablerSettings`-Objekt an eine `DefaultTheme`-Instanz.

---

## Wie geht es weiter

* **[Konzepte](../getting-started/concepts.md):** Sehen Sie, wie diese austauschbaren Bausteine in die Architektur des Frameworks passen.
* **[Views](../user-guide/views.md):** Entdecken Sie die zentralen Views, an die die meisten dieser Extension Points angebunden werden können.
