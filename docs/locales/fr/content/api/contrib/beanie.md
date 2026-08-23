---
title: Référence de l'API du module Beanie
description: Documentation de référence de l'API pour l'intégration du backend Beanie
  dans starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Contrib : Beanie

Référence complète des attributs et des méthodes pour le backend Beanie (`starlette_admin.contrib.beanie`),
générée à partir des docstrings. Pour un guide orienté tâches, consultez la page
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Champs

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Convertisseurs

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Les classes de filtres concrètes (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) ne sont pas
    énumérées ici. Elles reprennent les filtres indépendants du backend documentés dans
    [Filtres](../filters.md) ; les comportements spécifiques à Beanie (correspondance de chaînes par regex ancrée,
    recherche plein texte) sont couverts dans [Beanie](../../integrations/beanie.md#filter-registry).
