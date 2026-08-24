---
title: SQLModel Contrib API-Referenz
description: API-Referenzdokumentation für die SQLModel-Backend-Integration in starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel

Vollständige Referenz aller Attribute und Methoden des SQLModel-Backends (`starlette_admin.contrib.sqlmodel`),
generiert aus den Docstrings. SQLModel basiert auf SQLAlchemy, daher sind `Admin` und `ModelView` schlanke
Subklassen des [SQLAlchemy-Backends](sqlalchemy.md), die Formulardaten über die Pydantic-Schicht des Modells
validieren. Eine aufgabensorientierte Anleitung finden Sie unter
[SQLModel Integration](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
