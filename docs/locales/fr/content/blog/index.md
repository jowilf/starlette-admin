---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# Blog des développeurs

Cette section fournit des schémas avancés et des techniques pratiques pour construire des interfaces d'administration avec `starlette-admin`. Ces articles se concentrent sur des implémentations concrètes qui complètent la documentation de référence standard.

## Publier un nouvel article

La plateforme Zensical repose actuellement sur un index statique maintenu manuellement pour le contenu du blog. Pour publier un nouvel article, suivez les étapes suivantes :

1. **Créer le contenu :** rédigez votre article et enregistrez le fichier Markdown dans le répertoire `blog/posts/`.
2. **Mettre à jour l'index :** ajoutez une nouvelle ligne au tableau **Articles publiés** ci-dessous, en incluant la date de publication et un lien relatif vers votre fichier.
3. **Mettre à jour la configuration :** enregistrez le chemin du nouvel article dans le fichier `zensical.toml`.

## Articles publiés

| Date | Titre de l'article |
| --- | --- |
| 2026-07-13 | [Add an Admin Panel to FastAPI in 5 Minutes with starlette-admin](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Soft Deletes and a Trash View with FastAPI & starlette-admin](posts/soft-deletes-trash-view.md) |
