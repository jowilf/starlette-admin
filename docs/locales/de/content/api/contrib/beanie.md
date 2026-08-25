---
title: Beanie Contrib API-Referenz
description: API-Referenzdokumentation für die Beanie-Backend-Integration in starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib: Beanie

Vollständige Referenz aller Attribute und Methoden des Beanie-Backends (`starlette_admin.contrib.beanie`),
generiert aus Docstrings. Eine aufgabenorientierte Anleitung finden Sie unter
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Fields

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converters

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Konkrete Filterklassen (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` usw.) werden
    hier nicht aufgeführt. Sie entsprechen den backend-unabhängigen Filtern, die in
    [Filters](../filters.md) dokumentiert sind; Beanie-spezifisches Verhalten (verankerte
    Regex-Zeichenkettenübereinstimmung, Volltextsuche) wird in
    [Beanie](../../integrations/beanie.md#filter-registry) behandelt.
