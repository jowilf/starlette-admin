---
title: Référence de l'API Admin
description: Documentation de référence de l'API pour la classe Admin dans starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Référence complète des attributs et méthodes de `BaseAdmin`, générée à partir de ses docstrings. Pour une présentation orientée tâches de ses options de constructeur, consultez
[Configurer l'Admin](../user-guide/admin.md).

`starlette_admin` n'exporte aucune classe `Admin` concrète en propre. Chaque backend dans
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) fournit sa propre sous-classe `Admin`
avec la même signature de constructeur que celle documentée ci-dessous.

::: starlette_admin.base.BaseAdmin
