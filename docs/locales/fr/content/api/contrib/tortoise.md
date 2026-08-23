---
title: Référence de l'API du contrib Tortoise ORM
description: Documentation de référence de l'API pour l'intégration du backend Tortoise
  ORM dans starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib : Tortoise ORM

Référence complète des attributs et méthodes du backend Tortoise ORM
(`starlette_admin.contrib.tortoise`), générée à partir des docstrings. Pour un
parcours orienté tâches, consultez [Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Champs

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Convertisseurs

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Les classes de filtres concrètes (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter`, etc.)
    ne sont pas énumérées ici. Elles reprennent les filtres indépendants du backend documentés dans
    [Filtres](../filters.md) ; le comportement spécifique à Tortoise (recherches insensibles à la casse,
    conversion des énumérations, vérifications de valeurs nulles sur les colonnes de clés brutes) est couvert dans
    [Tortoise ORM](../../integrations/tortoise.md#registre-des-filtres).
