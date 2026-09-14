---
title: Plugins
description: Empaquetez des fonctionnalités et extensions d'administration réutilisables
  sous forme de plugins prêts à l'emploi pour starlette-admin.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Plugins

Un plugin est un package Python qui étend `starlette-admin` via un simple argument de constructeur. Un plugin peut regrouper n'importe quelle combinaison de champs, templates, assets statiques, convertisseurs de modèles, filtres, formats d'import/export, backends de stockage, abonnés d'événements, vues, routes, middlewares, assets de thème et catalogues de traduction.

## Utiliser un plugin

Passez les plugins via l'argument `plugins` lorsque vous construisez votre instance `Admin` :

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Le constructeur du plugin prend les options, et la liste est transmise directement à `Admin`. Rien d'autre à configurer ni à enregistrer. Les options circulent du constructeur vers le backend Python, les templates Jinja et le JavaScript frontend.

## Créer un plugin

Pour écrire un plugin, partez du template cookiecutter officiel. Il génère un package publiable avec la structure de répertoires et la configuration appropriées.

### Prérequis

Installez `cookiecutter` avec votre gestionnaire de packages. Consultez le [guide d'installation officiel](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) pour plus de détails :

```bash
pip install cookiecutter
```

### Scaffolding

Exécutez le template cookiecutter depuis n'importe quel emplacement :

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Le template vous demande le nom du plugin, le slug du package, la version et quelques autres variables. Une fois terminé, vous disposez d'un package autonome contenant :

* Un répertoire `src/` hébergeant la classe de votre plugin et ses champs.
* Des dossiers `templates/`, `static/` et `translations/` correctement namespacés.
* Une suite de tests complète.
* Une application exemple exécutable.

## L'API des plugins

Au cœur de chaque plugin se trouve une sous-classe de `BasePlugin` (`starlette_admin.plugins.BasePlugin`), qui vous fournit des hooks pour enregistrer vos fonctionnalités pendant l'initialisation de `Admin`.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

L'attribut `name` est un identifiant unique en kebab-case qui sert également de namespace pour vos templates et vos assets statiques. Chaque template et chaque fichier statique fourni par votre plugin doit résider sous `plugins/<name>/`.

### Dossiers d'assets

Un plugin peut contenir exactement trois dossiers à la racine de son package. Rien n'est à enregistrer, car l'administration les trouve par convention :

* `templates/` : les templates Jinja, qui doivent se trouver sous `templates/plugins/<name>/`.
* `static/` : les assets statiques tels que les fichiers CSS et JS, qui doivent se trouver sous `static/plugins/<name>/`.
* `translations/` : les catalogues de traduction Babel.

Rester dans le namespace `plugins/<name>/` évite que vos assets entrent en collision avec les fichiers du cœur ou ceux d'autres plugins, tout en les laissant surchargeables via le `templates_dir` ou le `static_dir` de l'utilisateur.

### Hooks déclaratifs

Surchargez les hooks déclaratifs pour injecter des assets, enregistrer des vues ou monter des routes.

* `css_links(self, request: Request) -> Sequence[str]` : ajoute des feuilles de style à la mise en page de chaque page d'administration.
* `js_links(self, request: Request) -> Sequence[str]` : ajoute des scripts à la mise en page de chaque page d'administration.
* `views(self) -> Sequence[BaseView]` : renvoie les vues à enregistrer dans la barre latérale de l'administration. Renvoyez une `DropDown` pour les regrouper.
* `routes(self) -> Sequence[Route | Mount]` : renvoie des endpoints headless montés sous `/plugins/<name>/`, ce qui est pratique pour les webhooks et les endpoints proxy.
* `middlewares(self) -> Sequence[Middleware]` : ajoute des middlewares Starlette.
* `template_globals(self) -> dict[str, Any]` : expose des globals Jinja, préfixés par `<name>_` afin d'éviter toute collision.
* `template_filters(self) -> dict[str, Callable]` : expose des filtres Jinja, préfixés par `<name>_` de la même manière.

### Le hook setup

`setup(self, admin: BaseAdmin) -> None` intègre votre plugin aux registres du cœur. Utilisez-le pour enregistrer des convertisseurs de modèles, des filtres, des formats d'import et d'export, des backends de stockage et des abonnés d'événements. Il s'exécute après l'application des hooks déclaratifs.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Le hook de cycle de vie

`on_mount(self, admin: BaseAdmin) -> None` s'exécute exactement une fois, après la construction et le montage de la sous-application Starlette. L'application construite est disponible via `admin.app`.

## Templates et surcharges

Les templates des plugins rejoignent automatiquement la chaîne de loaders. Un utilisateur en surcharge un en plaçant un fichier au chemin correspondant dans son propre `templates_dir`, qui a toujours la priorité. Pour surcharger `plugins/geospatial/fields/form/point.html`, par exemple, il crée `templates_dir/plugins/geospatial/fields/form/point.html`.

Afin qu'une surcharge utilisateur puisse étendre l'original en toute sécurité, chaque plugin reçoit un mapping de préfixe `@<name>` qui fonctionne comme le préfixe `@core`. La surcharge commence par `{% extends "@geospatial/fields/form/point.html" %}` et étend le template de base du plugin sans s'inclure elle-même récursivement.

## Intégration JavaScript frontend

Un plugin qui fournit des champs personnalisés doit empaqueter ses scripts frontend conformément au contrat d'initialisation des champs. Cela garantit leur fonctionnement aussi bien lors des chargements complets de page que lors de l'insertion dynamique de fragments.

* **Ciblez localement :** effectuez vos requêtes dans l'élément `container` qui vous est fourni, jamais sur le `document` global.
* **Soyez idempotent :** le cœur exécute l'initialiseur au chargement du DOM, puis à nouveau chaque fois qu'il insère des lignes inline ou des fragments.
* **Utilisez les attributs data :** lisez la configuration à partir des attributs `data-*` rendus sur l'élément du champ.

```javascript title="plugins/<name>/js/slider.js"
(function () {
  function initSlider(container) {
    var input = container.querySelector('input[type="range"]');
    var output = container.querySelector(".sa-slider-output");
    var suffix = container.dataset.suffix || "";

    input.addEventListener("input", function () {
      output.textContent = input.value + suffix;
    });
  }

  // Register the initializer so core runs it on the right lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## Points d'extension via le hook setup

Les plugins utilisent les registres publics existants plutôt qu'un chemin d'extension distinct qui leur serait propre.

* **Convertisseurs** : appelez `register_converter`, depuis le backend contrib que vous ciblez, pour associer les types de colonnes ORM à vos classes de champs. Définissez le champ lui-même comme une sous-classe ordinaire de `StringField`, stockant et affichant les géométries sous forme de texte WKT :

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField): ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **Filtres** : appelez `register_filters` pour attacher des classes de filtres à un type de champ.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Stockage** : appelez `register_storage` pour exposer un nouveau backend, tel qu'Azure ou GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importeurs et Exporteurs** : utilisez `register_import_format` et `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Un plugin peut prendre en charge plusieurs backends ORM ; importez-les donc conditionnellement dans `setup()`. Ainsi, le plugin se charge quand même lorsque l'utilisateur n'en a installé qu'un seul :

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## Et ensuite ?

* **[Thèmes personnalisés](custom-themes.md) :** empaquetez et partagez un système visuel complet, en suivant le même workflow cookiecutter.
* **[Événements](events.md) :** l'API d'abonnement qu'un plugin enregistre depuis son hook `setup()`.
* **[Points d'extension](extension-points.md) :** tous les registres et classes de base auxquels un plugin peut se raccrocher.
