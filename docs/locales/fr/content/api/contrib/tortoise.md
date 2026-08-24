---
title: Référence API du contrib Tortoise ORM
description: Documentation de référence de l'API pour l'intégration du backend Tortoise
  ORM dans starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

Référence complète des attributs et des méthodes pour le backend Tortoise ORM
(`starlette_admin.contrib.tortoise`), générée à partir des docstrings. Pour un guide
orienté tâches, consultez [Tortoise ORM](../../integrations/tortoise.md).

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
    [Filtres](../filters.md) ; les comportements spécifiques à Tortoise (recherches insensibles à la casse,
    conversion des enums, vérifications de valeurs nulles sur les colonnes de clés brutes) sont traités dans
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry).
