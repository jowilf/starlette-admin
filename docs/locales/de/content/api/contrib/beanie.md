---
title: Beanie Contrib API-Referenz
description: API-Referenzdokumentation für die Beanie-Backend-Integration in starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib: Beanie

Vollständige Referenz für Attribute und Methoden des Beanie-Backends (`starlette_admin.contrib.beanie`),
generiert aus Docstrings. Für eine aufgabenorientierte Einführung siehe
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Felder

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converter

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Konkrete Filterklassen (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` usw.) werden
    hier nicht aufgelistet. Sie spiegeln die backend-agnostischen Filter wider, die in
    [Filters](../filters.md) dokumentiert sind. Beanie-spezifisches Verhalten (verankertes Regex-String-Matching, Volltext-
    Suche) wird in [Beanie](../../integrations/beanie.md#filterregistrierung) behandelt.
