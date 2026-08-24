---
title: Admin-API-Referenz
description: API-Referenzdokumentation für die Admin-Klasse in starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Vollständige Referenz aller Attribute und Methoden von `BaseAdmin`, generiert aus dessen Docstrings. Eine aufgabenorientierte Einführung in die Optionen des Konstruktors finden Sie unter
[Configuring Admin](../user-guide/admin.md).

`starlette_admin` exportiert keine eigene konkrete `Admin`-Klasse. Jedes Backend in
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) bringt seine eigene `Admin`-
Unterklasse mit derselben unten dokumentierten Konstruktorsignatur mit.

::: starlette_admin.base.BaseAdmin
