---
title: Référence de l'API des filtres
description: Documentation de référence de l'API pour les filtres de requêtes de base
  de données dans starlette-admin.
source_hash: c26f3e6379afdc4268934bf0f05b895ebb00f0517dd9834b6fbc337c4f192231
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/filters/)
<!-- translation-notice:end -->

# Filtres

Référence complète des attributs et méthodes du système de filtres, générée à partir des docstrings. Pour un guide orienté tâches, consultez [Filtres](../user-guide/filters.md) et
[Filtres personnalisés](../advanced/custom-filters.md).

Les classes ci-dessous sont indépendantes du backend : elles déclarent le `name`, le `label` et le
`data_type` d'un filtre, mais pas sa logique de requête. Chaque backend ORM (`contrib.sqla`, `contrib.beanie`,
`contrib.mongoengine`, `contrib.tortoise`) les spécialise pour ajouter l'implémentation concrète de la méthode `apply()` propre à ce
backend. Consultez la [page d'intégration](../integrations/sqlalchemy.md) correspondante pour obtenir les classes de filtres concrètes,
importables.

## Types fondamentaux

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## Génériques

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## Numériques

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## Chaînes de caractères

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## Booléens

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## Date et heure

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

## Tableaux

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
