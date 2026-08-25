---
title: Référence de l'API Admin
description: Documentation de référence de l'API pour la classe Admin de starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Référence complète des attributs et méthodes de `BaseAdmin`, générée à partir de ses docstrings. Pour un guide pratique des options de son constructeur, consultez
[Configuration d'Admin](../user-guide/admin.md).

`starlette_admin` n'exporte aucune classe `Admin` concrète en propre. Chaque backend de
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) fournit sa propre sous-classe `Admin`
avec la même signature de constructeur que celle documentée ci-dessous.

::: starlette_admin.base.BaseAdmin
