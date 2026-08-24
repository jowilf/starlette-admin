---
title: Admin-API-Referenz
description: API-Referenzdokumentation für die Klasse Admin in starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Vollständige Referenz der Attribute und Methoden von `BaseAdmin`, generiert aus dessen Docstrings. Eine aufgabenorientierte Einführung in die Optionen seines Konstruktors finden Sie unter
[Admin konfigurieren](../user-guide/admin.md).

`starlette_admin` exportiert keine eigene konkrete `Admin`-Klasse. Jedes Backend in
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) bringt seine eigene `Admin`-Subklasse mit derselben unten dokumentierten Konstruktorsignatur mit.

::: starlette_admin.base.BaseAdmin
