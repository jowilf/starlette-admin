---
title: SQLAlchemy Contrib API Reference
description: API-Referenzdokumentation für die SQLAlchemy-Backend-Integration in starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Vollständige Referenz der Attribute und Methoden für das SQLAlchemy-Backend (`starlette_admin.contrib.sqla`),
generiert aus den Docstrings. Eine aufgabenorientierte Einführung finden Sie unter
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Pydantic-Validierung

Die Erweiterung `ext.pydantic` validiert die Formulardaten anhand eines Pydantic-Modells, bevor der
Datensatz geschrieben wird. Eine vollständige Schritt-für-Schritt-Anleitung finden Sie unter
[Pydantic-Validierung](../../integrations/sqlalchemy.md#pydantic-validierung).

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Felder

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Konverter

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Ausnahmen

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Die konkreten Filterklassen (`EqualFilter`, `ContainsFilter`, `BetweenFilter` usw.) werden hier
    nicht aufgezählt. Sie entsprechen den backendunabhängigen Filtern aus
    [Filtern](../filters.md) eins zu eins; das SQLAlchemy-spezifische Verhalten, das es zu kennen
    lohnt, ist in [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry) beschrieben.
