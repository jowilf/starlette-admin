---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# Entwickler-Blog

Dieser Abschnitt bietet fortgeschrittene Muster und praktische Techniken für den Aufbau von Admin-Interfaces mit `starlette-admin`. Diese Artikel konzentrieren sich auf Implementierungen aus der Praxis, die über die Standard-Referenzdokumentation hinausgehen.

## Einen neuen Beitrag veröffentlichen

Die Zensical-Plattform stützt sich derzeit auf einen manuell gepflegten statischen Index für Bloginhalte. Um einen neuen Artikel zu veröffentlichen, führen Sie die folgenden Schritte aus:

1. **Inhalte erstellen:** Schreiben Sie Ihren Beitrag und speichern Sie die Markdown-Datei im Verzeichnis `blog/posts/`.
2. **Index aktualisieren:** Fügen Sie der Tabelle **Veröffentlichte Artikel** unten eine neue Zeile hinzu, einschließlich des Veröffentlichungsdatums und eines relativen Links zu Ihrer Datei.
3. **Konfiguration aktualisieren:** Registrieren Sie den Pfad des neuen Beitrags in der Datei `zensical.toml`.

## Veröffentlichte Artikel

| Datum | Artikeltitel |
| --- | --- |
| 2026-07-13 | [Ein Admin-Panel zu FastAPI in 5 Minuten mit starlette-admin hinzufügen](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Soft-Deletes und eine Papierkorb-View mit FastAPI & starlette-admin](posts/soft-deletes-trash-view.md) |
