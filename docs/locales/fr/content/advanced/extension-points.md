---
title: Points d'extension
description: Une vue d'ensemble de toutes les méthodes de hook personnalisables, des
  classes de base et des points de configuration disponibles dans starlette-admin.
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
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

# Points d'extension

Cette page répertorie en un seul endroit toutes les surfaces enfichables de `starlette-admin`. Trouvez la classe, le hook ou le décorateur correspondant à ce que vous souhaitez modifier, puis suivez le lien pour accéder au guide complet.

| Point d'extension | Interface d'API ou hook | Documentation |
| --- | --- | --- |
| **Filtre personnalisé** | Créez une sous-classe de `BaseFilter` et redéfinissez `get_filter_registry()` sur une `ModelView`. | [Filtres personnalisés](custom-filters.md) |
| **Exportateur personnalisé** | Créez une sous-classe de `BaseExporter`. | [Exportation et importation](../user-guide/export-import.md) |
| **Importateur personnalisé** | Créez une sous-classe de `BaseImporter`. | [Exportation et importation](../user-guide/export-import.md) |
| **Thème personnalisé** | Créez une sous-classe de `BaseTheme`. | [Thèmes personnalisés](custom-themes.md) |
| **Backend d'authentification personnalisé** | Créez une sous-classe de `BaseAuthProvider`. | [Authentification](../user-guide/auth.md) |
| **Stockage de fichiers personnalisé** | Créez une sous-classe de `BaseStorage`, qui s'enregistre elle-même via son attribut `name`. | [Stockage de fichiers](../user-guide/file-storage.md) |
| **Widget personnalisé** | Créez une sous-classe de `BaseWidget`. | [Vues personnalisées](../user-guide/custom-views.md) |
| **Routes supplémentaires sur une vue personnalisée** | Appliquez le décorateur `@route("/path", methods=["GET"])` à une méthode d'une `CustomView`. | [Vues personnalisées](../user-guide/custom-views.md) |
| **Plug-in** | Créez une sous-classe de `BasePlugin` pour regrouper des champs, des vues, des assets, etc. | [Plug-ins](plugins.md) |

!!! tip
    Pour modifier les couleurs par défaut du thème Tabler, vous n'avez pas besoin d'un thème personnalisé. Passez plutôt un objet `TablerSettings` à une instance de `DefaultTheme`.

---

## Et ensuite ?

* **[Concepts](../getting-started/concepts.md) :** Découvrez comment ces éléments enfichables s'intègrent dans l'architecture du framework.
* **[Vues](../user-guide/views.md) :** Explorez les vues principales auxquelles la plupart de ces points d'extension se rattachent.
