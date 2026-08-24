---
title: Filter-API-Referenz
description: API-Referenzdokumentation für Datenbank-Query-Filter in starlette-admin.
source_hash: c26f3e6379afdc4268934bf0f05b895ebb00f0517dd9834b6fbc337c4f192231
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/filters/)
<!-- translation-notice:end -->

# Filter

Vollständige Attribut- und Methodenreferenz für das Filtersystem, generiert aus Docstrings. Für eine aufgabenorientierte Einführung siehe [Filter](../user-guide/filters.md) und [Benutzerdefinierte Filter](https://jowilf.github.io/starlette-admin/advanced/custom-filters/).

Die folgenden Klassen sind backend-agnostisch: Sie deklarieren `name`, `label` und `data_type` eines Filters, aber nicht dessen Query-Logik. Jedes ORM-Backend (`contrib.sqla`, `contrib.beanie`,
`contrib.mongoengine`, `contrib.tortoise`) leitet davon ab, um die tatsächliche `apply()`-Implementierung für dieses Backend hinzuzufügen. Auf der jeweiligen [Integrationsseite](../integrations/sqlalchemy.md) finden Sie die konkreten, importierbaren Filterklassen.

## Kerntypen

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## Generisch

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## Numerisch

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## String

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## Boolean

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## Datum und Uhrzeit

::: starlette_admin.filters.date.DateEqualFilter

::: starlette_admin.filters.date.DateTimeEqualFilter

::: starlette_admin.filters.date.TimeEqualFilter

::: starlette_admin.filters.date.DateBetweenFilter

::: starlette_admin.filters.date.DateTimeBetweenFilter

::: starlette_admin.filters.date.TimeBetweenFilter

::: starlette_admin.filters.date.DateInPastFilter

::: starlette_admin.filters.date.DateInFutureFilter

## Enum

::: starlette_admin.filters.enum.InFilter

::: starlette_admin.filters.enum.NotInFilter

## Array

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
