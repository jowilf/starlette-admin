---
title: Tortoise ORM Contrib API-Referenz
description: API-Referenzdokumentation für die Tortoise-ORM-Backend-Integration in
  starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM

Vollständige Referenz der Attribute und Methoden des Tortoise-ORM-Backends
(`starlette_admin.contrib.tortoise`), generiert aus den Docstrings. Eine
anwendungsorientierte Einführung finden Sie unter
[Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Felder

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Konverter

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Die konkreten Filterklassen (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter` usw.)
    werden hier nicht aufgeführt. Sie entsprechen den backend-unabhängigen Filtern, die in
    [Filter](../filters.md) dokumentiert sind; Tortoise-spezifisches Verhalten (Suchen ohne
    Berücksichtigung der Groß-/Kleinschreibung, Enum-Konvertierung, Null-Prüfungen der rohen
    Schlüsselspalte) wird in
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry) behandelt.
