---
title: Tortoise ORM Contrib API-Referenz
description: API-Referenzdokumentation für die Tortoise-ORM-Backend-Integration in
  starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM

Vollständige Referenz aller Attribute und Methoden des Tortoise-ORM-Backends
(`starlette_admin.contrib.tortoise`), generiert aus den Docstrings. Eine
aufgabenorientierte Anleitung finden Sie unter [Tortoise ORM](../../integrations/tortoise.md).

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
    werden hier nicht aufgelistet. Sie entsprechen den backend-unabhängigen Filtern, die unter
    [Filter](../filters.md) dokumentiert sind; Tortoise-spezifisches Verhalten (Lookups ohne
    Berücksichtigung der Groß-/Kleinschreibung, Enum-Umwandlung, Null-Prüfungen für rohe
    Schlüsselspalten) wird unter
    [Tortoise ORM](../../integrations/tortoise.md#filterregistry) behandelt.
