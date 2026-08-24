---
title: SQLModel Contrib API-Referenz
description: API-Referenzdokumentation für die SQLModel-Backend-Integration in starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel

Vollständige Referenz aller Attribute und Methoden des SQLModel-Backends (`starlette_admin.contrib.sqlmodel`),
generiert aus Docstrings. SQLModel basiert auf SQLAlchemy, daher sind `Admin` und `ModelView` schlanke
Subklassen des [SQLAlchemy-Backends](sqlalchemy.md), die Formulardaten über die Pydantic-Schicht des Modells validieren. Für eine aufgabenorientierte Einführung siehe
[SQLModel-Integration](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
