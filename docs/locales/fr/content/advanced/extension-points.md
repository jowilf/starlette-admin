---
title: Points d'extension
description: Un aperçu de toutes les méthodes de hook personnalisables, classes de
  base et points de configuration disponibles dans starlette-admin.
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/extension-points/)
<!-- translation-notice:end -->

# Points d'extension

Cette page répertorie en un seul endroit toutes les surfaces enfichables de `starlette-admin`. Identifiez la classe, le hook ou le décorateur correspondant à ce que vous souhaitez modifier, puis suivez le lien pour consulter le guide complet.

| Point d'extension | Interface API ou hook | Documentation |
| --- | --- | --- |
| **Filtre personnalisé** | Héritez de `BaseFilter` et redéfinissez `get_filter_registry()` sur un `ModelView`. | [Filtres personnalisés](custom-filters.md) |
| **Exportateur personnalisé** | Héritez de `BaseExporter`. | [Export et import](../user-guide/export-import.md) |
| **Importateur personnalisé** | Héritez de `BaseImporter`. | [Export et import](../user-guide/export-import.md) |
| **Thème personnalisé** | Héritez de `BaseTheme`. | [Thèmes personnalisés](custom-themes.md) |
| **Backend d'authentification personnalisé** | Héritez de `BaseAuthProvider`. | [Authentification](../user-guide/auth.md) |
| **Stockage de fichiers personnalisé** | Héritez de `BaseStorage`, qui s'enregistre lui-même via son attribut `name`. | [Stockage de fichiers](../user-guide/file-storage.md) |
| **Widget personnalisé** | Héritez de `BaseWidget`. | [Vues personnalisées](../user-guide/custom-views.md) |
| **Routes supplémentaires sur une vue personnalisée** | Appliquez le décorateur `@route("/path", methods=["GET"])` à une méthode d'un `CustomView`. | [Vues personnalisées](../user-guide/custom-views.md) |
| **Plugin** | Héritez de `BasePlugin` pour regrouper des champs, des vues, des assets et bien plus. | [Plugins](plugins.md) |

!!! tip
    Pour modifier les couleurs par défaut du thème Tabler, vous n'avez pas besoin d'un thème personnalisé. Passez plutôt un objet `TablerSettings` à une instance de `DefaultTheme`.

---

## Et ensuite ?

* **[Concepts](../getting-started/concepts.md) :** Découvrez comment ces éléments enfichables s'intègrent dans l'architecture du framework.
* **[Vues](../user-guide/views.md) :** Explorez les vues principales auxquelles la plupart de ces points d'extension se rattachent.
