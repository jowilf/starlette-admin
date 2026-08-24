---
title: Erweiterungspunkte
description: Ein Überblick über alle anpassbaren Hook-Methoden, Basisklassen und Konfigurationspunkte,
  die in starlette-admin verfügbar sind.
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/extension-points/)
<!-- translation-notice:end -->

# Erweiterungspunkte

Diese Seite listet alle pluggable Oberflächen in `starlette-admin` an einem Ort auf. Finden Sie die Klasse, den Hook oder den Decorator, der zu Ihrer gewünschten Änderung passt, und folgen Sie dem Link zur vollständigen Anleitung.

| Erweiterungspunkt | API-Schnittstelle oder Hook | Dokumentation |
| --- | --- | --- |
| **Benutzerdefinierter Filter** | Subclass von `BaseFilter` erstellen und `get_filter_registry()` auf einer `ModelView` überschreiben. | [Benutzerdefinierte Filter](custom-filters.md) |
| **Benutzerdefinierter Exporter** | Subclass von `BaseExporter` erstellen. | [Export und Import](../user-guide/export-import.md) |
| **Benutzerdefinierter Importer** | Subclass von `BaseImporter` erstellen. | [Export und Import](../user-guide/export-import.md) |
| **Benutzerdefiniertes Theme** | Subclass von `BaseTheme` erstellen. | [Benutzerdefinierte Themes](custom-themes.md) |
| **Benutzerdefiniertes Authentication-Backend** | Subclass von `BaseAuthProvider` erstellen. | [Authentication](../user-guide/auth.md) |
| **Benutzerdefinierter File Storage** | Subclass von `BaseStorage` erstellen, die sich über ihr `name`-Attribut registriert. | [File Storage](../user-guide/file-storage.md) |
| **Benutzerdefiniertes Widget** | Subclass von `BaseWidget` erstellen. | [Benutzerdefinierte Views](../user-guide/custom-views.md) |
| **Zusätzliche Routen auf einer Custom View** | Den Decorator `@route("/path", methods=["GET"])` auf eine Methode einer `CustomView` anwenden. | [Benutzerdefinierte Views](../user-guide/custom-views.md) |
| **Plugin** | Subclass von `BasePlugin` erstellen, um Fields, Views, Assets und mehr zu bündeln. | [Plugins](plugins.md) |

!!! tip
    Um die Standardfarben des Tabler-Themes zu ändern, benötigen Sie kein benutzerdefiniertes Theme. Übergeben Sie stattdessen ein `TablerSettings`-Objekt an eine `DefaultTheme`-Instanz.

---

## Wie es weitergeht

* **[Konzepte](../getting-started/concepts.md):** Erfahren Sie, wie diese pluggable Bausteine in die Architektur des Frameworks eingebettet sind.
* **[Views](../user-guide/views.md):** Entdecken Sie die zentralen Views, an die die meisten dieser Erweiterungspunkte andocken.
