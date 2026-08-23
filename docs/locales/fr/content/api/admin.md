---
title: Référence de l'API Admin
description: Documentation de référence de l'API pour la classe Admin dans starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

# Admin

Référence complète des attributs et méthodes de `BaseAdmin`, générée à partir de ses docstrings. Pour une présentation orientée tâches de ses options de constructeur, consultez
[Configurer l'Admin](../user-guide/admin.md).

`starlette_admin` n'exporte aucune classe `Admin` concrète en propre. Chaque backend dans
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) fournit sa propre sous-classe `Admin`
avec la même signature de constructeur que celle documentée ci-dessous.

::: starlette_admin.base.BaseAdmin
