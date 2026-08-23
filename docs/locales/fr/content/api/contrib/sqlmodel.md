---
title: Référence de l'API de starlette_admin.contrib.sqlmodel
description: Documentation de référence de l'API pour l'intégration du backend SQLModel
  dans starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib : SQLModel

Référence complète des attributs et des méthodes du backend SQLModel (`starlette_admin.contrib.sqlmodel`),
générée à partir des docstrings. SQLModel repose sur SQLAlchemy, de sorte que `Admin` et `ModelView` sont
des sous-classes légères du [backend SQLAlchemy](sqlalchemy.md) qui valident les données des formulaires
via la couche Pydantic du modèle. Pour un guide orienté tâches, consultez
[Intégration de SQLModel](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
