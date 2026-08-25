---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# Entwickler-Blog

Dieser Abschnitt bietet fortgeschrittene Muster und praxisnahe Techniken für den Aufbau von Admin-Oberflächen mit `starlette-admin`. Diese Artikel konzentrieren sich auf Implementierungen aus der Praxis, die über die Standard-Referenzdokumentation hinausgehen.

## Veröffentlichen eines neuen Beitrags

Die Zensical-Plattform basiert derzeit auf einem manuell gepflegten statischen Index für Blog-Inhalte. Um einen neuen Artikel zu veröffentlichen, führen Sie die folgenden Schritte durch:

1. **Inhalt erstellen:** Schreiben Sie Ihren Beitrag und speichern Sie die Markdown-Datei im Verzeichnis `blog/posts/`.
2. **Index aktualisieren:** Fügen Sie der Tabelle **Veröffentlichte Artikel** unten eine neue Zeile hinzu, einschließlich des Veröffentlichungsdatums und eines relativen Links zu Ihrer Datei.
3. **Konfiguration aktualisieren:** Registrieren Sie den Pfad des neuen Beitrags in der Datei `zensical.toml`.

## Veröffentlichte Artikel

| Datum | Artikeltitel |
| --- | --- |
| 2026-07-13 | [Add an Admin Panel to FastAPI in 5 Minutes with starlette-admin](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Soft Deletes and a Trash View with FastAPI & starlette-admin](posts/soft-deletes-trash-view.md) |
